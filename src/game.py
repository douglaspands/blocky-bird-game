"""Classe Game: loop principal e maquina de estados."""

import pygame

from src import textures
from src.config import BLOCK, FPS, SCREEN_H, SCREEN_W, TITLE


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.textures = textures.generate_all(BLOCK)

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update(self) -> None:
        pass

    def draw(self) -> None:
        # Tela de teste temporaria: exibe as texturas geradas (task 2, R7.1/R7.2).
        self.screen.fill((135, 206, 235))
        margin = 20
        x = y = margin
        for tex in self.textures.values():
            self.screen.blit(tex, (x, y))
            x += BLOCK + margin
            if x + BLOCK > SCREEN_W:
                x = margin
                y += BLOCK + margin
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()
        pygame.quit()
