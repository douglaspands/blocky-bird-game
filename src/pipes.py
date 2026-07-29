"""PipePair e PipeManager: obstaculos do jogo (R2)."""

import random

import pygame

from src.config import (
    BLOCK,
    GAP_MARGIN,
    GAP_SIZE,
    GROUND_H,
    PIPE_SPACING,
    PIPE_SPEED,
    PIPE_W,
    SCREEN_H,
    SCREEN_W,
)

MAIN_TEXTURE = "dirt"
EDGE_TEXTURE = "grass_side"


class PipePair:
    def __init__(self, x: float, gap_y: float, gap_size: int) -> None:
        self.x = x
        self.gap_y = gap_y
        self.gap_size = gap_size
        self.scored = False

    @property
    def top_rect(self) -> pygame.Rect:
        bottom = round(self.gap_y - self.gap_size / 2)
        return pygame.Rect(round(self.x), 0, PIPE_W, bottom)

    @property
    def bottom_rect(self) -> pygame.Rect:
        top = round(self.gap_y + self.gap_size / 2)
        ground_y = SCREEN_H - GROUND_H
        return pygame.Rect(round(self.x), top, PIPE_W, ground_y - top)

    def off_screen(self) -> bool:
        return self.x + PIPE_W < 0

    def draw(self, surface: pygame.Surface, textures: dict[str, pygame.Surface]) -> None:
        """Desenha a coluna como pilha de blocos, com bloco de borda na boca da abertura (R2.5)."""
        main_tex = textures[MAIN_TEXTURE]
        edge_tex = textures[EDGE_TEXTURE]
        x = round(self.x)

        top = self.top_rect
        y = top.bottom - BLOCK
        first = True
        while y > -BLOCK:
            surface.blit(edge_tex if first else main_tex, (x, y))
            y -= BLOCK
            first = False

        bottom = self.bottom_rect
        y = bottom.top
        first = True
        while y < bottom.bottom:
            surface.blit(edge_tex if first else main_tex, (x, y))
            y += BLOCK
            first = False


class PipeManager:
    def __init__(self, speed: float = PIPE_SPEED, gap_size: int = GAP_SIZE) -> None:
        self.speed = speed
        self.gap_size = gap_size
        self.pipes: list[PipePair] = []
        self._spawn(SCREEN_W)

    def _spawn(self, x: float) -> None:
        gap_y = random.uniform(GAP_MARGIN, SCREEN_H - GROUND_H - GAP_MARGIN)
        self.pipes.append(PipePair(x, gap_y, self.gap_size))

    def update(self) -> None:
        """Move as colunas (R2.3), spawna novas (R2.1/R2.2) e remove as que saem da tela (R2.4)."""
        for pipe in self.pipes:
            pipe.x -= self.speed

        if self.pipes[-1].x <= SCREEN_W - PIPE_SPACING:
            self._spawn(self.pipes[-1].x + PIPE_SPACING)

        self.pipes = [p for p in self.pipes if not p.off_screen()]

    def draw(self, surface: pygame.Surface, textures: dict[str, pygame.Surface]) -> None:
        for pipe in self.pipes:
            pipe.draw(surface, textures)
