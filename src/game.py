"""Classe Game: loop principal e maquina de estados."""

import pygame

from src import textures
from src.bird import Bird
from src.config import BLOCK, FPS, SCREEN_H, SCREEN_W, TITLE


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.textures = textures.generate_all(BLOCK)
        self.bird = Bird(SCREEN_W // 4, SCREEN_H // 2)

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_UP):
                self.bird.flap()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.bird.flap()

    def update(self) -> None:
        self.bird.update()

    def draw(self) -> None:
        self.screen.fill((135, 206, 235))
        self.bird.draw(self.screen, self.textures)
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()
        pygame.quit()
