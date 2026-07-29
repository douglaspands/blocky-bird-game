"""Classe Game: loop principal e maquina de estados."""

import pygame

from src import textures
from src.bird import Bird
from src.config import BLOCK, FPS, SCREEN_H, SCREEN_W, TITLE
from src.ground import Ground
from src.pipes import PipeManager


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.textures = textures.generate_all(BLOCK)
        self.reset()

    def reset(self) -> None:
        self.bird = Bird(SCREEN_W // 4, SCREEN_H // 2)
        self.pipes = PipeManager()
        self.ground = Ground(self.pipes.speed)

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_UP):
                self.bird.flap()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.bird.flap()

    def _collided(self) -> bool:
        if self.bird.rect.colliderect(self.ground.rect):
            return True
        return any(
            self.bird.rect.colliderect(pipe.top_rect) or self.bird.rect.colliderect(pipe.bottom_rect)
            for pipe in self.pipes.pipes
        )

    def update(self) -> None:
        self.bird.update()
        self.pipes.update()
        self.ground.update()
        if self._collided():
            # Estado GAME_OVER ainda nao existe (task 6); por ora, reinicia direto (R3.1).
            self.reset()

    def draw(self) -> None:
        self.screen.fill((135, 206, 235))
        self.pipes.draw(self.screen, self.textures)
        self.ground.draw(self.screen, self.textures)
        self.bird.draw(self.screen, self.textures)
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()
        pygame.quit()
