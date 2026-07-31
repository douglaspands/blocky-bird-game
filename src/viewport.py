"""Canvas logico e area jogavel: como o jogo preenche telas de qualquer proporcao (R23, R24).

Duas grandezas passam a ser distintas, e essa distincao e o coracao da v3:

- **Area jogavel** — sempre 480x720 de mundo. E onde a abelha voa, onde as colunas
  existem e onde a colisao acontece. Nenhuma constante de fisica ou de bioma depende
  da tela, entao o desafio e identico no celular e no PC e os recordes continuam
  comparaveis (R24.1, R24.2).
- **Canvas logico** — tem a proporcao real da tela (Android) ou da janela (desktop).
  Contem a area jogavel e, ao redor dela, as faixas decorativas (R25).

Por construcao so um dos dois eixos sobra: o canvas recebe exatamente a proporcao da
tela, entao a escala final e uniforme e preenche tudo — nenhuma barra preta e nenhum
corte (R23.1, R23.2, R23.4).

Ver specs/v3/design.md secao 32.
"""

import os
from dataclasses import dataclass

import pygame

from src.config import BLOCK
from src.storage import is_android

PLAY_W = 480
PLAY_H = 720
"""Area jogavel em coordenadas de mundo. Imutavel: e a calibracao de dificuldade da
v1 (task 12), que a v3 se compromete a nao mexer (R24.1)."""

MAX_GROUND_EXTRA = 2 * BLOCK
"""Teto do que a sobra vertical pode virar de chao: ate 2 fileiras de bloco.

O limite existe para que uma tela muito alongada nao vire uma tira fina de jogo sobre
um bloco de terra gigante; o que passa disso vai para o ceu, que absorve altura sem
parecer estranho. O valor foi escolhido por inspecao visual, nao por analise."""

DESKTOP_WINDOW = (960, 720)
"""Janela padrao do desktop: mais larga que a area jogavel, para as faixas laterais
aparecerem sem o jogador precisar redimensionar nada (R23.7) e para a conferencia
visual no PC ser representativa do celular."""

ENV_CANVAS = "BLOCKY_CANVAS"
"""`BLOCKY_CANVAS=LxA` forca o canvas, para conferir a proporcao de um celular sem
aparelho. Ferramenta de desenvolvimento, no mesmo espirito de `BLOCKY_PERF`."""

ENV_ORIENTATION = "SDL_IOS_ORIENTATIONS"
"""Nome de ambiente do hint `SDL_HINT_ORIENTATIONS` do SDL2.

O prefixo `IOS` e historico: a documentacao do proprio SDL descreve o hint como
"which orientations are allowed on iOS/Android". Escrever `SDL_HINT_ORIENTATIONS`
no ambiente nao teria efeito nenhum — esse e o nome da macro em C, e `SDL_GetHint`
procura pela string para a qual ela aponta, que e esta."""


@dataclass(frozen=True)
class Viewport:
    """Canvas logico com a area jogavel posicionada dentro dele.

    As faixas sao derivadas, nao armazenadas: `sky_band` e `ground_band` cobrem a
    largura toda do canvas e `left_band`/`right_band` a altura toda, porque ceu,
    parallax e chao sao desenhados de borda a borda e as faixas laterais os cobrem
    depois (R25.5, design secao 32.6).
    """

    canvas: tuple[int, int]
    play: pygame.Rect
    sky_extra: int
    ground_extra: int

    @property
    def width(self) -> int:
        """Largura do canvas logico."""
        return self.canvas[0]

    @property
    def height(self) -> int:
        """Altura do canvas logico."""
        return self.canvas[1]

    @property
    def sky_band(self) -> pygame.Rect:
        """Faixa de ceu estendido acima da area jogavel (R25.1). Vazia numa tela 2:3."""
        return pygame.Rect(0, 0, self.width, self.sky_extra)

    @property
    def ground_band(self) -> pygame.Rect:
        """Fileiras extras de chao abaixo da area jogavel (R25.1). Vazia numa tela 2:3."""
        return pygame.Rect(0, self.play.bottom, self.width, self.ground_extra)

    @property
    def left_band(self) -> pygame.Rect:
        """Corte transversal do subsolo a esquerda (R25.2). Vazia numa tela 2:3."""
        return pygame.Rect(0, 0, self.play.left, self.height)

    @property
    def right_band(self) -> pygame.Rect:
        """Corte transversal do subsolo a direita (R25.2). Vazia numa tela 2:3.

        Calculada a partir de `play.right`, e nao como espelho de `left_band`, para
        absorver o pixel impar quando `canvas_w - PLAY_W` e impar."""
        return pygame.Rect(self.play.right, 0, self.width - self.play.right, self.height)


def compute(screen_w: int, screen_h: int) -> Viewport:
    """Deriva o canvas logico e a area jogavel de um tamanho real de tela ou janela.

    O canvas recebe a proporcao da tela e cresce a partir da area jogavel, nunca
    encolhendo abaixo dela. A sobra vertical vira chao (ate `MAX_GROUND_EXTRA`) e o
    resto vira ceu; a sobra horizontal vira faixa lateral, com a area jogavel
    centralizada. Tamanho invalido devolve o canvas 2:3, na mesma disciplina de
    `scale.fit_scale` — nunca deveria ocorrer com uma tela real, e um numero
    estranho jamais deve impedir o jogo de abrir.
    """
    if screen_w <= 0 or screen_h <= 0:
        screen_w, screen_h = PLAY_W, PLAY_H

    if screen_w * PLAY_H < screen_h * PLAY_W:  # tela mais alongada que 2:3 (celular em retrato)
        canvas_w = PLAY_W
        canvas_h = round(PLAY_W * screen_h / screen_w)
    else:  # tela mais larga que 2:3 (monitor, janela padrao do desktop)
        canvas_h = PLAY_H
        canvas_w = round(PLAY_H * screen_w / screen_h)
    canvas_w = max(canvas_w, PLAY_W)
    canvas_h = max(canvas_h, PLAY_H)

    leftover_v = canvas_h - PLAY_H
    ground_extra = min(leftover_v, MAX_GROUND_EXTRA)
    sky_extra = leftover_v - ground_extra

    play = pygame.Rect((canvas_w - PLAY_W) // 2, sky_extra, PLAY_W, PLAY_H)
    return Viewport(canvas=(canvas_w, canvas_h), play=play, sky_extra=sky_extra, ground_extra=ground_extra)


def forced_size() -> tuple[int, int] | None:
    """Le `BLOCKY_CANVAS=LxA`, ou None se ausente ou mal formada.

    Como `compute` e idempotente sobre a propria saida, forcar o tamanho de tela
    equivale a forcar o canvas. Valor invalido e ignorado em silencio: e ferramenta
    de desenvolvimento e nunca deve impedir o jogo de abrir."""
    raw = os.environ.get(ENV_CANVAS, "").lower()
    parts = raw.split("x")
    if len(parts) != 2:
        return None
    try:
        width, height = int(parts[0]), int(parts[1])
    except ValueError:
        return None
    if width <= 0 or height <= 0:
        return None
    return width, height


def screen_size() -> tuple[int, int]:
    """Tamanho real de tela/janela que alimenta `compute`.

    No Android e a resolucao nativa do aparelho, que e o que faz a tela cheia
    preencher os quatro lados (R23.3); no desktop e a janela padrao mais larga que a
    area jogavel (R23.7). `BLOCKY_CANVAS` tem precedencia sobre os dois."""
    forced = forced_size()
    if forced is not None:
        return forced
    if is_android():
        try:
            sizes = pygame.display.get_desktop_sizes()
        except pygame.error:  # display ainda nao inicializado
            sizes = []
        if sizes:
            return sizes[0]
    return DESKTOP_WINDOW


def lock_portrait_orientation() -> None:
    """Trava a orientacao em retrato pelo lado do SDL. Chamar ANTES de `pygame.init()`.

    Reforca o `orientation = portrait` que o `buildozer.spec` ja declara: o manifesto
    convence o Android, este hint convence o SDL, e o jogo nunca gira quando o
    aparelho e virado (R23.5). Nao sobrescreve um valor ja definido no ambiente, para
    continuar sendo possivel investigar paisagem sem editar codigo."""
    os.environ.setdefault(ENV_ORIENTATION, "Portrait")
