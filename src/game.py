"""Classe Game: loop principal e maquina de estados (R6)."""

from enum import Enum, auto

import pygame

from src import textures, ui
from src.bird import Bird
from src.config import BLOCK, FPS, SCREEN_H, SCREEN_W, TITLE
from src.ground import Ground
from src.pipes import PipeManager


class GameState(Enum):
    PRONTO = auto()
    JOGANDO = auto()
    PAUSADO = auto()
    GAME_OVER = auto()


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.textures = textures.generate_all(BLOCK)
        self.score = 0
        self.highscore = 0
        self.reset()

    def reset(self) -> None:
        self.bird = Bird(SCREEN_W // 4, SCREEN_H // 2)
        self.pipes = PipeManager()
        self.ground = Ground(self.pipes.speed)
        self.score = 0
        self.state = GameState.PRONTO

    def _flap_action(self) -> None:
        if self.state == GameState.PRONTO:
            self.state = GameState.JOGANDO
            self.bird.flap()
        elif self.state == GameState.JOGANDO:
            self.bird.flap()
        elif self.state == GameState.GAME_OVER:
            self.reset()

    def _toggle_pause(self) -> None:
        if self.state == GameState.JOGANDO:
            self.state = GameState.PAUSADO
        elif self.state == GameState.PAUSADO:
            self.state = GameState.JOGANDO

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_UP):
                    self._flap_action()
                elif event.key in (pygame.K_ESCAPE, pygame.K_p):
                    self._toggle_pause()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._flap_action()

    def _collided(self) -> bool:
        if self.bird.rect.colliderect(self.ground.rect):
            return True
        return any(
            self.bird.rect.colliderect(pipe.top_rect) or self.bird.rect.colliderect(pipe.bottom_rect)
            for pipe in self.pipes.pipes
        )

    def update(self) -> None:
        if self.state == GameState.PRONTO:
            self.bird.update_idle()
        elif self.state == GameState.JOGANDO:
            self.bird.update()
            self.pipes.update()
            self.ground.update()
            if self._collided():
                self.state = GameState.GAME_OVER
                self.highscore = max(self.highscore, self.score)
        # PAUSADO e GAME_OVER: fisica e obstaculos ficam congelados (R3.3, R6.3).

    def draw(self) -> None:
        self.screen.fill((135, 206, 235))
        self.pipes.draw(self.screen, self.textures)
        self.ground.draw(self.screen, self.textures)
        self.bird.draw(self.screen, self.textures)

        if self.state == GameState.PRONTO:
            ui.draw_ready_screen(self.screen)
        elif self.state == GameState.PAUSADO:
            ui.draw_paused_overlay(self.screen)
        elif self.state == GameState.GAME_OVER:
            ui.draw_game_over_screen(self.screen, self.score, self.highscore)

        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()
        pygame.quit()
