"""Classe Game: loop principal e maquina de estados (R6)."""

from enum import Enum, auto

import pygame

from src import score, textures, ui
from src.biome import BiomeManager
from src.bird import Bird
from src.config import BLOCK, CREDITS, FPS, PIPE_W, SCREEN_H, SCREEN_W, TITLE
from src.decor import DecorManager
from src.ground import Ground
from src.input import ACTION_BACK, ACTION_FLAP, ACTION_MUTE, ACTION_PAUSE, InputManager
from src.particles import ParticleSystem
from src.pipes import PipeManager
from src.sounds import SoundManager


class GameState(Enum):
    PRONTO = auto()
    JOGANDO = auto()
    PAUSADO = auto()
    GAME_OVER = auto()


class Game:
    def __init__(self) -> None:
        pygame.init()
        # SCALED: SDL renderiza numa surface logica 480x720 e escala p/ a janela real
        # mantendo a proporcao (letterbox/pillarbox automatico, R9.1, R14.3). Todo o
        # jogo continua desenhando em coordenadas logicas 480x720.
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.SCALED | pygame.RESIZABLE)
        pygame.display.set_caption(f"{TITLE} - {CREDITS}")
        self.clock = pygame.time.Clock()
        self.running = True
        self.textures = textures.generate_all(BLOCK)
        self.sounds = SoundManager()
        self.input = InputManager()
        self.score = 0
        self.highscore = score.load_highscore()
        self.reset()

    def reset(self) -> None:
        self.bird = Bird(SCREEN_W // 4, SCREEN_H // 2)
        self.biome = BiomeManager()
        b = self.biome.current
        self.pipes = PipeManager(b.gap_size, b.block_main, b.block_edge)
        self.ground = Ground()
        self.decor = DecorManager()
        self.particles = ParticleSystem()
        self.score = 0
        self.state = GameState.PRONTO

    def _flap_action(self) -> None:
        if self.state == GameState.PRONTO:
            self.state = GameState.JOGANDO
            self.bird.flap()
            self.sounds.play("flap")
        elif self.state == GameState.JOGANDO:
            self.bird.flap()
            self.sounds.play("flap")
        elif self.state == GameState.GAME_OVER:
            self.reset()

    def _toggle_pause(self) -> None:
        if self.state == GameState.JOGANDO:
            self.state = GameState.PAUSADO
        elif self.state == GameState.PAUSADO:
            self.state = GameState.JOGANDO

    def _back_action(self) -> None:
        """BACK do Android pausa em JOGANDO; nos demais estados, encerra o
        jogo (R15.2, R15.3). Fica no Game (que conhece o estado), nao no
        InputManager, mantendo a separacao acao/estado da v1."""
        if self.state == GameState.JOGANDO:
            self._toggle_pause()
        else:
            self.running = False

    def handle_events(self) -> None:
        actions, quit_requested = self.input.poll()
        if quit_requested:
            self.running = False
        if ACTION_BACK in actions:
            self._back_action()
        if ACTION_FLAP in actions:
            self._flap_action()
        if ACTION_PAUSE in actions:
            self._toggle_pause()
        if ACTION_MUTE in actions:
            self.sounds.toggle_mute()

    def _collision_texture(self) -> str | None:
        """Retorna a chave da textura do bloco atingido, ou None se nao houve colisao (R3.2)."""
        if self.bird.rect.colliderect(self.ground.rect):
            return self.biome.current.block_main
        for pipe in self.pipes.pipes:
            if self.bird.rect.colliderect(pipe.top_rect) or self.bird.rect.colliderect(pipe.bottom_rect):
                return pipe.block_main
        return None

    def _update_score(self) -> None:
        """+1 por coluna ultrapassada, uma unica vez por coluna (R4.1). Grava o
        recorde no instante em que e superado, nao so no GAME_OVER — um
        encerramento abrupto do app pelo Android nao perde o recorde ja
        alcancado (R4.3, R16.4)."""
        for pipe in self.pipes.pipes:
            if not pipe.scored and pipe.x + PIPE_W < self.bird.pos.x:
                pipe.scored = True
                self.score += 1
                self.sounds.play("score")
                if self.score > self.highscore:
                    self.highscore = self.score
                    score.save_highscore(self.highscore)

    def update(self) -> None:
        if self.state == GameState.PRONTO:
            self.bird.update_idle()
        elif self.state == GameState.JOGANDO:
            b = self.biome.current
            self.bird.update()
            self.pipes.update(b.speed, b.gap_size, b.block_main, b.block_edge)
            self.ground.update(b.speed)
            self.decor.update(b.speed)
            self._update_score()
            if self.biome.update(self.score):
                self.sounds.play("portal")
            hit_texture = self._collision_texture()
            if hit_texture is not None:
                self.state = GameState.GAME_OVER
                self.particles.burst(self.bird.rect.center, self.textures[hit_texture])
                self.sounds.play("hit")
                # recorde ja foi gravado incrementalmente em _update_score() se superado
        # PAUSADO: fisica, obstaculos, biomas e particulas ficam congelados (R3.3, R6.3).
        if self.state != GameState.PAUSADO:
            self.particles.update()

    def draw(self) -> None:
        b = self.biome.current
        self.biome.draw_background(self.screen)
        self.decor.draw(self.screen, b.decor)
        self.pipes.draw(self.screen, self.textures)
        self.ground.draw(self.screen, self.textures, b.block_main, b.block_edge)
        self.bird.draw(self.screen, self.textures)
        self.particles.draw(self.screen)
        self.biome.draw_banner(self.screen)
        ui.draw_mute_icon(self.screen, self.sounds.muted)

        if self.state == GameState.PRONTO:
            ui.draw_ready_screen(self.screen, self.highscore)
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
