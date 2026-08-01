"""Mobs decorativos: nove variedades nas faixas, e nenhuma delas toca o jogo (R25.3, R25.4).

Duas afirmacoes independentes convivem aqui, e a segunda e a que da nome ao requisito.
A primeira e que os mobs aparecem — tres variedades por bioma, animados, distribuidos
pelas faixas de ceu e laterais. A segunda e que **nada** do que eles fazem chega ao
jogo: nem um pixel dentro da area jogavel, nem uma colisao, nem um ponto, nem um
frame de simulacao diferente do que haveria sem eles.

Ver specs/v3/design.md secao 35.
"""

import ast
import random
from itertools import pairwise
from pathlib import Path
from types import ModuleType

import pygame
import pytest

from src import config, decor, mobs, textures
from src import game as game_module
from src.game import Game, GameState
from src.viewport import PLAY_H, PLAY_W, compute
from tests.fakes import FakeRenderer

PHONE = (1080, 2400)  # canvas 480x1067: faixa de ceu de 251px, sem laterais
WIDE = (1920, 1080)  # canvas 1280x720: laterais de 400px, sem ceu
SQUARE_2_3 = (PLAY_W, PLAY_H)  # a geometria da v2: faixa nenhuma
SHORT_SKY = (1080, 1850)  # canvas 480x822: ceu de 6px, mais baixo que um sprite

BIOME_IDS = tuple(mobs.BIOME_MOBS)


def _use(screen: tuple[int, int]) -> pygame.Rect:
    """Ativa o canvas daquela tela e devolve a area jogavel."""
    config.set_viewport(compute(*screen))
    return config.play()


def _mob_draws(renderer: FakeRenderer) -> list[tuple[str, pygame.Rect]]:
    """Pares (variedade, retangulo de destino) dos mobs desenhados, na ordem."""
    return [(str(key[1]), rect) for key, rect in renderer.draws if isinstance(key, tuple) and key[0] == "mob"]


def _frames(
    screen: tuple[int, int], biome_id: str, count: int = 1, speed: float = 3.0
) -> list[list[tuple[str, pygame.Rect]]]:
    """Desenha `count` frames de um campo de mobs e devolve o que saiu em cada um."""
    _use(screen)
    renderer = FakeRenderer(config.viewport().canvas)
    mobs.precompute(renderer)
    field = mobs.MobField()
    seen = []
    for _ in range(count):
        renderer.calls.clear()
        field.draw_sky(renderer, biome_id)
        field.draw_sides(renderer, biome_id)
        seen.append(_mob_draws(renderer))
        field.update(speed)
    return seen


# --- Os mobs existem mesmo (ancoras contra vacuidade) --------------------------


@pytest.mark.parametrize("screen", (PHONE, WIDE), ids=("ceu", "laterais"))
@pytest.mark.parametrize("biome_id", BIOME_IDS)
def test_every_band_kind_shows_mobs_in_every_biome(screen, biome_id):
    """Sem esta ancora, todo teste de "mob nenhum invade o jogo" passaria por
    vacuidade — inclusive se `mobs.py` nunca desenhasse nada."""
    drawn = [mob for frame in _frames(screen, biome_id, count=90) for mob in frame]
    assert drawn
    assert {kind for kind, _ in drawn} <= set(mobs.BIOME_MOBS[biome_id])


@pytest.mark.parametrize("biome_id", BIOME_IDS)
def test_every_field_carries_the_three_varieties_of_its_biome(biome_id):
    """R25.3 pede pelo menos tres variedades por bioma *em cena*, e a deriva e lenta
    demais para que uma partida percorra o ciclo inteiro do campo. Quem garante e a
    distribuicao: as tres entram em rodizio em todo campo, de qualquer geometria."""
    for screen, band, period in ((PHONE, "sky", mobs.SKY_PERIOD), (WIDE, "side", mobs.SIDE_PERIOD)):
        _use(screen)
        vp = config.viewport()
        top, height = (0, vp.sky_band.height) if band == "sky" else (0, vp.height)
        field = mobs._field(biome_id, band, period, top, height, vp.width)
        assert {slot.kind for slot in field} == set(mobs.BIOME_MOBS[biome_id])


def test_each_biome_has_three_varieties_and_none_repeats_across_biomes():
    """R25.3 pede pelo menos tres por bioma; sao tres, e as nove sao distintas."""
    assert all(len(set(kinds)) == 3 for kinds in mobs.BIOME_MOBS.values())
    every = [kind for kinds in mobs.BIOME_MOBS.values() for kind in kinds]
    assert len(set(every)) == 9
    assert set(every) == set(textures.MOB_MAKERS)


@pytest.mark.parametrize("kind", tuple(textures.MOB_MAKERS))
def test_each_sprite_has_two_distinct_idle_frames(kind):
    """Dois frames de idle por mob, e eles precisam mesmo diferir: um `frame` ignorado
    pela fabrica passaria despercebido em tudo o mais."""
    frames = [textures.MOB_MAKERS[kind](frame) for frame in mobs.IDLE_FRAMES]
    pixels = [[surface.get_at((x, y)) for y in range(16) for x in range(16)] for surface in frames]
    assert frames[0].get_size() == (16, 16)
    assert sum(1 for pixel in pixels[0] if pixel.a > 0) > 40  # nao e um sprite quase vazio
    assert pixels[0] != pixels[1]


def test_the_idle_animation_alternates_and_the_mobs_are_not_in_lockstep():
    """A cadencia e a da asa da abelha; a fase por posicao e o que impede o cenario de
    piscar todo junto, que e o jeito mais rapido de um fundo parecer mecanico."""
    field = mobs.MobField()
    seen = []
    for _ in range(mobs.IDLE_FRAME_INTERVAL * 2):
        seen.append(field.frame)
        field.update(0.0)
    assert seen == [0] * mobs.IDLE_FRAME_INTERVAL + [1] * mobs.IDLE_FRAME_INTERVAL

    _use(WIDE)
    phases = {slot.phase for slot in mobs._field("cave", "side", mobs.SIDE_PERIOD, 0, 720, 1280)}
    assert phases == {0, 1}


# --- Nada disso entra na area jogavel (R25.4) ---------------------------------


@pytest.mark.parametrize("screen", (PHONE, WIDE), ids=("ceu", "laterais"))
@pytest.mark.parametrize("biome_id", BIOME_IDS)
def test_no_mob_pixel_ever_lands_inside_the_play_area(screen, biome_id):
    """A afirmacao central. Ao longo de um ciclo inteiro de deriva, em todo bioma e nas
    duas geometrias de faixa, nenhum retangulo de mob encosta em `viewport.play`."""
    play = _use(screen)
    for frame in _frames(screen, biome_id, count=240):
        for kind, rect in frame:
            assert not play.colliderect(rect), f"{kind} em {rect} invadiu {play}"


def test_the_bands_are_disjoint_from_the_play_area_by_construction():
    """Por que o recorte contra a faixa basta: as faixas e a area jogavel nunca se
    tocam, entao recortar contra uma e ficar fora da outra."""
    for screen in (PHONE, WIDE, SQUARE_2_3, SHORT_SKY):
        play = _use(screen)
        vp = config.viewport()
        for band in (vp.sky_band, vp.left_band, vp.right_band):
            assert not play.colliderect(band)


def test_a_mob_at_the_band_edge_is_clipped_instead_of_spilling():
    """O mecanismo: o sprite que cruza a borda da faixa e desenhado recortado — ele
    desliza para tras da terra em vez de piscar ou vazar para o campo de jogo."""
    _use(WIDE)
    renderer = FakeRenderer(config.viewport().canvas)
    mobs.precompute(renderer)
    field = mobs.MobField()
    bands = (config.viewport().left_band, config.viewport().right_band)

    clipped = []
    for _ in range(400):
        renderer.calls.clear()
        field.draw_sides(renderer, "overworld")
        for _kind, key, rect, area in renderer.calls:
            if isinstance(key, tuple) and key[0] == "mob" and area is not None and area.width < mobs.MOB_SIZE:
                clipped.append((rect, area))
        field.update(3.0)

    assert clipped  # a borda foi mesmo atravessada durante a deriva
    for rect, area in clipped:
        assert rect.width == area.width  # o destino encolhe junto com o recorte
        assert any(band.contains(rect) for band in bands)


def test_a_2_3_canvas_draws_no_mobs():
    """Sem faixa nao ha onde eles morarem — e o desenho nao pode inventar um lugar."""
    for biome_id in BIOME_IDS:
        assert not [mob for frame in _frames(SQUARE_2_3, biome_id, count=60) for mob in frame]


def test_a_sky_band_shorter_than_a_sprite_draws_no_mobs():
    """Um mob cortado na horizontal contra o ceu leria como defeito — ao contrario do
    corte vertical da lateral, que le como estar atras da terra."""
    _use(SHORT_SKY)
    assert config.viewport().sky_band.height < mobs.MOB_SIZE
    assert config.viewport().left_band.width == 0
    assert not [mob for frame in _frames(SHORT_SKY, "nether", count=60) for mob in frame]


# --- Nada disso muda uma regra do jogo (R25.4) --------------------------------


@pytest.fixture
def frozen_rng():
    """Devolve o gerador global ao estado anterior ao teste.

    `_simulate` precisa fixar a semente global, e deixa-la fixada tornaria
    deterministicos os testes seguintes da sessao — que e o tipo de acoplamento que so
    aparece muito depois, num arquivo que nem sabe deste."""
    state = random.getstate()
    yield
    random.setstate(state)


def _autopilot(game: Game, frame: int) -> None:
    """Mira a abertura da coluna mais proxima. Mantem a partida viva e pontuando."""
    ahead = [pipe for pipe in game.pipes.pipes if pipe.x + config.PIPE_W > game.bird.pos.x]
    target = ahead[0].gap_y if ahead else config.play().centery
    if game.bird.pos.y > target:
        game.bird.flap()


def _blind_flapping(game: Game, frame: int) -> None:
    """Flapa em cadencia fixa, sem olhar as colunas. Acaba batendo — e e o ponto."""
    if frame % 20 == 0:
        game.bird.flap()


def _simulate(frames: int, steer) -> list[tuple]:
    """Roda uma partida por `frames` frames e devolve o estado observavel de cada um.

    A semente global e fixada porque a abertura da coluna sai de `random.uniform`
    (`pipes._spawn`): sem ela as duas partidas comparadas teriam colunas diferentes, e
    a comparacao mediria o sorteio em vez dos mobs."""
    random.seed(20250731)
    game = Game()
    game.renderer = FakeRenderer(game.viewport.canvas)
    game.state = GameState.JOGANDO
    trace = []
    for index in range(frames):
        steer(game, index)
        game.update()
        game.draw()
        trace.append(
            (
                game.state,
                game.score,
                round(game.bird.pos.y, 6),
                round(game.bird.vel_y, 6),
                tuple(round(pipe.x, 6) for pipe in game.pipes.pipes),
                tuple(pipe.scored for pipe in game.pipes.pipes),
                game.biome.current.id,
            )
        )
    return trace


def test_the_whole_simulation_is_identical_with_and_without_mobs(
    monkeypatch: pytest.MonkeyPatch, frozen_rng
) -> None:
    """R25.4 por inteiro, e de uma vez: colisao, pontuacao, velocidade, bioma e
    trajetoria. Desligar os mobs nao muda um unico frame de duas partidas de 400.

    Partidas completas em vez de tres asserts separados porque o requisito e sobre a
    *ausencia* de influencia: enumerar as regras deixaria de fora justamente a que
    ninguem pensou em enumerar. Sao duas porque uma so nao cobre as duas metades — a
    que pilota pontua e troca de bioma, a que flapa as cegas colide e vai para
    GAME_OVER."""
    flying = _simulate(400, _autopilot)
    crashing = _simulate(400, _blind_flapping)
    assert max(frame[1] for frame in flying) > 0  # pontuou de verdade
    assert any(frame[0] is GameState.GAME_OVER for frame in crashing)  # colidiu de verdade

    monkeypatch.setattr(mobs.MobField, "draw_sky", lambda *args: None)
    monkeypatch.setattr(mobs.MobField, "draw_sides", lambda *args: None)
    assert _simulate(400, _autopilot) == flying
    assert _simulate(400, _blind_flapping) == crashing


def test_a_mob_over_the_bird_does_not_collide():
    """A abelha voa por dentro do retangulo onde um mob esta desenhado — na tela
    estreita a faixa de ceu fica logo acima dela — e nada acontece."""
    game = Game()
    game.apply_resize(PHONE)
    game.renderer = FakeRenderer(game.viewport.canvas)
    game.reset()
    game.state = GameState.JOGANDO
    game.pipes.pipes.clear()
    game.draw()

    drawn = _mob_draws(game.renderer)
    assert drawn
    game.bird.pos.x = drawn[0][1].centerx
    game.bird.pos.y = drawn[0][1].centery
    assert game.bird.rect.colliderect(drawn[0][1])  # sobrepostos de fato
    assert game._collision_texture() is None


def test_mobs_module_imports_nothing_from_the_game():
    """R25.4 pela dependencia, que e o que impede a regressao: um mob so pode deixar de
    ser decorativo se `mobs.py` puder alcancar o estado de jogo, e ele nao pode."""
    assert _src_imports(mobs) == {"src.config", "src.render", "src.textures"}
    # ancora: a mesma leitura aplicada a quem TEM acesso ao jogo enxerga a diferenca
    assert "src.game" not in _src_imports(mobs)
    assert {"src.mobs", "src.pipes", "src.score"} <= _src_imports(game_module)


def _src_imports(module: ModuleType) -> set[str]:
    """Modulos de `src` importados por `module`, lidos do fonte.

    As duas formas em uso no projeto — `from src import x` e `from src.x import Y` —
    sao normalizadas para o mesmo nome, `src.x`."""
    tree = ast.parse(Path(str(module.__file__)).read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            root = node.module or ""
            if root == "src":
                found |= {f"src.{alias.name}" for alias in node.names}
            elif root.startswith("src."):
                found.add(root)
        elif isinstance(node, ast.Import):
            found |= {alias.name for alias in node.names if alias.name.startswith("src.")}
    return found


# --- Distribuicao, deriva e custo ---------------------------------------------


def test_mobs_drift_slower_than_the_far_parallax_layer():
    """Mais lento que a camada distante e o que os coloca atras dela (R25.3)."""
    assert 0 < mobs.MOB_FACTOR < decor.FAR_FACTOR
    field = mobs.MobField()
    layers = decor.DecorManager()
    for _ in range(60):
        field.update(3.0)
        layers.update(3.0)
    assert field.scrolled < layers.far_scrolled


def test_no_two_mobs_of_a_field_overlap_even_at_the_seam():
    """O desvio sorteado dentro de cada periodo nunca passa de `period - MOB_SIZE`,
    entao dois vizinhos ficam a pelo menos um sprite de distancia — e o ultimo do ciclo
    fica a essa distancia do primeiro, que e onde a conta seria facil de errar."""
    _use(WIDE)
    for biome_id in BIOME_IDS:
        field = mobs._field(biome_id, "side", mobs.SIDE_PERIOD, 0, 720, 1280)
        span = len(field) * mobs.SIDE_PERIOD
        xs = sorted(slot.x for slot in field)
        gaps = [b - a for a, b in pairwise(xs)] + [xs[0] + span - xs[-1]]
        assert min(gaps) >= mobs.MOB_SIZE


def test_the_field_is_periodic_and_the_drift_wraps_around():
    """A deriva da a volta no campo: um ciclo inteiro depois, a cena e a mesma."""
    _use(WIDE)
    renderer = FakeRenderer(config.viewport().canvas)
    field = mobs.MobField()
    span = len(mobs._field("cave", "side", mobs.SIDE_PERIOD, 0, 720, 1280)) * mobs.SIDE_PERIOD

    field.draw_sides(renderer, "cave")
    first = _mob_draws(renderer)
    renderer.calls.clear()
    field.scrolled = float(span)
    field.draw_sides(renderer, "cave")
    assert _mob_draws(renderer) == first
    assert first  # nao e a igualdade de duas listas vazias


def test_the_field_covers_at_least_three_canvas_widths():
    """Um campo curto fecharia o ciclo em poucos segundos e a repeticao ficaria obvia."""
    _use(WIDE)
    field = mobs._field("nether", "side", mobs.SIDE_PERIOD, 0, 720, 1280)
    assert len(field) * mobs.SIDE_PERIOD >= mobs.FIELD_SPANS * 1280
    _use((480, 720 * 4))  # canvas estreito: a conta daria menos que o piso
    narrow = mobs._field("nether", "sky", mobs.SKY_PERIOD, 0, 400, 480)
    assert len(narrow) >= mobs.MIN_SLOTS


def _sweep_counts(screen: tuple[int, int], band: str) -> list[int]:
    """Mobs desenhados em cada deslocamento de um ciclo inteiro do campo.

    Um ciclo tem milhares de pixels e a deriva anda 0,45px por frame, entao percorre-lo
    frame a frame levaria dezenas de milhares de iteracoes; o deslocamento e fixado
    direto, que e a mesma coisa que a deriva produz."""
    _use(screen)
    vp = config.viewport()
    renderer = FakeRenderer(vp.canvas)
    mobs.precompute(renderer)
    field = mobs.MobField()
    period = mobs.SKY_PERIOD if band == "sky" else mobs.SIDE_PERIOD
    height = vp.sky_band.height if band == "sky" else vp.height
    span = len(mobs._field("cave", band, period, 0, height, vp.width)) * period

    counts = []
    for offset in range(0, span, 3):
        field.scrolled = float(offset)
        renderer.calls.clear()
        if band == "sky":
            field.draw_sky(renderer, "cave")
        else:
            field.draw_sides(renderer, "cave")
        counts.append(len(_mob_draws(renderer)))
    return counts


@pytest.mark.parametrize(("screen", "band", "floor", "ceiling"), ((PHONE, "sky", 2, 4), (WIDE, "side", 3, 7)))
def test_the_bands_stay_populated_and_cheap_over_a_whole_cycle(screen, band, floor, ceiling):
    """Duas afirmacoes que so um ciclo inteiro cobre.

    O piso e a continuidade: a faixa nunca esvazia, porque o mob que sai por uma ponta
    do campo volta pela outra. Sem a volta, os que ja passaram simplesmente sumiriam e
    a faixa iria ficando vazia ate o ciclo reiniciar.

    O teto e o custo: os mobs sao cenario, e o orcamento da secao 34 do design e de
    poucos desenhos por frame — o campo so cabe nele porque quase todas as suas
    posicoes estao, a cada instante, fora da tela ou fora das faixas."""
    counts = _sweep_counts(screen, band)
    assert min(counts) == floor
    assert max(counts) == ceiling


# --- Construcao fora do frame (R27.2) -----------------------------------------


def test_precompute_builds_the_eighteen_sprites_once():
    renderer = FakeRenderer()
    mobs.precompute(renderer)
    keys = set(renderer._images)
    assert keys == {("mob", kind, frame) for kind in textures.MOB_MAKERS for frame in mobs.IDLE_FRAMES}

    before = dict(renderer._images)
    mobs.precompute(renderer)
    assert renderer._images == before  # idempotente: nada e reconstruido


def test_a_fresh_game_draws_without_building_a_single_sprite(monkeypatch: pytest.MonkeyPatch) -> None:
    """A pre-computacao acontece mesmo em `Game.__init__`, e nao "por acaso" no primeiro
    frame: sem ela os 18 sprites nasceriam durante o jogo, um por vez, exatamente o
    custo que R27.2 tira de dentro do frame."""
    game = Game()  # com o renderizador de verdade: e o cache dele que interessa aqui
    game.state = GameState.JOGANDO

    def forbidden(*args, **kwargs):
        raise AssertionError("sprite de mob construido durante o desenho")

    monkeypatch.setattr(textures, "scale_pixel_perfect", forbidden)
    for _ in range(120):
        game.update()
        game.draw()


def test_no_sprite_is_built_during_a_frame(monkeypatch: pytest.MonkeyPatch) -> None:
    """Depois da pre-computacao, desenhar nao pode escalar nem pintar sprite nenhum —
    e o que impede o custo de voltar para dentro do frame."""
    _use(WIDE)
    renderer = FakeRenderer(config.viewport().canvas)
    mobs.precompute(renderer)
    field = mobs.MobField()

    def forbidden(*args, **kwargs):
        raise AssertionError("sprite de mob construido durante o desenho")

    monkeypatch.setattr(textures, "scale_pixel_perfect", forbidden)
    for _ in range(180):
        field.draw_sky(renderer, "nether")
        field.draw_sides(renderer, "nether")
        field.update(3.3)


def test_a_resize_rebuilds_the_sprites_outside_the_frame():
    """`forget_images` derruba tudo; sem refaze-los ali, os 18 voltariam um por frame."""
    game = Game()
    game.renderer = FakeRenderer(game.viewport.canvas)
    game.draw()
    game.apply_resize(PHONE)
    keys = set(game.renderer._images)
    assert {("mob", kind, frame) for kind in textures.MOB_MAKERS for frame in mobs.IDLE_FRAMES} <= keys


# --- Ordem de desenho (design secao 32.6) -------------------------------------


def _drawn_kinds(screen: tuple[int, int]) -> list[str]:
    """Sequencia de tipos de imagem desenhados num frame de JOGANDO naquela tela.

    Roda alguns frames antes de olhar: a coluna nasce em `play.right` e a task 54 a
    descarta enquanto ela estiver fora do canvas, entao no primeiro frame de uma tela
    estreita nao ha coluna nenhuma desenhada para comparar."""
    game = Game()
    game.apply_resize(screen)
    game.reset()  # as colunas nascem em `play.right`, que acabou de mudar
    game.renderer = FakeRenderer(game.viewport.canvas)
    game.state = GameState.JOGANDO
    for _ in range(30):
        game.update()
    game.draw()
    return [str(key[0] if isinstance(key, tuple) else key) for key, _ in game.renderer.draws]


def test_sky_and_side_bands_never_coexist():
    """Por que a ordem de desenho e verificada em duas telas, e nao numa so: o canvas
    recebe a proporcao da tela, entao so um dos eixos pode sobrar (`viewport.compute`).
    Uma tela com faixa de ceu *e* faixa lateral nao existe."""
    for screen in (PHONE, WIDE, SQUARE_2_3, SHORT_SKY, (1400, 1000)):
        vp = compute(*screen)
        assert not (vp.sky_extra and vp.left_band.width)


def test_sky_mobs_are_drawn_before_the_pipes():
    """O do ceu fica atras da coluna, que atravessa a faixa vinda de fora da tela."""
    kinds = _drawn_kinds(PHONE)
    pipes = [i for i, kind in enumerate(kinds) if kind in ("pipe_top", "pipe_bottom")]
    sky_mobs = [i for i, kind in enumerate(kinds) if kind == "mob"]
    assert pipes and sky_mobs
    assert max(sky_mobs) < min(pipes)


def test_side_mobs_are_drawn_after_the_opaque_bands():
    """A faixa lateral e opaca: um mob desenhado antes dela sumiria atras da terra —
    ele vive NA parede, nao atras dela."""
    kinds = _drawn_kinds(WIDE)
    bands = [i for i, kind in enumerate(kinds) if kind == "band"]
    side_mobs = [i for i, kind in enumerate(kinds) if kind == "mob"]
    assert bands and side_mobs
    assert min(side_mobs) > max(bands)
