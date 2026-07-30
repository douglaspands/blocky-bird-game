"""Classe Game: loop principal e maquina de estados (R6)."""

import contextlib
from enum import Enum, auto

import pygame

from src import assets, config, score, storage, textures, ui
from src.biome import BiomeManager
from src.bird import Bird
from src.config import BLOCK, CREDITS, FPS, PIPE_W, SCREEN_W, TITLE
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
from src.screen_adapt import adapted_canvas_size, portrait_height
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
        if storage.is_android():
            info = pygame.display.Info()
            device_w, device_h = info.current_w, info.current_h
        else:
            # Desktop nao tem "aparelho": o formato inicial e a propria base 2:3,
            # entao o calculo abaixo devolve exatamente 480x720 sem nenhuma mudanca
            # de comportamento (task 21). Redimensionar a janela na sessao continua
            # com o letterbox/pillarbox automatico do SCALED (nao recalculado ao
            # vivo — recriar o display em runtime crashou em teste real com esta
            # versao do SDL/pygame-ce, ver design.md secao 20.1.3).
            device_w, device_h = SCREEN_W, config.BASE_SCREEN_H
        is_landscape = device_w > 0 and device_h > 0 and device_w / device_h > SCREEN_W / config.BASE_SCREEN_H
        if is_landscape:
            # Aparelho em paisagem mais largo que a base (Android TV 16:9): o canvas
            # de FUNDO estica na largura para eliminar o pillarbox (R14.3) — o fundo
            # (biome/decor) se estende por esse canvas maior, area jogavel continua
            # fixa em 480x720 (calibracao da task 12 intocada). Tasks 35/38,
            # inalterado pela task 39.
            canvas_w, canvas_h = adapted_canvas_size(SCREEN_W, config.BASE_SCREEN_H, device_w, device_h)
            config.SCREEN_H = config.BASE_SCREEN_H
        else:
            # Aparelho em retrato (a maioria dos celulares): a area JOGAVEL de
            # verdade acompanha a proporcao real do aparelho — largura fixa em 480,
            # altura dinamica — eliminando o pillarbox sem estender fundo decorativo
            # nem cortar nada (R14.3 refinado, task 39). config.SCREEN_H passa a
            # valer para toda a sessao; ground/pipes/ui leem o valor dinamico.
            config.SCREEN_H = portrait_height(SCREEN_W, config.BASE_SCREEN_H, device_w, device_h)
            canvas_w, canvas_h = SCREEN_W, config.SCREEN_H
        # SCALED: SDL renderiza numa surface logica do tamanho do canvas e escala p/ a
        # janela/tela real mantendo a proporcao (letterbox/pillarbox automatico, R9.1).
        self.screen = pygame.display.set_mode((canvas_w, canvas_h), pygame.SCALED | pygame.RESIZABLE)
        # descarta eventos de janela gerados pela criacao do display (ex.: WindowShown,
        # WindowFocusGained/Lost) para nao serem lidos como acoes do jogador antes do
        # loop comecar — visto sob SDL_VIDEODRIVER=dummy com SDL 2.32 (pygame-ce).
        pygame.event.clear()
        pygame.display.set_caption(f"{TITLE} - {CREDITS}")
        # subsurface: area jogavel SCREEN_W x SCREEN_H, ancorada embaixo (o chao toca
        # a borda real da tela) e centralizada na largura. offset_y so fica > 0 no
        # caso paisagem (canvas_h == config.SCREEN_H em retrato, sempre). Todo
        # gameplay/UI continua desenhando em coordenadas locais 0..SCREEN_W/0..SCREEN_H
        # — so o fundo (biome/decor) desenha direto em self.screen (canvas inteiro).
        offset_x = (canvas_w - SCREEN_W) // 2
        offset_y = canvas_h - config.SCREEN_H
        self.gameplay = self.screen.subsurface((offset_x, offset_y, SCREEN_W, config.SCREEN_H))
        self.clock = pygame.time.Clock()
        self.running = True
        self.textures = textures.generate_all(BLOCK)
        self.sounds = SoundManager()
        self.input = InputManager(canvas_size=(canvas_w, canvas_h), offset=(offset_x, offset_y))
        self.score = 0
        self.highscore = score.load_highscore()
        self.reset()

    def reset(self) -> None:
        self.bird = Bird(SCREEN_W // 4, config.SCREEN_H // 2)
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
