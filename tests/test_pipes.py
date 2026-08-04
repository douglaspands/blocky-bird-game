import pygame
import pytest

from src import config, render, textures
from src.config import BLOCK, GAP_MARGIN, GROUND_H, PIPE_SPACING, PIPE_W, screen_h, screen_w
from src.pipes import PipeManager, PipePair
from src.viewport import PLAY_H, PLAY_W, compute
from tests.fakes import FakeRenderer

WIDE = (1920, 1080)  # canvas 1280x720: a coluna nasce dentro do canvas, sob a faixa lateral
SQUARE_2_3 = (PLAY_W, PLAY_H)  # a geometria da v2: a area jogavel e o canvas inteiro
BIOME_BLOCKS = [("dirt", "grass_side"), ("netherrack", "obsidian")]


def test_initial_spawn_is_at_right_edge():
    pm = PipeManager(160, "dirt", "grass_side")
    assert len(pm.pipes) == 1
    assert pm.pipes[0].x == screen_w()


def test_gap_is_within_safe_margins():
    pm = PipeManager(160, "dirt", "grass_side")
    pipe = pm.pipes[0]
    assert GAP_MARGIN <= pipe.gap_y <= screen_h() - GROUND_H - GAP_MARGIN


def test_new_pipe_freezes_current_gap_size_and_textures():
    pm = PipeManager(160, "dirt", "grass_side")
    assert pm.pipes[0].gap_size == 160
    assert pm.pipes[0].block_main == "dirt"
    assert pm.pipes[0].block_edge == "grass_side"


def test_update_moves_pipes_left_by_speed():
    pm = PipeManager(160, "dirt", "grass_side")
    start_x = pm.pipes[0].x
    pm.update(2.5, 160, "dirt", "grass_side")
    assert pm.pipes[0].x == start_x - 2.5


def test_spawns_new_pipe_at_fixed_spacing():
    pm = PipeManager(160, "dirt", "grass_side")
    while len(pm.pipes) < 2:
        pm.update(2.5, 160, "dirt", "grass_side")
    assert pm.pipes[1].x - pm.pipes[0].x == PIPE_SPACING


def test_existing_pipe_keeps_old_biome_params_after_biome_change():
    pm = PipeManager(160, "dirt", "grass_side")
    first_pipe = pm.pipes[0]
    pm.update(3.0, 145, "stone", "cobblestone")
    assert first_pipe.gap_size == 160
    assert first_pipe.block_main == "dirt"
    assert first_pipe.block_edge == "grass_side"


def test_new_pipe_uses_new_biome_params():
    pm = PipeManager(160, "dirt", "grass_side")
    while len(pm.pipes) < 2:
        pm.update(3.0, 145, "stone", "cobblestone")
    assert pm.pipes[1].gap_size == 145
    assert pm.pipes[1].block_main == "stone"
    assert pm.pipes[1].block_edge == "cobblestone"


def test_pipe_removed_once_fully_off_screen():
    pm = PipeManager(160, "dirt", "grass_side")
    first_pipe = pm.pipes[0]
    frames = 0
    while first_pipe in pm.pipes and frames < 5000:
        pm.update(2.5, 160, "dirt", "grass_side")
        frames += 1
    assert first_pipe not in pm.pipes
    assert first_pipe.x + PIPE_W < 0


# --- desenho: duas faixas pre-renderizadas por coluna (R27.2) --------------------


def _use(screen: tuple[int, int]) -> None:
    """Ativa o canvas daquela tela."""
    config.set_viewport(compute(*screen))


def _draw_the_v2_way(renderer: render.Renderer, tex: dict[str, pygame.Surface], pipe: PipePair) -> None:
    """Reproducao literal do `PipePair.draw` da v2, para servir de referencia.

    Sem ela a equivalencia visual nao teria contra o que ser comparada, e a contagem
    de desenhos nao diria de quanto foi a queda."""
    main_img = renderer.image(pipe.block_main, lambda: tex[pipe.block_main])
    edge_img = renderer.image(pipe.block_edge, lambda: tex[pipe.block_edge])
    x = round(pipe.x)

    top = pipe.top_rect
    y = top.bottom - BLOCK
    first = True
    while y > -BLOCK:
        renderer.draw(edge_img if first else main_img, (x, y))
        y -= BLOCK
        first = False

    bottom = pipe.bottom_rect
    y = bottom.top
    first = True
    while y < bottom.bottom:
        renderer.draw(edge_img if first else main_img, (x, y))
        y += BLOCK
        first = False


def _pipe(gap_y: float, x: float = 100.0, blocks: tuple[str, str] = ("dirt", "grass_side")) -> PipePair:
    """Coluna com a abertura onde o teste quiser."""
    return PipePair(x, gap_y, 160, *blocks)


def _drawn(pipe: PipePair, *, v2: bool) -> pygame.Surface:
    """Canvas com a coluna desenhada por um dos dois caminhos, sobre fundo magenta."""
    canvas = config.viewport().canvas
    renderer = render.SurfaceRenderer(canvas, canvas)
    renderer.clear((255, 0, 255))
    tex = textures.generate_all(BLOCK)
    if v2:
        _draw_the_v2_way(renderer, tex, pipe)
    else:
        pipe.draw(renderer, tex)
    return renderer.snapshot()


def _record(pipe: PipePair) -> FakeRenderer:
    """Um frame com uma coluna so, registrado sem pintar pixels."""
    renderer = FakeRenderer(config.viewport().canvas)
    pipe.draw(renderer, textures.generate_all(BLOCK))
    return renderer


def test_a_pipe_is_two_draw_calls() -> None:
    """O que a task 54 entrega: uma faixa recortada por metade da coluna."""
    assert len(_record(_pipe(360.0)).draws) == 2


def test_the_v2_way_needed_ten_draws_for_the_same_pipe() -> None:
    """Ancora do teste acima: sem ela, "2 desenhos" nao diria de quanto foi a queda.

    O custo da v2 crescia com a altura do canvas — a coluna sempre vai do topo ao
    chao, menos a abertura —, e o novo nao cresce."""
    renderer = FakeRenderer(config.viewport().canvas)
    _draw_the_v2_way(renderer, textures.generate_all(BLOCK), _pipe(360.0))
    assert len(renderer.draws) == 10


def test_both_halves_come_from_their_own_strip() -> None:
    """Uma faixa tem a fileira de borda embaixo e a outra em cima: sao imagens
    diferentes, e nao a mesma virada."""
    keys = [key for key, _ in _record(_pipe(360.0)).draws]
    assert keys == [
        ("pipe_top", "dirt", "grass_side", PLAY_H),
        ("pipe_bottom", "dirt", "grass_side", PLAY_H),
    ]


def test_the_two_strips_are_built_once_for_all_pipes_of_a_biome() -> None:
    """Pre-renderizar so vale se a faixa servir a coluna seguinte."""
    renderer = FakeRenderer(config.viewport().canvas)
    tex = textures.generate_all(BLOCK)
    for x in (60.0, 200.0, 340.0):
        _pipe(360.0, x).draw(renderer, tex)
    assert len(renderer.draws) == 6
    assert len(renderer._images) == 2


def test_a_pipe_of_another_biome_gets_its_own_pair_of_strips() -> None:
    """O bioma continua congelado na criacao da coluna (R2.5)."""
    renderer = FakeRenderer(config.viewport().canvas)
    tex = textures.generate_all(BLOCK)
    _pipe(360.0, 60.0).draw(renderer, tex)
    _pipe(360.0, 200.0, ("netherrack", "obsidian")).draw(renderer, tex)
    assert len(renderer._images) == 4


def test_an_opening_flush_with_the_ceiling_draws_only_the_bottom_half() -> None:
    """Caso extremo alcancavel: com `gap_y` no minimo e a abertura maxima, a coluna
    de cima tem altura zero. A v2 simplesmente nao entrava no laco; aqui o recorte
    vazio precisa ser evitado na mao, porque um `area` de altura 0 nao e desenho."""
    _use(SQUARE_2_3)
    pipe = _pipe(float(GAP_MARGIN))
    assert pipe.top_rect.height == 0  # ancora: o caso e mesmo este
    keys = [key for key, _ in _record(pipe).draws]
    assert keys == [("pipe_bottom", "dirt", "grass_side", PLAY_H)]


# --- descarte por posicao (R27.7) ------------------------------------------------


def test_the_pipe_born_at_the_play_edge_is_not_drawn_on_a_2_3_canvas() -> None:
    """A coluna que a v2 desenhava inteira toda vez sem ninguem poder ve-la: num
    canvas 2:3 `play.right` e a propria borda da tela."""
    _use(SQUARE_2_3)
    pm = PipeManager(160, "dirt", "grass_side")
    assert pm.pipes[0].x == config.screen_w()  # ancora: a coluna esta mesmo na borda
    renderer = FakeRenderer(config.viewport().canvas)
    pm.draw(renderer, textures.generate_all(BLOCK))
    assert renderer.draws == []


def test_the_pipe_born_at_the_play_edge_is_drawn_on_a_wide_canvas() -> None:
    """O outro lado da regra: numa tela larga a coluna nasce dentro do canvas, e la
    ela existe de verdade — quem a esconde e a faixa lateral, desenhada depois
    (R24.4). Descartar contra a area jogavel deixaria um buraco onde a faixa nao
    cobrisse."""
    _use(WIDE)
    pm = PipeManager(160, "dirt", "grass_side")
    assert config.play().right < config.screen_w()  # ancora: a tela tem mesmo faixa
    renderer = FakeRenderer(config.viewport().canvas)
    pm.draw(renderer, textures.generate_all(BLOCK))
    assert len(renderer.draws) == 2


@pytest.mark.parametrize(
    ("x", "drawn"),
    [(-PIPE_W - 1, False), (-PIPE_W, False), (-PIPE_W + 1, True), (PLAY_W - 1, True), (PLAY_W, False)],
)
def test_visibility_is_decided_by_the_canvas_edges(x: float, drawn: bool) -> None:
    """As bordas exatas do recorte, um pixel de cada lado."""
    _use(SQUARE_2_3)
    assert _pipe(360.0, float(x)).visible() is drawn


def test_a_pipe_still_on_the_canvas_keeps_being_drawn_while_it_leaves() -> None:
    """O descarte nao pode comer a saida da coluna pela esquerda: ela continua
    visivel ate o ultimo pixel."""
    _use(SQUARE_2_3)
    pipe = _pipe(360.0, -PIPE_W + 3)
    assert len(_record(pipe).draws) == 2
    canvas = _drawn(pipe, v2=False)
    assert canvas.get_at((0, 10))[:3] != (255, 0, 255)  # os 3px que ainda entram na tela
    assert canvas.get_at((3, 10))[:3] == (255, 0, 255)  # e nada alem deles


# --- equivalencia visual com a implementacao anterior -----------------------------


@pytest.mark.parametrize("screen", [SQUARE_2_3, WIDE], ids=["2:3", "wide"])
@pytest.mark.parametrize("gap_y", [200.0, 360.0, 543.0])
@pytest.mark.parametrize("blocks", BIOME_BLOCKS, ids=["overworld", "nether"])
def test_the_strips_draw_exactly_what_the_v2_loop_drew(
    screen: tuple[int, int], gap_y: float, blocks: tuple[str, str]
) -> None:
    """Igualdade exata de pixel acima da linha do chao.

    Abaixo dela os dois caminhos divergem de proposito e sem consequencia: a v2
    desenhava o ultimo bloco inteiro, transbordando ate 47px por baixo de
    `ground_y()`, e a faixa recorta exatamente na linha. O chao e desenhado depois
    das colunas e cobre os dois casos igual."""
    _use(screen)
    pipe = _pipe(gap_y, 100.0, blocks)
    new = _drawn(pipe, v2=False)
    old = _drawn(pipe, v2=True)
    different = [
        (x, y)
        for x in range(round(pipe.x) - 2, round(pipe.x) + PIPE_W + 2)
        for y in range(0, config.ground_y())
        if new.get_at((x, y)) != old.get_at((x, y))
    ]
    assert different == []


def test_the_pipe_really_covers_both_halves_of_the_column() -> None:
    """Ancora da comparacao acima: as duas poderiam concordar por nao desenharem
    nada. A coluna vai do topo ao chao, com a abertura no meio."""
    _use(SQUARE_2_3)
    pipe = _pipe(360.0)
    canvas = _drawn(pipe, v2=False)
    x = round(pipe.x) + PIPE_W // 2
    assert canvas.get_at((x, 0))[:3] != (255, 0, 255)  # encosta no topo
    assert canvas.get_at((x, config.ground_y() - 1))[:3] != (255, 0, 255)  # e no chao
    assert canvas.get_at((x, round(pipe.gap_y)))[:3] == (255, 0, 255)  # a abertura ficou vazia
