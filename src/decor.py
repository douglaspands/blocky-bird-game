"""Decoracao de fundo com parallax, duas camadas por bioma (R7.4)."""

import random
from collections.abc import Callable

import pygame

from src.config import GROUND_H

FAR_FACTOR = 0.3
NEAR_FACTOR = 0.6

Drawer = Callable[[pygame.Surface, int, int, int], None]


def _tile(surface: pygame.Surface, scrolled: float, period: int, ground_y: int, drawer: Drawer) -> None:
    """Ladrilha ate a largura real da surface recebida (R14.3) — no Android essa
    largura pode ser maior que a area jogavel 480px, esticando o parallax para
    preencher a tela em vez de sobrar barra preta."""
    first_idx = int(scrolled // period)
    x = -(scrolled % period)
    idx = first_idx
    width = surface.get_width()
    while x < width:
        drawer(surface, round(x), idx, ground_y)
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
    surface: pygame.Surface,
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
        pygame.draw.rect(surface, color, rect)


def _draw_clouds(surface: pygame.Surface, x: int, idx: int, ground_y: int) -> None:
    rng = random.Random(idx * 13 + 1)
    shape = rng.choice(CLOUD_SHAPES)
    top_y = 40 + rng.randint(0, 100)
    _draw_block_shape(surface, shape, x, top_y, CLOUD_UNIT, (255, 255, 255))


def _draw_hills(surface: pygame.Surface, x: int, idx: int, ground_y: int) -> None:
    rng = random.Random(idx * 17 + 2)
    shape = rng.choice(HILL_SHAPES)
    top_y = ground_y - len(shape) * HILL_UNIT
    _draw_block_shape(surface, shape, x, top_y, HILL_UNIT, (90, 160, 70))


def _draw_stalactites(surface: pygame.Surface, x: int, idx: int, ground_y: int) -> None:
    rng = random.Random(idx * 19 + 3)
    w = rng.randint(20, 40)
    h = rng.randint(40, 100)
    points = [(x, 0), (x + w, 0), (x + w // 2, h)]
    pygame.draw.polygon(surface, (55, 55, 62), points)


def _draw_ore_veins(surface: pygame.Surface, x: int, idx: int, ground_y: int) -> None:
    rng = random.Random(idx * 23 + 4)
    y = rng.randint(150, ground_y - 150)
    color = rng.choice([(120, 190, 255), (255, 215, 60), (200, 200, 210)])
    for _ in range(4):
        ox = rng.randint(-15, 15)
        oy = rng.randint(-15, 15)
        pygame.draw.rect(surface, color, (x + ox, y + oy, 6, 6))


def _draw_lava_pools(surface: pygame.Surface, x: int, idx: int, ground_y: int) -> None:
    rng = random.Random(idx * 29 + 5)
    w = rng.randint(100, 180)
    h = rng.randint(20, 40)
    rect = pygame.Rect(0, 0, w, h)
    rect.midbottom = (x + w // 2, ground_y)
    pygame.draw.ellipse(surface, (230, 100, 20), rect)


def _draw_pillars(surface: pygame.Surface, x: int, idx: int, ground_y: int) -> None:
    rng = random.Random(idx * 31 + 6)
    w = rng.randint(24, 40)
    h = rng.randint(100, 220)
    pygame.draw.rect(surface, (50, 30, 35), (x, ground_y - h, w, h))


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

    def draw(self, surface: pygame.Surface, decor_id: str) -> None:
        ground_y = surface.get_height() - GROUND_H
        far_period, far_drawer = _LAYERS[decor_id][0]
        near_period, near_drawer = _LAYERS[decor_id][1]
        _tile(surface, self.far_scrolled, far_period, ground_y, far_drawer)
        _tile(surface, self.near_scrolled, near_period, ground_y, near_drawer)
