"""Chao pre-renderizado: uma faixa por par de blocos, um desenho por frame (R27.2)."""

import pygame
import pytest

from src import config, render, textures
from src.config import BLOCK, GROUND_H
from src.ground import Ground
from src.viewport import PLAY_H, PLAY_W, compute
from tests.fakes import FakeRenderer

PHONE = (1080, 2400)  # canvas 480x1067: 96px de chao decorativo abaixo da area jogavel
WIDE = (1920, 1080)  # canvas 1280x720: quase o triplo de colunas de bloco
SQUARE_2_3 = (PLAY_W, PLAY_H)  # a geometria da v2, sem faixa nenhuma
BIOME_BLOCKS = [("dirt", "grass_side"), ("netherrack", "obsidian")]


def _use(screen: tuple[int, int]) -> None:
    """Ativa o canvas daquela tela."""
    config.set_viewport(compute(*screen))


def _draw_the_v2_way(
    renderer: render.Renderer,
    tex: dict[str, pygame.Surface],
    block_main: str,
    block_edge: str,
    offset: float,
) -> None:
    """Reproducao literal do `Ground.draw` da v2, para servir de referencia.

    Sem ela a equivalencia visual nao teria contra o que ser comparada: o teste diria
    apenas que a faixa desenha *alguma coisa*, e nao que desenha a mesma parede de
    blocos que o jogo desenhava antes."""
    main_img = renderer.image(block_main, lambda: tex[block_main])
    edge_img = renderer.image(block_edge, lambda: tex[block_edge])
    top_y = config.ground_y()
    canvas_w = config.screen_w()
    canvas_h = config.screen_h()

    x = round(offset) - BLOCK
    while x < canvas_w:
        renderer.draw(edge_img, (x, top_y))
        y = top_y + BLOCK
        while y < canvas_h:
            renderer.draw(main_img, (x, y))
            y += BLOCK
        x += BLOCK


def _drawn(screen: tuple[int, int], offset: float, blocks: tuple[str, str], *, v2: bool) -> pygame.Surface:
    """Canvas com o chao desenhado por um dos dois caminhos, sobre fundo magenta."""
    _use(screen)
    canvas = config.viewport().canvas
    renderer = render.SurfaceRenderer(canvas, canvas)
    renderer.clear((255, 0, 255))  # qualquer pixel remanescente denuncia buraco
    tex = textures.generate_all(BLOCK)
    if v2:
        _draw_the_v2_way(renderer, tex, *blocks, offset)
    else:
        ground = Ground()
        ground.offset = offset
        ground.draw(renderer, tex, *blocks)
    return renderer.snapshot()


def _ground_frame(screen: tuple[int, int], offset: float = 0.0) -> FakeRenderer:
    """Um frame de chao registrado, sem pintar pixels."""
    _use(screen)
    renderer = FakeRenderer(config.viewport().canvas)
    ground = Ground()
    ground.offset = offset
    ground.draw(renderer, textures.generate_all(BLOCK), "dirt", "grass_side")
    return renderer


# --- o ganho: de 22 blits para 1 (R27.2) ----------------------------------------


def test_a_ground_frame_is_a_single_draw_call() -> None:
    """O que a task 53 entrega, medido no canvas 2:3 da v2."""
    assert len(_ground_frame(SQUARE_2_3).draws) == 1


def test_the_v2_way_needed_twenty_two_draws_for_the_same_frame() -> None:
    """Ancora do teste acima: sem ela, "1 desenho" nao diria de quanto foi a queda."""
    _use(SQUARE_2_3)
    renderer = FakeRenderer(config.viewport().canvas)
    _draw_the_v2_way(renderer, textures.generate_all(BLOCK), "dirt", "grass_side", 0.0)
    assert len(renderer.draws) == 22  # 11 colunas x (1 borda + 1 preenchimento)


def test_a_wider_canvas_still_takes_a_single_draw_call() -> None:
    """O custo do chao deixou de crescer com a largura da tela — no canvas de 1280 a
    v2 pagaria 27 colunas."""
    assert len(_ground_frame(WIDE).draws) == 1


def test_the_strip_is_built_once_and_reused_across_frames() -> None:
    """Pre-renderizar so vale se o resultado sobreviver ao frame que o construiu."""
    _use(SQUARE_2_3)
    renderer = FakeRenderer(config.viewport().canvas)
    tex = textures.generate_all(BLOCK)
    ground = Ground()

    for _ in range(3):
        ground.update(3.0)
        ground.draw(renderer, tex, "dirt", "grass_side")

    assert len(renderer.draws) == 3  # um por frame
    assert len(renderer._images) == 1  # e uma unica faixa por tras dos tres
    whole_ground = pygame.Rect(0, config.ground_y(), PLAY_W, GROUND_H)
    assert all(rect == whole_ground for _, rect in renderer.draws)


def test_each_biome_pair_gets_its_own_strip() -> None:
    """As texturas continuam sendo as do bioma atual, sem congelamento (R7.3)."""
    _use(SQUARE_2_3)
    renderer = FakeRenderer(config.viewport().canvas)
    tex = textures.generate_all(BLOCK)
    ground = Ground()
    ground.draw(renderer, tex, "dirt", "grass_side")
    ground.draw(renderer, tex, "netherrack", "obsidian")
    assert len(renderer._images) == 2
    assert [key for key, _ in renderer.draws] == [
        ("ground", "dirt", "grass_side", PLAY_W, GROUND_H),
        ("ground", "netherrack", "obsidian", PLAY_W, GROUND_H),
    ]


# --- o rolamento (R7.3) ----------------------------------------------------------


@pytest.mark.parametrize("offset", [0.0, 1.4, 24.0, 47.6])
def test_scrolling_moves_the_source_rectangle_and_not_the_destination(offset: float) -> None:
    """O destino e sempre o canvas inteiro; o que anda e a janela dentro da faixa."""
    renderer = _ground_frame(SQUARE_2_3, offset)
    _, _, dest, area = renderer._of("draw")[0]
    assert dest == pygame.Rect(0, config.ground_y(), PLAY_W, GROUND_H)
    assert area == pygame.Rect(BLOCK - round(offset), 0, PLAY_W, GROUND_H)


def test_the_source_rectangle_never_leaves_the_strip() -> None:
    """A faixa tem `canvas_w + BLOCK` de largura justamente para isto: em qualquer
    ponto do ciclo de rolamento a origem cabe inteira dentro dela."""
    _use(SQUARE_2_3)
    ground = Ground()
    strip_w = PLAY_W + BLOCK
    for _ in range(200):
        ground.update(3.7)  # velocidade quebrada: passa por todo o ciclo, sem alinhar
        source_x = BLOCK - round(ground.offset)
        assert source_x >= 0
        assert source_x + PLAY_W <= strip_w


# --- equivalencia visual com a implementacao anterior -----------------------------


@pytest.mark.parametrize("screen", [SQUARE_2_3, PHONE, WIDE], ids=["2:3", "phone", "wide"])
@pytest.mark.parametrize("offset", [0.0, 1.4, 24.0, 47.6])
@pytest.mark.parametrize("blocks", BIOME_BLOCKS, ids=["overworld", "nether"])
def test_the_strip_draws_exactly_what_the_v2_loop_drew(
    screen: tuple[int, int], offset: float, blocks: tuple[str, str]
) -> None:
    """Igualdade exata de pixel, e nao aproximada: a faixa e um recorte das mesmas
    texturas nas mesmas posicoes, entao qualquer diferenca seria erro de geometria."""
    new = _drawn(screen, offset, blocks, v2=False)
    old = _drawn(screen, offset, blocks, v2=True)
    canvas_w, canvas_h = config.viewport().canvas
    different = [
        (x, y)
        for x in range(0, canvas_w, 3)
        for y in range(config.ground_y(), canvas_h, 3)
        if new.get_at((x, y)) != old.get_at((x, y))
    ]
    assert different == []


def test_the_ground_covers_the_canvas_from_edge_to_edge() -> None:
    """Ancora da comparacao acima: as duas poderiam concordar por nao desenharem
    nada. Nenhum pixel de chao pode continuar magenta, nem na coluna final parcial
    nem na fileira que desce pela faixa decorativa (R25.1)."""
    canvas = _drawn(PHONE, 13.0, BIOME_BLOCKS[0], v2=False)
    canvas_w, canvas_h = config.viewport().canvas
    for x in (0, canvas_w // 2, canvas_w - 1):
        for y in (config.ground_y(), config.ground_y() + BLOCK, canvas_h - 1):
            assert canvas.get_at((x, y))[:3] != (255, 0, 255)
