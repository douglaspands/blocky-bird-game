"""Classe Bird: fisica e animacao do passaro (R1)."""

import math

import pygame

from src import config, render
from src.config import BLOCK, FLAP_IMPULSE, GRAVITY, HITBOX_SCALE, MAX_FALL_SPEED

WING_FRAME_INTERVAL = 6
MAX_ANGLE_UP = 30
MAX_ANGLE_DOWN = -60
ANGLE_FALL_STEP = 3
IDLE_BOB_AMPLITUDE = 8
IDLE_BOB_SPEED = 0.08

WING_FRAMES = (0, 1)
ANGLES = tuple(range(MAX_ANGLE_DOWN, MAX_ANGLE_UP + 1, ANGLE_FALL_STEP))
"""Os 31 angulos que a abelha pode assumir, e a grade a que qualquer angulo e preso.

Nao e uma escolha de renderizacao: a fisica ja produzia so estes valores. `flap` fixa
o angulo em `MAX_ANGLE_UP` e a queda o decrementa de `ANGLE_FALL_STEP` em
`ANGLE_FALL_STEP` ate `MAX_ANGLE_DOWN`, entao o conjunto alcancavel e exatamente esta
progressao. Torna-la explicita e o que permite pre-computar as 31 x 2 = 62 texturas em
vez de descobri-las uma a uma durante o jogo (R27.2)."""


class Bird:
    """Fisica e animacao do passaro: gravidade, flap, rotacao e hitbox.

    Sem `__dict__` por instancia: e uma classe de dados pequena e estavel, o caso
    em que `__slots__` rende — menos memoria e acesso a atributo mais direto (R27.3).
    """

    __slots__ = ("_frame_timer", "_idle_timer", "angle", "base_y", "frame", "pos", "rect", "size", "vel_y")

    def __init__(self, x: float, y: float) -> None:
        """Cria o passaro na posicao `(x, y)`, parado, com hitbox sincronizada."""
        self.pos = pygame.Vector2(x, y)
        self.base_y = y
        self.vel_y = 0.0
        self.angle = 0.0
        self.frame = 0
        self.size = BLOCK
        self._frame_timer = 0
        self._idle_timer = 0
        hitbox_size = round(self.size * HITBOX_SCALE)
        self.rect = pygame.Rect(0, 0, hitbox_size, hitbox_size)
        """Hitbox reduzida (~85% do sprite) centralizada (R3.5).

        Atributo persistente, e nao `property`: `Game._collision_texture` a le uma vez
        por coluna, dentro do laco, e cada leitura construia dois `pygame.Rect` novos —
        dezenas de objetos descartaveis por frame para uma geometria que muda uma vez
        por passo de simulacao (R27.3). Quem mexe em `pos` fora de `update`/`update_idle`
        precisa chamar `sync_rect`."""
        self.sync_rect()

    def flap(self) -> None:
        """Aplica o impulso de subida e vira o sprite para cima."""
        self.vel_y = FLAP_IMPULSE
        self.angle = MAX_ANGLE_UP

    def update(self) -> None:
        """Avanca um passo de fisica: gravidade, posicao, rotacao e clamp no teto."""
        self.vel_y = min(self.vel_y + GRAVITY, MAX_FALL_SPEED)
        self.pos.y += self.vel_y

        # o teto fica na borda da AREA JOGAVEL, nao na do canvas: a faixa de ceu e
        # decorativa e nao pode dar espaco extra para voar (R24.5).
        ceiling = config.play().top
        if self.pos.y < ceiling:
            self.pos.y = ceiling
            self.vel_y = 0

        if self.vel_y < 0:
            self.angle = MAX_ANGLE_UP
        else:
            self.angle = max(MAX_ANGLE_DOWN, self.angle - ANGLE_FALL_STEP)

        self._advance_wing_frame()
        self.sync_rect()

    def update_idle(self) -> None:
        """Flutuacao senoidal no estado PRONTO, sem gravidade (R6.1)."""
        self._idle_timer += 1
        self.pos.y = self.base_y + math.sin(self._idle_timer * IDLE_BOB_SPEED) * IDLE_BOB_AMPLITUDE
        self.angle = 0
        self._advance_wing_frame()
        self.sync_rect()

    def _advance_wing_frame(self) -> None:
        self._frame_timer += 1
        if self._frame_timer >= WING_FRAME_INTERVAL:
            self._frame_timer = 0
            self.frame = 1 - self.frame

    def sync_rect(self) -> None:
        """Recentra a hitbox persistente na posicao atual.

        `centerx`/`centery` em vez de `center = (x, y)`: a forma com tupla constroi um
        objeto por chamada, e a chamada acontece uma vez por passo de simulacao.

        A conta e a mesma da `property` que existia aqui — `round(pos)` primeiro, meia
        largura depois — e nao `round(pos + size / 2)`: para um `size` impar as duas
        divergem, e a hitbox nao pode mudar de lugar por causa de uma otimizacao.
        """
        self.rect.centerx = round(self.pos.x) + self.size // 2
        self.rect.centery = round(self.pos.y) + self.size // 2

    def draw(self, renderer: render.Renderer, textures: dict[str, pygame.Surface]) -> None:
        """Consulta a textura do (frame de asa, angulo) atual e desenha (R27.2).

        Nao ha rotacao aqui: as 62 combinacoes ja foram rotacionadas por
        `precompute_sprites` na inicializacao, e `quantize` garante que a consulta
        sempre caia numa delas. `pygame.transform.rotate` aloca uma superficie nova a
        cada chamada e reamostra o sprite inteiro — barato uma vez, caro sessenta
        vezes por segundo (R27.3).
        """
        image = _sprite(renderer, textures, self.frame, quantize(self.angle))
        width, height = image.size
        center_x = self.pos.x + self.size / 2
        center_y = self.pos.y + self.size / 2
        renderer.draw(image, (round(center_x - width / 2), round(center_y - height / 2)))


def quantize(angle: float) -> int:
    """Angulo da grade de `ANGLES` mais proximo de `angle`.

    A fisica so produz angulos da grade, entao no jogo esta funcao devolve o proprio
    valor. Ela existe para que isso deixe de ser uma suposicao: sem ela, um angulo
    fora da grade — vindo de um estado restaurado, de um ajuste futuro no passo de
    queda ou de um teste — pediria uma textura que ninguem pre-computou, e a rotacao
    voltaria para dentro do frame, exatamente onde nao pode estar.
    """
    snapped = round(angle / ANGLE_FALL_STEP) * ANGLE_FALL_STEP
    return min(MAX_ANGLE_UP, max(MAX_ANGLE_DOWN, snapped))


def _sprite(
    renderer: render.Renderer, textures: dict[str, pygame.Surface], frame: int, angle: int
) -> render.Image:
    """Sprite rotacionado de um (frame de asa, angulo), construido uma vez."""
    return renderer.image(
        ("bee", frame, angle),
        lambda: pygame.transform.rotate(textures[f"bee_{frame}"], angle),
    )


def precompute_sprites(renderer: render.Renderer, textures: dict[str, pygame.Surface]) -> None:
    """Rotaciona as 62 combinacoes de (frame de asa, angulo) de uma vez (R27.2).

    Chamada na inicializacao e de novo apos um redimensionamento, que descarta o cache
    de imagens do renderizador. Sem ela as texturas nasceriam sob demanda — uma por
    frame durante a primeira queda, que e justamente o momento em que o jogador esta
    olhando o movimento.
    """
    for frame in WING_FRAMES:
        for angle in ANGLES:
            _sprite(renderer, textures, frame, angle)
