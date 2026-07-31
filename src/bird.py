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


class Bird:
    def __init__(self, x: float, y: float) -> None:
        self.pos = pygame.Vector2(x, y)
        self.base_y = y
        self.vel_y = 0.0
        self.angle = 0.0
        self.frame = 0
        self.size = BLOCK
        self._frame_timer = 0
        self._idle_timer = 0

    def flap(self) -> None:
        self.vel_y = FLAP_IMPULSE
        self.angle = MAX_ANGLE_UP

    def update(self) -> None:
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

    def update_idle(self) -> None:
        """Flutuacao senoidal no estado PRONTO, sem gravidade (R6.1)."""
        self._idle_timer += 1
        self.pos.y = self.base_y + math.sin(self._idle_timer * IDLE_BOB_SPEED) * IDLE_BOB_AMPLITUDE
        self.angle = 0
        self._advance_wing_frame()

    def _advance_wing_frame(self) -> None:
        self._frame_timer += 1
        if self._frame_timer >= WING_FRAME_INTERVAL:
            self._frame_timer = 0
            self.frame = 1 - self.frame

    @property
    def rect(self) -> pygame.Rect:
        """Hitbox reduzida (~85% do sprite) centralizada (R3.5)."""
        full = pygame.Rect(round(self.pos.x), round(self.pos.y), self.size, self.size)
        hitbox_size = round(self.size * HITBOX_SCALE)
        rect = pygame.Rect(0, 0, hitbox_size, hitbox_size)
        rect.center = full.center
        return rect

    def draw(self, renderer: render.Renderer, textures: dict[str, pygame.Surface]) -> None:
        """Desenha o sprite rotacionado do angulo atual.

        A rotacao acontece uma vez por combinacao de (frame de asa, angulo) e a
        imagem fica guardada com o renderizador. Sao 62 combinacoes no total: o
        angulo so assume os valores da grade de `ANGLE_FALL_STEP` entre
        `MAX_ANGLE_DOWN` e `MAX_ANGLE_UP`, e ha dois frames de asa. A task 56
        pre-computa as 62 na inicializacao; aqui elas nascem sob demanda."""
        angle = round(self.angle)
        image = renderer.image(
            ("bee", self.frame, angle),
            lambda: pygame.transform.rotate(textures[f"bee_{self.frame}"], angle),
        )
        width, height = image.size
        center_x = self.pos.x + self.size / 2
        center_y = self.pos.y + self.size / 2
        renderer.draw(image, (round(center_x - width / 2), round(center_y - height / 2)))
