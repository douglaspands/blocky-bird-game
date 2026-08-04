"""Parallax pre-renderizado: uma faixa por camada, ate 4 desenhos por frame (R27.2, R27.3).

A v2 refazia as duas camadas de fundo a cada frame — uma dezena de ladrilhos, cada um
precedido de um `random.Random(idx * 13 + 1)` novo — para sortear de novo exatamente a
mesma forma que o indice ja determinava. A task 55 constroi cada camada uma vez, numa
faixa periodica, e o frame vira um ou dois recortes por camada.
"""

import random

import pygame
import pytest

from src import config, render
from src.decor import _LAYERS, HILL_SHAPES, HILL_UNIT, DecorManager, _tile_count
from src.viewport import PLAY_H, PLAY_W, compute
from tests.fakes import FakeRenderer

PHONE = (1080, 2400)  # canvas 480x1067: faixa de ceu alta, chao la embaixo
WIDE = (1920, 1080)  # canvas 1280x720: quase o triplo da largura da area jogavel
SQUARE_2_3 = (PLAY_W, PLAY_H)  # a geometria da v2, sem faixa nenhuma
MAGENTA = (255, 0, 255)


def _use(screen: tuple[int, int]) -> None:
    """Ativa o canvas daquela tela."""
    config.set_viewport(compute(*screen))


def _strip_key(decor_id: str, layer: int) -> tuple:
    """Chave com que `DecorManager` pede a faixa de uma camada ao renderizador."""
    period = _LAYERS[decor_id][layer][0]
    return ("decor", decor_id, layer, period, _tile_count(period, config.screen_w()), config.ground_y())


def _tile_the_v2_way(
    renderer: render.Renderer,
    scrolled: float,
    period: int,
    ground_y: int,
    drawer,
    *,
    lookahead: int = 1,
) -> None:
    """Reproducao do `_tile` da v2, para servir de referencia da equivalencia visual.

    Sem ela a comparacao nao teria contra o que ser feita: o teste diria apenas que a
    faixa desenha *alguma coisa*, e nao que desenha o mesmo parallax de antes.

    `lookahead` e a unica licenca em relacao ao codigo literal da v2, e existe porque a
    v2 tinha ali um defeito: o laco parava no primeiro ladrilho com `x >= largura`, mas
    um veio de minerio e sorteado ate 15px a ESQUERDA do seu ladrilho — entao os cubos
    que o ladrilho logo alem da borda projetava para dentro da tela nunca eram
    desenhados. `test_the_v2_loop_dropped_the_ore_vein_from_beyond_the_edge` fixa o
    defeito por escrito, e e o que impede esta licenca de ser um ajuste conveniente.
    """
    idx = int(scrolled // period)
    x = -(scrolled % period)
    width = renderer.size[0] + lookahead * period
    while x < width:
        drawer(renderer, round(x), idx, ground_y)
        x += period
        idx += 1


def _scrolls(decor_id: str, extra: float) -> tuple[float, float]:
    """Deslocamento de cada camada, um periodo adiante do inicio da faixa.

    Um periodo adiante e nao zero para que o ladrilho de `lookback` exista (indice 0) e
    para que a janela comparada caia longe das duas pontas da faixa, onde o
    wrap-around traz conteudo da outra extremidade."""
    return _LAYERS[decor_id][0][0] + extra, _LAYERS[decor_id][1][0] + extra


def _painted(
    screen: tuple[int, int], decor_id: str, extra: float, *, v2: bool, lookahead: int = 1
) -> pygame.Surface:
    """Canvas com as duas camadas desenhadas por um dos caminhos, sobre fundo magenta."""
    _use(screen)
    canvas = config.viewport().canvas
    ground_y = config.ground_y()
    renderer = render.SurfaceRenderer(canvas, canvas)
    renderer.clear(MAGENTA)  # qualquer pixel remanescente denuncia buraco
    far, near = _scrolls(decor_id, extra)
    if v2:
        for scrolled, (period, drawer) in zip((far, near), _LAYERS[decor_id], strict=True):
            _assert_window_is_free_of_wrap(scrolled, period, canvas[0])
            _tile_the_v2_way(renderer, scrolled, period, ground_y, drawer, lookahead=lookahead)
    else:
        manager = DecorManager()
        manager.far_scrolled = far
        manager.near_scrolled = near
        manager.draw(renderer, decor_id)
    return renderer.snapshot()


def _assert_window_is_free_of_wrap(scrolled: float, period: int, canvas_w: int) -> None:
    """Confere que a janela comparada usa so indices que a faixa contem sem dar a volta.

    A faixa e periodica: fora deste intervalo o indice de mundo `i` vira `i % tiles`, e
    a sequencia de formas passa a ser outra — de proposito, e o preco de nao sortear
    nada por frame. A equivalencia com a v2 vale onde os dois lados falam dos *mesmos*
    indices, e e essa condicao que esta funcao verifica em vez de supor."""
    tiles = _tile_count(period, canvas_w)
    assert int(scrolled // period) >= 0
    assert int((scrolled + canvas_w) // period) + 1 < tiles


# --- o ganho: de ~30 desenhos e ~10 sorteios para ate 4 desenhos (R27.2, R27.3) ----


def test_a_parallax_frame_takes_at_most_four_draw_calls() -> None:
    """O que a task 55 entrega: uma ou duas chamadas por camada, com wrap."""
    for decor_id in _LAYERS:
        renderer = FakeRenderer((PLAY_W, PLAY_H))
        manager = DecorManager()
        for _ in range(30):
            manager.update(3.0)
            renderer.calls.clear()
            manager.draw(renderer, decor_id)
            assert 2 <= len(renderer.draws) <= 4, decor_id


def test_the_v2_way_took_around_thirty_draws_for_the_same_frame() -> None:
    """Ancora do teste acima: sem ela, "ate 4" nao diria de quanto foi a queda."""
    _use(SQUARE_2_3)
    counted = {}
    for decor_id, (far_layer, near_layer) in _LAYERS.items():
        renderer = FakeRenderer((PLAY_W, PLAY_H))
        for period, drawer in (far_layer, near_layer):
            _tile_the_v2_way(renderer, 0.0, period, config.ground_y(), drawer, lookahead=0)
        counted[decor_id] = len(renderer.draws) + len(renderer.fills)
    assert counted == {"overworld": 25, "cave": 24, "nether": 6}


def test_no_random_generator_is_created_while_drawing(monkeypatch: pytest.MonkeyPatch) -> None:
    """R27.3 na sua forma mais literal: o sorteio saiu do frame.

    Era o caso extremo da v2 — um Mersenne Twister (estado de 624 palavras) por
    ladrilho por frame, para produzir sempre o mesmo resultado, ja que a forma e
    deterministica por indice desde o inicio."""
    _use(SQUARE_2_3)
    renderer = FakeRenderer((PLAY_W, PLAY_H))
    manager = DecorManager()
    for decor_id in _LAYERS:
        manager.draw(renderer, decor_id)  # constroi as faixas, onde o sorteio acontece

    monkeypatch.setattr(random, "Random", _forbidden)
    for _ in range(20):
        manager.update(3.0)
        for decor_id in _LAYERS:
            manager.draw(renderer, decor_id)


def _forbidden(*args: object, **kwargs: object) -> object:
    raise AssertionError("random.Random instanciado durante o desenho")


def test_the_v2_way_created_a_generator_for_every_tile(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ancora do teste acima: o caminho antigo criava um por ladrilho, todo frame."""
    _use(SQUARE_2_3)
    made: list[object] = []
    real = random.Random
    monkeypatch.setattr(random, "Random", lambda *a: made.append(real(*a)) or made[-1])

    renderer = FakeRenderer((PLAY_W, PLAY_H))
    period, drawer = _LAYERS["overworld"][1]
    _tile_the_v2_way(renderer, 0.0, period, config.ground_y(), drawer, lookahead=0)
    assert len(made) == 4  # 480px de canvas / 150px de periodo, arredondado para cima


# --- a faixa: construida uma vez, recortada na altura do conteudo ------------------


def test_each_layer_of_each_biome_gets_one_strip_and_keeps_it() -> None:
    """Pre-renderizar so vale se o resultado sobreviver ao frame que o construiu."""
    _use(SQUARE_2_3)
    renderer = FakeRenderer((PLAY_W, PLAY_H))
    manager = DecorManager()
    for _ in range(50):
        manager.update(3.0)
        for decor_id in _LAYERS:
            manager.draw(renderer, decor_id)
    assert len(renderer._images) == 6  # 3 biomas x 2 camadas, e nada mais


def test_a_strip_spans_at_least_three_canvas_widths() -> None:
    """A faixa impoe um periodo ao fundo, que ate entao nao tinha nenhum: e o preco de
    trocar o sorteio por pixels prontos. Tres larguras de canvas colocam a volta do
    ciclo a dezenas de segundos de rolagem, bem alem de uma partida tipica."""
    for screen in (SQUARE_2_3, PHONE, WIDE):
        _use(screen)
        canvas_w = config.screen_w()
        renderer = FakeRenderer(config.viewport().canvas)
        DecorManager().draw(renderer, "cave")
        for image in renderer._images.values():
            assert image.size[0] >= 3 * canvas_w, (screen, image.size)


def test_a_strip_carries_no_empty_rows_above_or_below_its_content() -> None:
    """Uma camada ocupa uma faixa estreita da altura do canvas — nuvens la em cima,
    colinas rentes ao chao. Guardar o vazio entre elas custaria varias vezes o tamanho
    do conteudo, e num celular a soma das seis camadas e o que decide se isso cabe."""
    _use(PHONE)
    renderer = FakeRenderer(config.viewport().canvas)
    manager = DecorManager()
    for decor_id in _LAYERS:
        manager.draw(renderer, decor_id)
    for key, image in renderer._images.items():
        content = image.raw.get_bounding_rect()
        assert content.top == 0, key
        assert content.height == image.size[1], key


def test_the_hill_strip_is_a_fraction_of_the_canvas_height() -> None:
    """Ancora do teste acima: sem ela, "sem linhas vazias" seria compativel com uma
    faixa da altura toda cujo conteudo por acaso tocasse as duas bordas."""
    _use(PHONE)
    renderer = FakeRenderer(config.viewport().canvas)
    DecorManager().draw(renderer, "overworld")
    hills = renderer._images[_strip_key("overworld", 1)]
    assert hills.size[1] == len(HILL_SHAPES[0]) * HILL_UNIT  # 72px, contra 1067 de canvas
    assert hills.size[1] < config.screen_h() // 10


# --- o rolamento: origem que anda, com volta ao comeco -----------------------------


@pytest.mark.parametrize("screen", [SQUARE_2_3, WIDE], ids=["2:3", "wide"])
def test_the_two_cuts_cover_the_canvas_without_gap_or_overlap(screen: tuple[int, int]) -> None:
    """Quando a origem chega perto do fim da faixa, o que falta vem do comeco — e e so
    isso que o segundo recorte faz. Emenda errada aqui seria coluna vazia na tela."""
    _use(screen)
    canvas_w = config.screen_w()
    manager = DecorManager()
    seen_two = False
    for step in range(400):
        manager.far_scrolled = step * 13.7  # passo quebrado: percorre o ciclo sem alinhar
        renderer = FakeRenderer(config.viewport().canvas)
        manager.draw(renderer, "overworld")
        distant = _strip_key("overworld", 0)
        far = [rect for key, rect in renderer.draws if key == distant]
        covered = 0
        for rect in far:
            assert rect.left == covered
            covered = rect.right
        assert covered == canvas_w
        seen_two |= len(far) == 2
    assert seen_two  # a volta ao comeco chegou a acontecer nesta amostra


def test_scrolling_moves_the_source_rectangle_and_not_the_destination() -> None:
    """O destino cobre sempre o canvas inteiro; o que anda e a janela dentro da faixa."""
    _use(SQUARE_2_3)
    renderer = FakeRenderer((PLAY_W, PLAY_H))
    manager = DecorManager()
    manager.far_scrolled = 613.0
    manager.draw(renderer, "overworld")
    (_, _, dest, area) = renderer._of("draw")[0]
    width = renderer._images[_strip_key("overworld", 0)].size[0]
    assert dest.left == 0 and dest.width == PLAY_W
    assert area.left == 613 % width and area.width == PLAY_W


def test_draw_tiles_across_the_whole_canvas_width() -> None:
    """Numa tela mais larga que a area jogavel, o parallax tem que ladrilhar ate a
    borda do canvas — parar nos 480px de mundo deixaria a extensao vazia (R25.5)."""
    for decor_id in _LAYERS:
        renderer = FakeRenderer((1280, 720))
        DecorManager().draw(renderer, decor_id)
        rects = [rect for _, rect in renderer.draws]
        assert rects, decor_id
        assert max(r.right for r in rects) == 1280, decor_id
        assert min(r.left for r in rects) == 0, decor_id


def test_draw_anchors_ground_relative_decor_to_the_play_area() -> None:
    """Colinas, poças de lava e pilares assentam na linha do chao da area jogavel, nao
    na base do canvas — senao afundariam na faixa decorativa de baixo (R25.1)."""
    _use(PHONE)
    ground_y = config.ground_y()
    assert ground_y < config.screen_h() - 96  # ha faixa de chao abaixo

    for decor_id in ("overworld", "nether"):
        renderer = FakeRenderer(config.viewport().canvas)
        DecorManager().draw(renderer, decor_id)
        rects = [rect for _, rect in renderer.draws]
        assert max(r.bottom for r in rects) == ground_y, decor_id


# --- equivalencia visual com a implementacao anterior ------------------------------


@pytest.mark.parametrize("screen", [SQUARE_2_3, PHONE, WIDE], ids=["2:3", "phone", "wide"])
@pytest.mark.parametrize("decor_id", list(_LAYERS), ids=list(_LAYERS))
@pytest.mark.parametrize("extra", [0.0, 37.4])
def test_the_strip_draws_exactly_what_the_v2_loop_drew(
    screen: tuple[int, int], decor_id: str, extra: float
) -> None:
    """Igualdade exata de pixel, e nao aproximada: a faixa e um recorte das mesmas
    formas nas mesmas posicoes, pintadas pelos mesmos desenhadores — qualquer diferenca
    seria erro de geometria, nao de arredondamento."""
    new = _painted(screen, decor_id, extra, v2=False)
    old = _painted(screen, decor_id, extra, v2=True)
    canvas_w, canvas_h = config.viewport().canvas
    different = [
        (x, y)
        for x in range(0, canvas_w, 3)
        for y in range(0, canvas_h, 3)
        if new.get_at((x, y)) != old.get_at((x, y))
    ]
    assert different == []


def test_the_seam_of_the_strip_carries_the_shapes_of_both_ends() -> None:
    """Na emenda da faixa o vizinho de um ladrilho e a outra ponta dela.

    E o que obriga a construcao a pintar as duas pontas mais uma vez do lado de fora:
    um veio de minerio e sorteado ate 15px a esquerda do seu ladrilho, e o do primeiro
    ladrilho da faixa cai justamente atras da emenda. Sem essa repintura ficaria uma
    coluna de 15px sem minerio passando pela tela a cada volta do ciclo.

    A referencia aqui e o mesmo laco da v2, so que alimentado com a sequencia de
    indices que a faixa de fato tem — `idx % tiles`. E a forma direta de afirmar o que
    a faixa promete: a repeticao e no indice, e nao no desenho.
    """
    _use(SQUARE_2_3)
    canvas = config.viewport().canvas
    ground_y = config.ground_y()
    scrolls = []

    manager = DecorManager()
    for period, _ in _LAYERS["cave"]:
        width = period * _tile_count(period, canvas[0])
        scrolls.append(width - canvas[0] / 2)  # a emenda cai no meio da tela
    manager.far_scrolled, manager.near_scrolled = scrolls

    new = render.SurfaceRenderer(canvas, canvas)
    new.clear(MAGENTA)
    manager.draw(new, "cave")

    old = render.SurfaceRenderer(canvas, canvas)
    old.clear(MAGENTA)
    for scrolled, (period, drawer) in zip(scrolls, _LAYERS["cave"], strict=True):
        tiles = _tile_count(period, canvas[0])
        wrapped = (lambda d, n: lambda r, x, idx, gy: d(r, x, idx % n, gy))(drawer, tiles)
        _tile_the_v2_way(old, scrolled, period, ground_y, wrapped)

    before, after = new.snapshot(), old.snapshot()
    different = [
        (x, y)
        for x in range(canvas[0])
        for y in range(ground_y)
        if before.get_at((x, y)) != after.get_at((x, y))
    ]
    assert different == []


def test_the_parallax_actually_covers_ground_it_could_have_agreed_on_nothing() -> None:
    """Ancora da comparacao acima: as duas poderiam concordar por nao desenharem nada.

    Cada bioma tem que deixar pixel proprio na tela, e nas duas alturas — a camada
    distante la em cima ou no topo, a proxima rente ao chao."""
    for decor_id in _LAYERS:
        canvas = _painted(SQUARE_2_3, decor_id, 0.0, v2=False)
        painted = sum(
            canvas.get_at((x, y))[:3] != MAGENTA
            for x in range(0, PLAY_W, 2)
            for y in range(0, config.ground_y(), 2)
        )
        assert painted > 200, decor_id


# --- o defeito da v2 que a faixa nao herdou ---------------------------------------


ORE_REACH = 15
"""Quanto um veio de minerio pode ser sorteado a esquerda do seu proprio ladrilho."""


def test_the_v2_loop_dropped_the_ore_vein_from_beyond_the_edge() -> None:
    """O defeito que justifica o `lookahead` da referencia — e, o que importa mais, a
    unica diferenca que a faixa tem em relacao ao codigo literal da v2.

    `ore_vein_shapes` sorteia cada cubo ate 15px a esquerda do seu ladrilho, mas o laco
    da v2 parava no primeiro ladrilho fora da tela: os cubos que ele projetava de volta
    para dentro simplesmente nao apareciam, e surgiam de uma vez quando a rolagem
    trazia o ladrilho para dentro do intervalo. A faixa nao tem essa emenda — o
    wrap-around leva o vizinho junto — e a diferenca fica confinada aos ultimos 15px da
    tela, onde o caminho antigo e que estava faltando conteudo.

    Ha um segundo transbordo no parallax, e ele nao produz diferenca nenhuma: a colina
    de `HILL_SHAPES[1]` mede 162px contra um periodo de 150, mas a fileira que
    transborda e a da base, e a base de qualquer colina comeca na coluna 0 do proprio
    ladrilho — o vizinho sempre repinta por cima, na mesma cor."""
    strip = _painted(SQUARE_2_3, "cave", 118.4, v2=False)
    literal = _painted(SQUARE_2_3, "cave", 118.4, v2=True, lookahead=0)
    canvas_w, canvas_h = config.viewport().canvas

    different = [
        (x, y)
        for x in range(canvas_w)
        for y in range(canvas_h)
        if strip.get_at((x, y)) != literal.get_at((x, y))
    ]
    assert different, "o deslocamento escolhido tem que exercitar o caso"
    assert all(x >= canvas_w - ORE_REACH for x, _ in different)
    assert all(literal.get_at(p)[:3] == MAGENTA for p in different)  # faltava la, nao aqui


def test_the_hill_is_the_other_overflow_and_it_is_invisible() -> None:
    """Ancora da segunda metade da docstring acima: a colina larga existe mesmo (162px
    contra 150 de periodo) e a fileira que transborda e sempre a da base."""
    wide = next(i for i in range(1, 200) if random.Random(i * 17 + 2).choice(HILL_SHAPES) is HILL_SHAPES[1])
    shape = random.Random(wide * 17 + 2).choice(HILL_SHAPES)
    assert (shape[-1][0] + shape[-1][1]) * HILL_UNIT == 162 > _LAYERS["overworld"][1][0]
    assert all(rows[-1][0] == 0 for rows in HILL_SHAPES)  # a base sempre comeca na coluna 0
