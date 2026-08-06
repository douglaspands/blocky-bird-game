"""Classe Game: loop principal e maquina de estados (R6)."""

import asyncio
import contextlib
from enum import Enum, auto

import pygame

from src import assets, config, mobs, perf, quality, render, score, sounds, textures, ui, viewport
from src.bands import SideBands
from src.biome import BiomeManager
from src.bird import Bird, precompute_sprites
from src.config import BLOCK, CORNER_TOLERANCE, CREDITS, FPS, PIPE_W, TITLE
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
    configure_event_filter,
)
from src.particles import ParticleSystem
from src.pipes import PipeManager
from src.storage import is_android

RESIZE_SETTLE_FRAMES = 12
"""Frames sem novo evento de redimensionamento antes de aplicar o novo canvas —
~200ms a 60 FPS, o bastante para o arrasto assentar sem parecer travado."""

STEP_MS = 1000 / FPS
"""Duracao de um passo de simulacao, em milissegundos (R28.1).

`update()` continua sendo exatamente o que era: um passo logico de 1/60 s, com as
mesmas constantes de fisica. O que mudou foi quem decide quantos deles rodam por
frame — o tempo real, e nao mais o desenho."""

MAX_FRAME_MS = 250.0
"""Teto do tempo real que um unico frame pode acumular (R28.3).

Uma pausa longa — o app em segundo plano, o sistema travando — devolveria um delta de
segundos, e sem este corte ele viraria uma rajada de passos que faria o jogo *pular*
para frente. R16.1 ja pausa o jogo ao ir para segundo plano; isto e a segunda linha de
defesa, para o que nao vem acompanhado de evento nenhum."""

MAX_STEPS = 5
"""Teto de passos de simulacao por frame (R28.2).

Impede a espiral da morte: se um passo passar a custar mais que `STEP_MS`, cada frame
pediria mais passos do que consegue rodar, e a divida cresceria sem fim ate o jogo
parar de responder. Chegando ao teto, o atraso restante e descartado — perde-se tempo
de jogo, que e o preco de continuar respondendo."""


def _load_icon() -> pygame.Surface | None:
    """Icone da abelha para a janela/taskbar do desktop (R21.2).

    Sem efeito visivel no Android (sem barra de titulo), mas nao ha custo em tentar.
    Degradacao graciosa: um asset ausente ou corrompido nunca deve impedir o jogo de
    abrir (mesma disciplina do audio, R8.4).
    """
    with contextlib.suppress(OSError, pygame.error):
        return pygame.image.load(str(assets.asset_path("app_icon_512.png")))
    return None


def _collides(a: pygame.Rect, b: pygame.Rect) -> bool:
    """Colisao AABB que perdoa um resvalar raso de canto (R3.6, `config.CORNER_TOLERANCE`).

    So aritmetica sobre os quatro limites de cada retangulo — nenhum `pygame.Rect` novo
    e construido aqui (R27.3, `tests/test_alloc.py::test_the_collision_check_builds_no_rectangle_at_all`).
    """
    overlap_x = min(a.right, b.right) - max(a.left, b.left)
    overlap_y = min(a.bottom, b.bottom) - max(a.top, b.top)
    return overlap_x >= CORNER_TOLERANCE and overlap_y >= CORNER_TOLERANCE


class GameState(Enum):
    """Os quatro estados da maquina de estados do jogo (R6)."""

    PRONTO = auto()
    JOGANDO = auto()
    PAUSADO = auto()
    GAME_OVER = auto()


class Game:
    """Orquestra estado, entrada, atualizacao e desenho do jogo inteiro."""

    def __init__(self) -> None:
        """Inicializa pygame, janela, renderer e todos os subsistemas do jogo."""
        # antes do init: o SDL le o hint de orientacao ao criar o subsistema de video,
        # e o `pygame.init()` ja sobe o mixer com os parametros que `pre_init` deixou —
        # e uma vez so, em vez das duas da v2 (R27.6, design secao 40).
        viewport.lock_portrait_orientation()
        sounds.pre_init()
        pygame.init()
        # logo apos o init, antes de qualquer evento existir: o que o jogo nao consome
        # nao chega nem a virar objeto Python (R27.6).
        configure_event_filter()
        # O canvas logico recebe a proporcao REAL da tela (Android) ou da janela
        # (desktop), com a area jogavel de 480x720 posicionada dentro dele — o que
        # sobra vira faixa decorativa, nunca barra preta (R23.1, R23.4). Como a
        # proporcao bate, a escala do SDL e uniforme e preenche a tela inteira sem
        # cortar nada (R23.2). O viewport vai para o `config` porque todo o jogo o
        # consulta para se posicionar.
        self.viewport = viewport.compute(*viewport.screen_size())
        config.set_viewport(self.viewport)
        self.renderer = render.create(
            self.viewport.canvas,
            viewport.screen_size(),
            fullscreen=is_android(),
            title=f"{TITLE} - {CREDITS}",
            icon=_load_icon(),
        )
        # descarta eventos de janela gerados pela criacao do display (ex.: WindowShown,
        # WindowFocusGained/Lost) para nao serem lidos como acoes do jogador antes do
        # loop comecar — visto sob SDL_VIDEODRIVER=dummy com SDL 2.32 (pygame-ce).
        pygame.event.clear()
        self._pending_resize: tuple[int, int] | None = None
        self._resize_idle = 0
        self.clock = pygame.time.Clock()
        self.accumulator = 0.0
        """Tempo real ja decorrido e ainda nao simulado, em milissegundos (R28.1).

        E o que faz o resto de um frame nao ser jogado fora: a 60 FPS o relogio do
        pygame devolve inteiros alternando entre 16 e 17 ms, e descartar a diferenca
        para `STEP_MS` (16,67) faria o jogo correr devagar num aparelho que nao perdeu
        um quadro sequer."""
        self.running = True
        self.textures = textures.generate_all(BLOCK)
        # as 62 rotacoes da abelha e os 18 sprites de mob entram no cache do
        # renderizador antes do primeiro frame, para que nenhum deles seja construido
        # durante o jogo (R27.2).
        precompute_sprites(self.renderer, self.textures)
        mobs.precompute(self.renderer)
        # cache de superficie por bioma, independente de partida: sobrevive ao reset()
        self.bands = SideBands()
        self.sounds = sounds.SoundManager()
        self.input = InputManager(self.renderer)
        self.score = 0
        self.last_score: int | None = None
        """Pontuacao da partida anterior nesta execucao, so em memoria (R36.3). `None`
        ate a primeira transicao GAME_OVER -> PRONTO; nunca gravado em disco."""
        self.highscore = score.load_highscore()
        self._highscore_dirty = False
        """Recorde superado e ainda nao gravado (R27.5). Ver `_flush_highscore`."""
        # o nivel detectado na sessao anterior volta ja aplicado: os primeiros segundos
        # ruins de um aparelho fraco acontecem uma vez, e nao toda vez (R29.5).
        self.quality = quality.Quality(quality.load_level())
        # None em producao: a instrumentacao so existe com BLOCKY_PERF ligado (R30.2),
        # entao o custo normal e uma comparacao contra None por frame.
        self.profiler = perf.FrameProfiler() if perf.enabled() else None
        if self.profiler is not None:
            self.profiler.backend = self.renderer.backend  # R26.5
        self.reset()
        # por ultimo: tudo que o jogo constroi uma vez ja existe, e e exatamente isso
        # que sai da varredura do coletor daqui em diante (R27.3).
        perf.tune_gc()

    def apply_resize(self, size: tuple[int, int]) -> None:
        """Recalcula o canvas e as faixas para uma janela `size` (R23.6).

        A area jogavel nao muda: continua sendo a mesma coluna de 480x720 de mundo,
        so o canvas ao redor e elastico (R24.1).

        Com a camada de render no lugar, trocar o canvas e uma chamada: o
        `display.quit()/init()` que a task 48 precisava para contornar o `SCALED`
        desapareceu junto com o `SCALED`. As imagens chaveadas pelo tamanho do canvas
        (gradiente de ceu, faixas laterais) sao descartadas para nao ficarem ocupando
        memoria de video sem nunca mais serem pedidas.

        `forget_images` nao sabe distinguir o que depende do canvas do que nao depende,
        entao as 62 rotacoes da abelha e os 18 sprites de mob caem junto e sao refeitos
        aqui — fora do frame, como na inicializacao.
        """
        new_viewport = viewport.compute(*size)
        if new_viewport.canvas == self.viewport.canvas:
            return
        self.viewport = new_viewport
        config.set_viewport(new_viewport)
        self.renderer.forget_images()
        self.renderer.resize(new_viewport.canvas)
        precompute_sprites(self.renderer, self.textures)
        mobs.precompute(self.renderer)
        # os retangulos de colisao viraram persistentes na task 58, e dois deles
        # dependem da linha do chao — que acabou de mudar de lugar. Sem isto, os frames
        # entre o redimensionamento e o proximo passo de simulacao (PRONTO, PAUSADO,
        # GAME_OVER nao simulam) desenhariam a coluna com a altura do canvas antigo.
        self.pipes.sync_rects()
        self.ground.sync_rect()

    def _tick_resize(self) -> None:
        """Aplica o redimensionamento pendente quando o arrasto para.

        Sem esperar o arrasto assentar, cada pixel de uma janela sendo arrastada
        recriaria o display — dezenas de vezes por segundo.
        """
        if self._pending_resize is None:
            return
        self._resize_idle += 1
        if self._resize_idle >= RESIZE_SETTLE_FRAMES:
            size, self._pending_resize = self._pending_resize, None
            self.apply_resize(size)

    def reset(self) -> None:
        """Recria todo o estado de uma partida nova (passaro, biomas, colunas, score)."""
        play = config.play()
        self.bird = Bird(play.x + play.width // 4, play.y + play.height // 2)
        self.biome = BiomeManager()
        b = self.biome.current
        self.pipes = PipeManager(b.gap_size, b.block_main, b.block_edge)
        self.ground = Ground()
        self.decor = DecorManager()
        self.mobs = mobs.MobField()
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
            self.last_score = self.score
            self.reset()

    def _toggle_pause(self) -> None:
        if self.state == GameState.JOGANDO:
            self.state = GameState.PAUSADO
        elif self.state == GameState.PAUSADO:
            self.state = GameState.JOGANDO

    def _back_action(self) -> None:
        """BACK do Android pausa em JOGANDO; nos demais estados, encerra o jogo.

        (R15.2, R15.3). Fica no Game (que conhece o estado), nao no
        InputManager, mantendo a separacao acao/estado da v1.
        """
        if self.state == GameState.JOGANDO:
            self._toggle_pause()
        else:
            self.running = False

    def handle_events(self) -> None:
        """Coleta as acoes de entrada do quadro e as aplica ao estado do jogo."""
        actions, quit_requested = self.input.poll()
        if quit_requested:
            self.running = False
        if ACTION_RESIZE in actions:
            self._pending_resize = self.renderer.window_size
            self._resize_idle = 0
        self._tick_resize()
        if ACTION_FOCUS_LOST in actions:
            # ultimo instante garantido antes de o Android poder encerrar o app: e onde
            # o recorde da partida em curso vai para o disco (R27.5, R16.4). Fora do
            # `if` de estado de proposito — o recorde pode estar sujo em GAME_OVER que
            # falhou em gravar, e gravar de novo custa nada quando nao ha nada sujo.
            self._flush_to_disk()
            if self.state == GameState.JOGANDO:
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
        """Retorna a chave da textura do bloco atingido, ou None se nao houve colisao (R3.2, R3.6)."""
        if _collides(self.bird.rect, self.ground.rect):
            return self.biome.current.block_main
        for pipe in self.pipes.pipes:
            if _collides(self.bird.rect, pipe.top_rect) or _collides(self.bird.rect, pipe.bottom_rect):
                return pipe.block_main
        return None

    def _update_score(self) -> None:
        """+1 por coluna ultrapassada, uma unica vez por coluna (R4.1).

        Superar o recorde marca-o como sujo em vez de gravar em disco: escrita de
        arquivo dentro do frame de JOGANDO e uma chamada de sistema sincrona, com uma
        cauda de latencia que nao depende do jogo (R27.5). Quem grava e
        `_flush_highscore`.
        """
        for pipe in self.pipes.pipes:
            if not pipe.scored and pipe.x + PIPE_W < self.bird.pos.x:
                pipe.scored = True
                self.score += 1
                self.sounds.play("score")
                if self.score > self.highscore:
                    self.highscore = self.score
                    self._highscore_dirty = True

    def _flush_highscore(self) -> None:
        """Grava o recorde em disco, se houver um novo desde a ultima gravacao (R27.5).

        Chamado nos tres momentos em que o frame nao esta em jogo: o fim da partida, a
        ida para segundo plano e o encerramento do laco. A garantia que motivou a
        gravacao incremental da v2 continua de pe (R4.3, R16.4) porque o Android *avisa*
        antes de encerrar — `APP_WILLENTERBACKGROUND` chega primeiro, e e nele que a
        gravacao passa a acontecer. O que se perde e o caso de o processo morrer sem
        nenhum aviso, que nem a v2 cobria.
        """
        if self._highscore_dirty:
            score.save_highscore(self.highscore)
            self._highscore_dirty = False

    def _flush_quality(self) -> None:
        """Grava o nivel de qualidade detectado, se ele mudou (R29.5).

        Sai do frame pelo mesmo motivo do recorde: a troca de nivel acontece justamente
        no aparelho que ja esta com dificuldade, e escrever em disco ali seria uma
        chamada de sistema sincrona no pior momento possivel (R27.5).
        """
        if self.quality.dirty:
            quality.save_level(self.quality.level)
            self.quality.dirty = False

    def _flush_to_disk(self) -> None:
        """Descarrega tudo que esta pendente de gravacao.

        Os dois arquivos sao gravados nos mesmos tres momentos — fim de partida, ida
        para segundo plano e saida do laco — porque a razao e a mesma: sao os unicos
        instantes em que ninguem esta jogando.
        """
        self._flush_highscore()
        self._flush_quality()

    def update(self) -> None:
        """Avanca um passo fixo de simulacao conforme o estado atual do jogo."""
        if self.state == GameState.PRONTO:
            self.bird.update_idle()
            # sem deriva, so o idle: o cenario respira na tela inicial sem sair do lugar
            self.mobs.update(0.0)
        elif self.state == GameState.JOGANDO:
            b = self.biome.current
            self.bird.update()
            self.pipes.update(b.speed, b.gap_size, b.block_main, b.block_edge)
            self.ground.update(b.speed)
            self.decor.update(b.speed)
            self.mobs.update(b.speed)
            self._update_score()
            if self.biome.update(self.score):
                self.sounds.play("portal")
            hit_texture = self._collision_texture()
            if hit_texture is not None:
                self.state = GameState.GAME_OVER
                self.particles.burst(
                    self.bird.rect.center, self.textures[hit_texture], self.quality.settings.particles
                )
                self.sounds.play("hit")
                # fim da partida: e aqui que o recorde da rodada vai para o disco (R27.5)
                self._flush_to_disk()
        # PAUSADO: fisica, obstaculos, biomas e particulas ficam congelados (R3.3, R6.3).
        if self.state != GameState.PAUSADO:
            self.particles.update()

    def draw(self) -> None:
        """Desenha um quadro completo: fundo, decoracao, jogo e UI do estado atual."""
        b = self.biome.current
        renderer = self.renderer
        # o que cai fora nos niveis mais baixos e sempre decoracao — nunca coluna,
        # chao, abelha ou HUD, que sao o jogo (R29.2, R29.3).
        level = self.quality.settings
        self.biome.draw_background(renderer)
        self.decor.draw(renderer, b.decor, far=level.far_parallax, near=level.near_parallax)
        self.pipes.draw(renderer, self.textures)
        self.ground.draw(renderer, self.textures, b.block_main, b.block_edge)
        # depois do chao: o mob vive sobre a terra estendida, nao antes dela.
        if level.mobs:
            self.mobs.draw_ground(renderer, b.id)
        self.bird.draw(renderer, self.textures)
        self.particles.draw(renderer)
        # depois das colunas e da abelha, antes do HUD: a faixa e opaca e esconde a
        # coluna que ainda nao entrou na area jogavel (R24.4, seção 32.6).
        self.bands.draw(renderer, self.textures, b)
        # depois das faixas, que sao opacas: o mob vive NA parede, nao atras dela.
        if level.mobs:
            self.mobs.draw_sides(renderer, b.id)
        self.biome.draw_banner(renderer)
        ui.draw_mute_icon(renderer, self.sounds.muted)

        if self.state == GameState.PRONTO:
            ui.draw_ready_screen(renderer, self.highscore, self.last_score)
        elif self.state == GameState.JOGANDO:
            ui.draw_hud_score(renderer, self.score)
        elif self.state == GameState.PAUSADO:
            ui.draw_hud_score(renderer, self.score)
            ui.draw_paused_overlay(renderer)
        elif self.state == GameState.GAME_OVER:
            ui.draw_game_over_screen(renderer, self.score, self.highscore)

        if self.profiler is not None:
            perf.draw_overlay(renderer, self.profiler)

        renderer.present()

    def simulate(self, frame_ms: float) -> int:
        """Roda os passos fixos que `frame_ms` de tempo real comprou (R28.1-R28.3).

        Devolve quantos rodaram. A conta e a mesma de qualquer acumulador: o tempo
        decorrido entra, os passos inteiros saem, e o resto fica para o frame seguinte.
        Tres detalhes e que sao o requisito:

        - o delta e **cortado antes** de virar passos (R28.3), entao uma pausa de dois
          segundos vira 250 ms de jogo e nao dois segundos de avanco instantaneo;
        - o numero de passos tem teto (R28.2), entao um aparelho onde o passo custa
          mais que 1/60 s desiste de recuperar em vez de afundar;
        - batido o teto, o acumulador **zera**. Sem isso a divida ficaria guardada e o
          frame seguinte comecaria ja devendo, o que e a mesma espiral, so que mais
          lenta.

        O que nao muda e o principal: `update()` continua sendo um passo de 1/60 s. A
        60 FPS este laco roda exatamente um por frame, e o jogo e o mesmo da v2 ate no
        pixel (R28.4).
        """
        self.accumulator += min(frame_ms, MAX_FRAME_MS)
        steps = 0
        while self.accumulator >= STEP_MS and steps < MAX_STEPS:
            self.update()
            self.accumulator -= STEP_MS
            steps += 1
        if steps == MAX_STEPS:
            self.accumulator = 0.0
        return steps

    async def run(self) -> None:
        """Laco principal: relogio, simulacao em passos fixos e desenho, ate fechar.

        `await asyncio.sleep(0)` devolve o controle ao navegador a cada quadro (R37.2)
        - sob Emscripten/pygbag e o unico jeito de a aba nao travar; em CPython nativo
        o mesmo await custa uma cessao de controle sem I/O real, entao o MESMO laco
        roda sem ramo de plataforma no desktop/Android (R37.3).
        """
        profiler = self.profiler
        while self.running:
            # o teto de quadros vem do nivel de qualidade: cai para 30 no BAIXO, e a
            # simulacao continua a 60 passos logicos por segundo (R29.2, seção 38).
            frame_ms = self.clock.tick(self.quality.render_fps)
            # so JOGANDO alimenta a medicao: as telas paradas desenham outra coisa e
            # nao dizem nada sobre o desempenho da partida (R29.1).
            self.quality.frame(frame_ms, self.state == GameState.JOGANDO)
            self.handle_events()
            if profiler is None:
                self.simulate(frame_ms)
                self.draw()
            else:
                profiler.frame(frame_ms)
                profiler.begin()
                self.simulate(frame_ms)
                profiler.end_update()
                self.draw()
                profiler.end_draw()
            await asyncio.sleep(0)
        # saida ordenada (fechar a janela, BACK fora de JOGANDO): um recorde batido numa
        # partida que o jogador abandonou sem colidir nao pode se perder aqui (R4.3).
        self._flush_to_disk()
        pygame.quit()
