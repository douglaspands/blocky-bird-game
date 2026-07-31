"""Chao rolante de blocos, sincronizado a velocidade das colunas (R7.3)."""

import pygame

from src import config, render
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
        renderer: render.Renderer,
        textures: dict[str, pygame.Surface],
        block_main: str,
        block_edge: str,
    ) -> None:
        """Usa sempre as texturas do bioma atual, sem congelamento (R7.3)."""
        main_img = renderer.image(block_main, lambda: textures[block_main])
        edge_img = renderer.image(block_edge, lambda: textures[block_edge])
        top_y = config.ground_y()
        # icados para locais: sao os limites dos dois lacos de blit, e resolver o
        # viewport a cada iteracao seria trabalho repetido no caminho quente.
        canvas_w = config.screen_w()
        canvas_h = config.screen_h()

        x = round(self.offset) - BLOCK
        while x < canvas_w:
            renderer.draw(edge_img, (x, top_y))
            y = top_y + BLOCK
            while y < canvas_h:
                renderer.draw(main_img, (x, y))
                y += BLOCK
            x += BLOCK
