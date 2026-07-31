"""Classe Game: loop principal e maquina de estados (R6)."""

import contextlib
from enum import Enum, auto

import pygame

from src import assets, config, perf, score, textures, ui, viewport
from src.bands import SideBands
from src.biome import BiomeManager
from src.bird import Bird
from src.config import BLOCK, CREDITS, FPS, PIPE_W, TITLE
from src.decor import DecorManager
from src.ground import Ground
from src.input import (
    ACTION_BACK,
    ACTION_FLAP,
    ACTION_FOCUS_LOST,
    ACTION_LEFT,
    ACTION_MUTE,
    ACTION_PAUSE,
    ACTION_RESIZE,
    ACTION_RIGHT,
    InputManager,
)
from src.particles import ParticleSystem
from src.pipes import PipeManager
from src.sounds import SoundManager

RESIZE_SETTLE_FRAMES = 12
"""Frames sem novo evento de redimensionamento antes de aplicar o novo canvas —
~200ms a 60 FPS, o bastante para o arrasto assentar sem parecer travado."""


class GameState(Enum):
    PRONTO = auto()
    JOGANDO = auto()
    PAUSADO = auto()
    GAME_OVER = auto()


class Game:
    def __init__(self) -> None:
        # antes do init: o SDL le o hint de orientacao ao criar o subsistema de video
        viewport.lock_portrait_orientation()
        pygame.init()
        # O canvas logico recebe a proporcao REAL da tela (Android) ou da janela
        # (desktop), com a area jogavel de 480x720 posicionada dentro dele — o que
        # sobra vira faixa decorativa, nunca barra preta (R23.1, R23.4). Como a
        # proporcao bate, a escala do SDL e uniforme e preenche a tela inteira sem
        # cortar nada (R23.2). O viewport vai para o `config` porque todo o jogo o
        # consulta para se posicionar.
        self.viewport = viewport.compute(*viewport.screen_size())
        config.set_viewport(self.viewport)
        self._open_display()
        self._pending_resize: tuple[int, int] | None = None
        self._resize_idle = 0
        self.clock = pygame.time.Clock()
        self.running = True
        self.textures = textures.generate_all(BLOCK)
        # cache de superficie por bioma, independente de partida: sobrevive ao reset()
        self.bands = SideBands()
        self.sounds = SoundManager()
        self.input = InputManager()
        self.score = 0
        self.highscore = score.load_highscore()
        # None em producao: a instrumentacao so existe com BLOCKY_PERF ligado (R30.2),
        # entao o custo normal e uma comparacao contra None por frame.
        self.profiler = perf.FrameProfiler() if perf.enabled() else None
        self.reset()

    def _open_display(self) -> None:
        """Cria (ou recria) o display para o viewport ativo."""
        # icone da abelha na janela/taskbar do desktop (R21.2); sem efeito
        # visivel no Android (sem barra de titulo), mas nao ha custo em
        # tentar. Degradacao graciosa: um asset ausente/corrompido nunca
        # deve impedir o jogo de abrir (mesma disciplina do audio, R8.4).
        with contextlib.suppress(OSError, pygame.error):
            pygame.display.set_icon(pygame.image.load(str(assets.asset_path("app_icon_512.png"))))
        self.screen = pygame.display.set_mode(self.viewport.canvas, viewport.display_flags())
        pygame.display.set_caption(f"{TITLE} - {CREDITS}")
        # descarta eventos de janela gerados pela criacao do display (ex.: WindowShown,
        # WindowFocusGained/Lost) para nao serem lidos como acoes do jogador antes do
        # loop comecar — visto sob SDL_VIDEODRIVER=dummy com SDL 2.32 (pygame-ce).
        pygame.event.clear()

    def apply_resize(self, size: tuple[int, int]) -> None:
        """Recalcula o canvas e as faixas para uma janela `size` (R23.6).

        A area jogavel nao muda: continua sendo a mesma coluna de 480x720 de mundo,
        so o canvas ao redor e elastico (R24.1). Os caches de faixa e de gradiente se
        invalidam sozinhos, porque sao chaveados pelo tamanho do canvas.

        Trocar o canvas logico do `SCALED` exige recriar o display, e recriar sem o
        `display.quit()/init()` aborta o processo no pygame-ce 2.5.7 — medido tanto
        no driver do Windows quanto no `dummy`. Quando a camada de render entrar
        (task 49), isto vira `renderer.logical_size = viewport.canvas` e todo o
        rodeio desaparece."""
        new_viewport = viewport.compute(*size)
        if new_viewport.canvas == self.viewport.canvas:
            return
        self.viewport = new_viewport
        config.set_viewport(new_viewport)
        pygame.display.quit()
        pygame.display.init()
        self._open_display()
        viewport.restore_window_size(size)

    def _tick_resize(self) -> None:
        """Aplica o redimensionamento pendente quando o arrasto para.

        Sem esperar o arrasto assentar, cada pixel de uma janela sendo arrastada
        recriaria o display — dezenas de vezes por segundo."""
        if self._pending_resize is None:
            return
        self._resize_idle += 1
        if self._resize_idle >= RESIZE_SETTLE_FRAMES:
            size, self._pending_resize = self._pending_resize, None
            self.apply_resize(size)

    def reset(self) -> None:
        play = config.play()
        self.bird = Bird(play.x + play.width // 4, play.y + play.height // 2)
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
        if ACTION_RESIZE in actions:
            self._pending_resize = pygame.display.get_window_size()
            self._resize_idle = 0
        self._tick_resize()
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
        self.biome.draw_background(self.screen)
        self.decor.draw(self.screen, b.decor)
        self.pipes.draw(self.screen, self.textures)
        self.ground.draw(self.screen, self.textures, b.block_main, b.block_edge)
        self.bird.draw(self.screen, self.textures)
        self.particles.draw(self.screen)
        # depois das colunas e da abelha, antes do HUD: a faixa e opaca e esconde a
        # coluna que ainda nao entrou na area jogavel (R24.4, seção 32.6).
        self.bands.draw(self.screen, self.textures, b)
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

        if self.profiler is not None:
            perf.draw_overlay(self.screen, self.profiler)

        pygame.display.flip()

    def run(self) -> None:
        profiler = self.profiler
        while self.running:
            frame_ms = self.clock.tick(FPS)
            self.handle_events()
            if profiler is None:
                self.update()
                self.draw()
            else:
                profiler.frame(frame_ms)
                profiler.begin()
                self.update()
                profiler.end_update()
                self.draw()
                profiler.end_draw()
        pygame.quit()
