"""Classe Game: loop principal e maquina de estados (R6)."""

from enum import Enum, auto

import pygame

from src import score, textures, ui
from src.biome import BiomeManager
from src.bird import Bird
from src.config import BLOCK, FPS, PIPE_W, SCREEN_H, SCREEN_W, TITLE
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
        self.highscore = score.load_highscore()
        self.reset()

    def reset(self) -> None:
        self.bird = Bird(SCREEN_W // 4, SCREEN_H // 2)
        self.biome = BiomeManager()
        b = self.biome.current
        self.pipes = PipeManager(b.gap_size, b.block_main, b.block_edge)
        self.ground = Ground()
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

    def _update_score(self) -> None:
        """+1 por coluna ultrapassada, uma unica vez por coluna (R4.1)."""
        for pipe in self.pipes.pipes:
            if not pipe.scored and pipe.x + PIPE_W < self.bird.pos.x:
                pipe.scored = True
                self.score += 1

    def update(self) -> None:
        if self.state == GameState.PRONTO:
            self.bird.update_idle()
        elif self.state == GameState.JOGANDO:
            b = self.biome.current
            self.bird.update()
            self.pipes.update(b.speed, b.gap_size, b.block_main, b.block_edge)
            self.ground.update(b.speed)
            self._update_score()
            self.biome.update(self.score)
            if self._collided():
                self.state = GameState.GAME_OVER
                if self.score > self.highscore:
                    self.highscore = self.score
                    score.save_highscore(self.highscore)
        # PAUSADO e GAME_OVER: fisica, obstaculos e biomas ficam congelados (R3.3, R6.3).

    def draw(self) -> None:
        b = self.biome.current
        self.biome.draw_background(self.screen)
        self.pipes.draw(self.screen, self.textures)
        self.ground.draw(self.screen, self.textures, b.block_main, b.block_edge)
        self.bird.draw(self.screen, self.textures)
        self.biome.draw_banner(self.screen)

        if self.state == GameState.PRONTO:
            ui.draw_ready_screen(self.screen)
        elif self.state == GameState.JOGANDO:
            ui.draw_hud_score(self.screen, self.score)
        elif self.state == GameState.PAUSADO:
            ui.draw_hud_score(self.screen, self.score)
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
