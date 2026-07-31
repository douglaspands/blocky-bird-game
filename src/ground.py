"""Chao rolante de blocos, sincronizado a velocidade das colunas (R7.3)."""

import pygame

from src import config
from src.config import BLOCK, GROUND_H


class Ground:
    def __init__(self) -> None:
        self.offset = 0.0

    def update(self, speed: float) -> None:
        self.offset = (self.offset - speed) % BLOCK

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(0, config.ground_y(), config.screen_w(), GROUND_H)

    def draw(
        self,
        surface: pygame.Surface,
        textures: dict[str, pygame.Surface],
        block_main: str,
        block_edge: str,
    ) -> None:
        """Usa sempre as texturas do bioma atual, sem congelamento (R7.3)."""
        main_tex = textures[block_main]
        edge_tex = textures[block_edge]
        top_y = config.ground_y()
        # icados para locais: sao os limites dos dois lacos de blit, e resolver o
        # viewport a cada iteracao seria trabalho repetido no caminho quente.
        canvas_w = config.screen_w()
        canvas_h = config.screen_h()

        x = round(self.offset) - BLOCK
        while x < canvas_w:
            surface.blit(edge_tex, (x, top_y))
            y = top_y + BLOCK
            while y < canvas_h:
                surface.blit(main_tex, (x, y))
                y += BLOCK
            x += BLOCK
