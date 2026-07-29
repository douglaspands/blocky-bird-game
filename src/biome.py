"""Definicoes de bioma e gerenciador de transicao (R5, R2.5, R7.3)."""

from dataclasses import dataclass

import pygame

from src import ui
from src.config import SCREEN_H, SCREEN_W

FADE_FRAMES = 60  # <= 1s a 60 FPS (R5.4)
BANNER_FRAMES = 90


@dataclass(frozen=True)
class Biome:
    id: str
    name: str
    threshold: int
    speed: float
    gap_size: int
    sky_top: tuple[int, int, int]
    sky_bottom: tuple[int, int, int]
    block_main: str
    block_edge: str
    decor: str


BIOMES: list[Biome] = [
    Biome(
        "overworld", "Overworld", 0, 2.5, 160,
        (135, 206, 235), (200, 230, 245), "dirt", "grass_side", "overworld",
    ),
    Biome(
        "cave", "Cave", 10, 3.0, 145,
        (25, 25, 35), (60, 58, 70), "stone", "cobblestone", "cave",
    ),
    Biome(
        "nether", "Nether", 25, 3.5, 130,
        (80, 15, 10), (150, 60, 20), "netherrack", "obsidian", "nether",
    ),
]


def _lerp_color(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(round(a + (b - a) * t) for a, b in zip(c1, c2))


def _make_gradient(top: tuple[int, int, int], bottom: tuple[int, int, int]) -> pygame.Surface:
    surf = pygame.Surface((SCREEN_W, SCREEN_H))
    for y in range(SCREEN_H):
        t = y / max(SCREEN_H - 1, 1)
        pygame.draw.line(surf, _lerp_color(top, bottom, t), (0, y), (SCREEN_W, y))
    return surf


def _biome_for_score(score: int) -> Biome:
    active = BIOMES[0]
    for biome in BIOMES:
        if score >= biome.threshold:
            active = biome
    return active


class BiomeManager:
    def __init__(self) -> None:
        self._gradients = {b.id: _make_gradient(b.sky_top, b.sky_bottom) for b in BIOMES}
        self.current = BIOMES[0]
        self.previous = BIOMES[0]
        self.fade_timer = 0
        self.banner_timer = 0

    def update(self, score: int) -> bool:
        """Detecta cruzamento de threshold (R5.1) e ativa fade + banner (R5.4). Retorna True se houve transicao."""
        target = _biome_for_score(score)
        if target.id != self.current.id:
            self.previous = self.current
            self.current = target
            self.fade_timer = FADE_FRAMES
            self.banner_timer = BANNER_FRAMES
            return True
        self.fade_timer = max(0, self.fade_timer - 1)
        self.banner_timer = max(0, self.banner_timer - 1)
        return False

    def draw_background(self, surface: pygame.Surface) -> None:
        current_grad = self._gradients[self.current.id]
        if self.fade_timer > 0:
            prev_grad = self._gradients[self.previous.id]
            prev_grad.set_alpha(255)
            surface.blit(prev_grad, (0, 0))
            alpha = round(255 * (1 - self.fade_timer / FADE_FRAMES))
            current_grad.set_alpha(alpha)
            surface.blit(current_grad, (0, 0))
        else:
            current_grad.set_alpha(255)
            surface.blit(current_grad, (0, 0))

    def draw_banner(self, surface: pygame.Surface) -> None:
        if self.banner_timer > 0:
            ui.draw_text(surface, self.current.name.upper(), (SCREEN_W // 2, 110), base_size=16)
