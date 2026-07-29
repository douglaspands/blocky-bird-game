"""Chao rolante de blocos, sincronizado a velocidade das colunas (R7.3)."""

import pygame

from src.config import BLOCK, GROUND_H, SCREEN_H, SCREEN_W

MAIN_TEXTURE = "dirt"
EDGE_TEXTURE = "grass_side"


class Ground:
    def __init__(self, speed: float) -> None:
        self.speed = speed
        self.offset = 0.0

    def update(self) -> None:
        self.offset = (self.offset - self.speed) % BLOCK

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(0, SCREEN_H - GROUND_H, SCREEN_W, GROUND_H)

    def draw(self, surface: pygame.Surface, textures: dict[str, pygame.Surface]) -> None:
        main_tex = textures[MAIN_TEXTURE]
        edge_tex = textures[EDGE_TEXTURE]
        top_y = SCREEN_H - GROUND_H

        x = round(self.offset) - BLOCK
        while x < SCREEN_W:
            surface.blit(edge_tex, (x, top_y))
            y = top_y + BLOCK
            while y < SCREEN_H:
                surface.blit(main_tex, (x, y))
                y += BLOCK
            x += BLOCK
