"""Decoracao de fundo com parallax, duas camadas por bioma (R7.4)."""

import random
from typing import Callable

import pygame

from src.config import GROUND_H, SCREEN_H, SCREEN_W

FAR_FACTOR = 0.3
NEAR_FACTOR = 0.6

GROUND_Y = SCREEN_H - GROUND_H

Drawer = Callable[[pygame.Surface, int, int], None]


def _tile(surface: pygame.Surface, scrolled: float, period: int, drawer: Drawer) -> None:
    first_idx = int(scrolled // period)
    x = -(scrolled % period)
    idx = first_idx
    while x < SCREEN_W:
        drawer(surface, round(x), idx)
        x += period
        idx += 1


def _draw_clouds(surface: pygame.Surface, x: int, idx: int) -> None:
    rng = random.Random(idx * 13 + 1)
    y = 40 + rng.randint(0, 120)
    w = rng.randint(50, 90)
    h = rng.randint(18, 30)
    rect = pygame.Rect(0, 0, w, h)
    rect.center = (x + w // 2, y)
    pygame.draw.ellipse(surface, (255, 255, 255), rect)


def _draw_hills(surface: pygame.Surface, x: int, idx: int) -> None:
    rng = random.Random(idx * 17 + 2)
    w = rng.randint(120, 200)
    h = rng.randint(40, 90)
    rect = pygame.Rect(0, 0, w, h * 2)
    rect.midbottom = (x + w // 2, GROUND_Y + h)
    pygame.draw.ellipse(surface, (90, 160, 70), rect)


def _draw_stalactites(surface: pygame.Surface, x: int, idx: int) -> None:
    rng = random.Random(idx * 19 + 3)
    w = rng.randint(20, 40)
    h = rng.randint(40, 100)
    points = [(x, 0), (x + w, 0), (x + w // 2, h)]
    pygame.draw.polygon(surface, (55, 55, 62), points)


def _draw_ore_veins(surface: pygame.Surface, x: int, idx: int) -> None:
    rng = random.Random(idx * 23 + 4)
    y = rng.randint(150, GROUND_Y - 150)
    color = rng.choice([(120, 190, 255), (255, 215, 60), (200, 200, 210)])
    for _ in range(4):
        ox = rng.randint(-15, 15)
        oy = rng.randint(-15, 15)
        pygame.draw.rect(surface, color, (x + ox, y + oy, 6, 6))


def _draw_lava_pools(surface: pygame.Surface, x: int, idx: int) -> None:
    rng = random.Random(idx * 29 + 5)
    w = rng.randint(100, 180)
    h = rng.randint(20, 40)
    rect = pygame.Rect(0, 0, w, h)
    rect.midbottom = (x + w // 2, GROUND_Y)
    pygame.draw.ellipse(surface, (230, 100, 20), rect)


def _draw_pillars(surface: pygame.Surface, x: int, idx: int) -> None:
    rng = random.Random(idx * 31 + 6)
    w = rng.randint(24, 40)
    h = rng.randint(100, 220)
    pygame.draw.rect(surface, (50, 30, 35), (x, GROUND_Y - h, w, h))


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
        far_period, far_drawer = _LAYERS[decor_id][0]
        near_period, near_drawer = _LAYERS[decor_id][1]
        _tile(surface, self.far_scrolled, far_period, far_drawer)
        _tile(surface, self.near_scrolled, near_period, near_drawer)
