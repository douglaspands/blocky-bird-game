"""Decoracao de fundo com parallax, duas camadas por bioma (R7.4)."""

import random
from collections.abc import Callable, Iterator

import pygame

from src import config, render

FAR_FACTOR = 0.3
NEAR_FACTOR = 0.6

Drawer = Callable[[render.Renderer, int, int, int], None]


def _tile(renderer: render.Renderer, scrolled: float, period: int, ground_y: int, drawer: Drawer) -> None:
    """Ladrilha ate a largura do canvas logico (R25.5) — mais larga que a area jogavel
    sempre que a tela nao e 2:3, entao o parallax cobre a tela toda em vez de parar
    nos 480px de mundo."""
    first_idx = int(scrolled // period)
    x = -(scrolled % period)
    idx = first_idx
    width = renderer.size[0]
    while x < width:
        drawer(renderer, round(x), idx, ground_y)
        x += period
        idx += 1


CLOUD_UNIT = 14
CLOUD_SHAPES = [
    # cada linha: (deslocamento em unidades, largura em unidades), de cima para baixo
    [(2, 4), (1, 6), (0, 8), (1, 6)],
    [(3, 3), (1, 6), (0, 9), (2, 5)],
    [(2, 3), (0, 7), (1, 6)],
]

HILL_UNIT = 18
HILL_SHAPES = [
    # cada linha: (deslocamento em unidades, largura em unidades), de cima para baixo (topo -> chao)
    [(3, 2), (2, 4), (1, 6), (0, 8)],
    [(4, 1), (2, 5), (1, 7), (0, 9)],
    [(2, 3), (1, 5), (0, 7)],
]


def _draw_block_shape(
    renderer: render.Renderer,
    shape: list[tuple[int, int]],
    x: int,
    top_y: int,
    unit: int,
    color: tuple[int, int, int],
) -> None:
    """Desenha uma forma quadriculada (pilha de retangulos), estilo voxel Minecraft."""
    for row_i, (col_offset, width_units) in enumerate(shape):
        y = top_y + row_i * unit
        rect = pygame.Rect(x + col_offset * unit, y, width_units * unit, unit)
        renderer.fill(color, rect)


def _draw_clouds(renderer: render.Renderer, x: int, idx: int, ground_y: int) -> None:
    rng = random.Random(idx * 13 + 1)
    shape = rng.choice(CLOUD_SHAPES)
    top_y = 40 + rng.randint(0, 100)
    _draw_block_shape(renderer, shape, x, top_y, CLOUD_UNIT, (255, 255, 255))


def _draw_hills(renderer: render.Renderer, x: int, idx: int, ground_y: int) -> None:
    rng = random.Random(idx * 17 + 2)
    shape = rng.choice(HILL_SHAPES)
    top_y = ground_y - len(shape) * HILL_UNIT
    _draw_block_shape(renderer, shape, x, top_y, HILL_UNIT, (90, 160, 70))


STALACTITE_COLOR = (55, 55, 62)
LAVA_COLOR = (230, 100, 20)
PILLAR_COLOR = (50, 30, 35)


def _paint_triangle(size: tuple[int, int], color: tuple[int, int, int]) -> pygame.Surface:
    """Pinta um triangulo apontando para baixo, do tamanho pedido."""
    width, height = size
    surface = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.polygon(surface, color, [(0, 0), (width, 0), (width // 2, height)])
    return surface


def _paint_ellipse(size: tuple[int, int], color: tuple[int, int, int]) -> pygame.Surface:
    """Pinta uma elipse preenchendo o retangulo do tamanho pedido."""
    surface = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.ellipse(surface, color, pygame.Rect((0, 0), size))
    return surface


def _draw_stalactites(renderer: render.Renderer, x: int, idx: int, ground_y: int) -> None:
    """Estalactite: a unica forma do parallax que nao e retangulo.

    O renderizador so preenche retangulos, entao o triangulo e pintado numa
    superficie e guardado como imagem, chaveada pelo seu tamanho — os sorteios
    produzem poucas combinacoes distintas, e a partir da segunda aparicao de cada uma
    o desenho e uma draw call."""
    rng = random.Random(idx * 19 + 3)
    size = (rng.randint(20, 40), rng.randint(40, 100))
    image = renderer.image(("stalactite", size), lambda: _paint_triangle(size, STALACTITE_COLOR))
    renderer.draw(image, (x, 0))


def ore_vein_shapes(x: int, idx: int, ground_y: int) -> Iterator[tuple[tuple[int, int, int], pygame.Rect]]:
    """Gera os quatro cubos de um veio de minerio, com a cor sorteada por `idx`.

    Publico e devolvendo formas, em vez de desenhar, porque tem dois consumidores que
    pintam em alvos diferentes: a camada de parallax da Cave, que preenche pelo
    renderizador, e as faixas laterais, que constroem uma superficie uma unica vez
    (`bands.py`, R25.2)."""
    rng = random.Random(idx * 23 + 4)
    y = rng.randint(150, ground_y - 150)
    color = rng.choice([(120, 190, 255), (255, 215, 60), (200, 200, 210)])
    for _ in range(4):
        ox = rng.randint(-15, 15)
        oy = rng.randint(-15, 15)
        yield color, pygame.Rect(x + ox, y + oy, 6, 6)


def _draw_ore_veins(renderer: render.Renderer, x: int, idx: int, ground_y: int) -> None:
    for color, rect in ore_vein_shapes(x, idx, ground_y):
        renderer.fill(color, rect)


def _draw_lava_pools(renderer: render.Renderer, x: int, idx: int, ground_y: int) -> None:
    """Poca de lava: elipse assentada na linha do chao, pela mesma razao da estalactite."""
    rng = random.Random(idx * 29 + 5)
    size = (rng.randint(100, 180), rng.randint(20, 40))
    image = renderer.image(("lava_pool", size), lambda: _paint_ellipse(size, LAVA_COLOR))
    renderer.draw(image, (x, ground_y - size[1]))


def _draw_pillars(renderer: render.Renderer, x: int, idx: int, ground_y: int) -> None:
    rng = random.Random(idx * 31 + 6)
    w = rng.randint(24, 40)
    h = rng.randint(100, 220)
    renderer.fill(PILLAR_COLOR, pygame.Rect(x, ground_y - h, w, h))


_LAYERS: dict[str, tuple[tuple[int, Drawer], tuple[int, Drawer]]] = {
    "overworld": ((220, _draw_clouds), (150, _draw_hills)),
    "cave": ((130, _draw_stalactites), (100, _draw_ore_veins)),
    "nether": ((200, _draw_lava_pools), (170, _draw_pillars)),
}


class DecorManager:
    def __init__(self) -> None:
        self.far_scrolled = 0.0
        self.near_scrolled = 0.0

    def update(self, speed: float) -> None:
        self.far_scrolled += speed * FAR_FACTOR
        self.near_scrolled += speed * NEAR_FACTOR

    def draw(self, renderer: render.Renderer, decor_id: str) -> None:
        # a linha do chao vem da area jogavel, nao da base do canvas: colinas, poças
        # de lava e pilares tem que assentar no chao de verdade, nao afundar na faixa
        # decorativa de baixo (R25.1).
        ground_y = config.ground_y()
        far_period, far_drawer = _LAYERS[decor_id][0]
        near_period, near_drawer = _LAYERS[decor_id][1]
        _tile(renderer, self.far_scrolled, far_period, ground_y, far_drawer)
        _tile(renderer, self.near_scrolled, near_period, ground_y, near_drawer)
