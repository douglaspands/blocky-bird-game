"""Classe Game: loop principal e maquina de estados (R6)."""

import contextlib
from enum import Enum, auto

import pygame

from src import assets, score, storage, textures, ui
from src.biome import BiomeManager
from src.bird import Bird
from src.config import BLOCK, CREDITS, FPS, PIPE_W, SCREEN_H, SCREEN_W, TITLE
from src.decor import DecorManager
from src.ground import Ground
from src.input import (
    ACTION_BACK,
    ACTION_FLAP,
    ACTION_FOCUS_LOST,
    ACTION_LEFT,
    ACTION_MUTE,
    ACTION_PAUSE,
    ACTION_RIGHT,
    InputManager,
)
from src.particles import ParticleSystem
from src.pipes import PipeManager
from src.screen_adapt import adapted_canvas_size
from src.sounds import SoundManager


class GameState(Enum):
    PRONTO = auto()
    JOGANDO = auto()
    PAUSADO = auto()
    GAME_OVER = auto()


class Game:
    def __init__(self) -> None:
        pygame.init()
        # icone da abelha na janela/taskbar do desktop (R21.2); sem efeito
        # visivel no Android (sem barra de titulo), mas nao ha custo em
        # tentar. Degradacao graciosa: um asset ausente/corrompido nunca
        # deve impedir o jogo de abrir (mesma disciplina do audio, R8.4).
        with contextlib.suppress(OSError, pygame.error):
            pygame.display.set_icon(pygame.image.load(str(assets.asset_path("app_icon_512.png"))))
        canvas_w, canvas_h = SCREEN_W, SCREEN_H
        if storage.is_android():
            # No Android o aparelho real quase sempre tem proporcao diferente da
            # base 480x720, sobrando letterbox/pillarbox preto. Em vez disso,
            # estica o canvas ate a proporcao do aparelho (R14.3) — a area
            # jogavel continua fixa em 480x720 (calibracao da task 12 intocada),
            # so o fundo (biome/decor) se estende pelo canvas inteiro. Ver
            # src/screen_adapt.py e specs/v2/design.md secao 20.
            info = pygame.display.Info()
            canvas_w, canvas_h = adapted_canvas_size(SCREEN_W, SCREEN_H, info.current_w, info.current_h)
        # SCALED: SDL renderiza numa surface logica do tamanho do canvas e escala p/ a
        # janela/tela real mantendo a proporcao (letterbox/pillarbox automatico, R9.1).
        self.screen = pygame.display.set_mode((canvas_w, canvas_h), pygame.SCALED | pygame.RESIZABLE)
        # descarta eventos de janela gerados pela criacao do display (ex.: WindowShown,
        # WindowFocusGained/Lost) para nao serem lidos como acoes do jogador antes do
        # loop comecar — visto sob SDL_VIDEODRIVER=dummy com SDL 2.32 (pygame-ce).
        pygame.event.clear()
        pygame.display.set_caption(f"{TITLE} - {CREDITS}")
        # subsurface: area jogavel 480x720, ancorada embaixo (o chao toca a borda real
        # da tela; o espaco extra vira ceu no topo) e centralizada na largura (sem eixo
        # preferencial quando o canvas estica horizontalmente, ex. Android TV). Todo
        # gameplay/UI continua desenhando em coordenadas locais 0..480/0..720 — so o
        # fundo (biome/decor) desenha direto em self.screen (canvas inteiro).
        offset_x = (canvas_w - SCREEN_W) // 2
        offset_y = canvas_h - SCREEN_H
        self.gameplay = self.screen.subsurface((offset_x, offset_y, SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()
        self.running = True
        self.textures = textures.generate_all(BLOCK)
        self.sounds = SoundManager()
        self.input = InputManager(canvas_size=(canvas_w, canvas_h), offset=(offset_x, offset_y))
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
        elif self.state == GameState.PAUSADO:
            # despausa sem flapar: garante que todo estado seja alcancavel so
            # com o botao central do D-pad/toque, mesmo sem tecla de pause
            # dedicada (ESC/P) ou botao Start de gamepad (R14.4, R15.5) — sem
            # isso, quem pausa via BACK (task 23) ficaria sem como voltar.
            self.state = GameState.JOGANDO
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
        if ACTION_FOCUS_LOST in actions and self.state == GameState.JOGANDO:
            # o app foi para segundo plano (ou perdeu foco no desktop): pausa e
            # nunca retoma sozinho, mesmo quando volta ao primeiro plano (R16.1,
            # R16.2) — so um flap/pause explicito do jogador despausa.
            self._toggle_pause()
        if ACTION_BACK in actions:
            self._back_action()
        if ACTION_FLAP in actions:
            self._flap_action()
        if ACTION_PAUSE in actions:
            self._toggle_pause()
        if ACTION_MUTE in actions:
            self.sounds.toggle_mute()
        if self.state == GameState.PAUSADO and (ACTION_LEFT in actions or ACTION_RIGHT in actions):
            # D-pad esquerda/direita alterna mudo em PAUSADO — unica forma de
            # mudar sem tecla M nem toque, para Android TV (R14.4, R15.4).
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
        # fundo (ceu + parallax) preenche o canvas inteiro (R14.3); gameplay/UI
        # desenham na subsurface 480x720, coordenadas locais inalteradas.
        self.biome.draw_background(self.screen)
        self.decor.draw(self.screen, b.decor)
        self.pipes.draw(self.gameplay, self.textures)
        self.ground.draw(self.gameplay, self.textures, b.block_main, b.block_edge)
        self.bird.draw(self.gameplay, self.textures)
        self.particles.draw(self.gameplay)
        self.biome.draw_banner(self.gameplay)
        ui.draw_mute_icon(self.gameplay, self.sounds.muted)

        if self.state == GameState.PRONTO:
            ui.draw_ready_screen(self.gameplay, self.highscore)
        elif self.state == GameState.JOGANDO:
            ui.draw_hud_score(self.gameplay, self.score)
        elif self.state == GameState.PAUSADO:
            ui.draw_hud_score(self.gameplay, self.score)
            ui.draw_paused_overlay(self.gameplay)
        elif self.state == GameState.GAME_OVER:
            ui.draw_game_over_screen(self.gameplay, self.score, self.highscore)

        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()
        pygame.quit()
