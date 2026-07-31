"""PipePair e PipeManager: obstaculos do jogo (R2)."""

import random

import pygame

from src import config
from src.config import BLOCK, GAP_MARGIN, PIPE_SPACING, PIPE_W


class PipePair:
    def __init__(self, x: float, gap_y: float, gap_size: int, block_main: str, block_edge: str) -> None:
        self.x = x
        self.gap_y = gap_y
        self.gap_size = gap_size
        self.block_main = block_main
        self.block_edge = block_edge
        self.scored = False

    @property
    def top_rect(self) -> pygame.Rect:
        bottom = round(self.gap_y - self.gap_size / 2)
        return pygame.Rect(round(self.x), 0, PIPE_W, bottom)

    @property
    def bottom_rect(self) -> pygame.Rect:
        top = round(self.gap_y + self.gap_size / 2)
        return pygame.Rect(round(self.x), top, PIPE_W, config.ground_y() - top)

    def off_screen(self) -> bool:
        """Descarte na borda esquerda da area jogavel, nao do canvas (R2.4): o que
        sai dela ja esta atras da faixa decorativa e nao volta a ser visto."""
        return self.x + PIPE_W < config.play().left

    def draw(self, surface: pygame.Surface, textures: dict[str, pygame.Surface]) -> None:
        """Desenha a coluna como pilha de blocos do bioma congelado na criacao (R2.5)."""
        main_tex = textures[self.block_main]
        edge_tex = textures[self.block_edge]
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
    def __init__(self, gap_size: int, block_main: str, block_edge: str) -> None:
        self.pipes: list[PipePair] = []
        self._spawn(config.screen_w(), gap_size, block_main, block_edge)

    def _spawn(self, x: float, gap_size: int, block_main: str, block_edge: str) -> None:
        # a abertura e sorteada dentro da AREA JOGAVEL: com uma faixa de ceu acima,
        # `GAP_MARGIN` sozinho deixaria o centro da abertura cair na decoracao, fora
        # do alcance da abelha (R24.1, R25.1).
        gap_y = random.uniform(config.play().top + GAP_MARGIN, config.ground_y() - GAP_MARGIN)
        self.pipes.append(PipePair(x, gap_y, gap_size, block_main, block_edge))

    def update(self, speed: float, gap_size: int, block_main: str, block_edge: str) -> None:
        """Move as colunas (R2.3), spawna novas com o bioma atual (R2.1/R2.2/R2.5).

        Remove as que saem da tela (R2.4).
        """
        for pipe in self.pipes:
            pipe.x -= speed

        if self.pipes[-1].x <= config.screen_w() - PIPE_SPACING:
            self._spawn(self.pipes[-1].x + PIPE_SPACING, gap_size, block_main, block_edge)

        self.pipes = [p for p in self.pipes if not p.off_screen()]

    def draw(self, surface: pygame.Surface, textures: dict[str, pygame.Surface]) -> None:
        for pipe in self.pipes:
            pipe.draw(surface, textures)
