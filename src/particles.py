"""Sistema de particulas de bloco quebrando na colisao (R3.2)."""

import math
import random

import pygame

from src import render

GRAVITY = 0.35
MIN_LIFETIME = 20
MAX_LIFETIME = 40
MIN_SPEED = 2.0
MAX_SPEED = 6.0
MIN_SIZE = 4
MAX_SIZE = 8


class Particle:
    __slots__ = ("color", "lifetime", "pos", "rect", "size", "vel")
    """Sem `__dict__` por instancia: sao 16 por explosao, todas iguais em forma (R27.3)."""

    def __init__(
        self,
        pos: tuple[float, float],
        vel: tuple[float, float],
        lifetime: int,
        size: int,
        color: tuple[int, int, int],
    ) -> None:
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.lifetime = lifetime
        self.size = size
        self.color = color
        self.rect = pygame.Rect(0, 0, size, size)
        """Retangulo de desenho persistente, pelo mesmo motivo da hitbox da abelha:
        `draw` roda uma vez por particula por frame, e eram 16 `Rect` novos por frame
        na tela de GAME_OVER (R27.3)."""
        self._sync_rect()

    def update(self) -> None:
        self.vel.y += GRAVITY
        self.pos += self.vel
        self.lifetime -= 1
        self._sync_rect()

    def _sync_rect(self) -> None:
        self.rect.centerx = round(self.pos.x)
        self.rect.centery = round(self.pos.y)

    @property
    def alive(self) -> bool:
        return self.lifetime > 0

    def draw(self, renderer: render.Renderer) -> None:
        renderer.fill(self.color, self.rect)


class ParticleSystem:
    def __init__(self) -> None:
        self.particles: list[Particle] = []

    def burst(self, pos: tuple[float, float], texture: pygame.Surface, n: int = 16) -> None:
        """Amostra cores da textura do bloco atingido e dispara explosao radial (R3.2)."""
        w, h = texture.get_size()
        for _ in range(n):
            r, g, b = texture.get_at((random.randrange(w), random.randrange(h)))[:3]
            color = (r, g, b)

            angle = random.uniform(0, math.tau)
            speed = random.uniform(MIN_SPEED, MAX_SPEED)
            vel = (math.cos(angle) * speed, math.sin(angle) * speed)

            lifetime = random.randint(MIN_LIFETIME, MAX_LIFETIME)
            size = random.randint(MIN_SIZE, MAX_SIZE)
            self.particles.append(Particle(pos, vel, lifetime, size, color))

    def update(self) -> None:
        for particle in self.particles:
            particle.update()
        # remocao no lugar, como em `PipeManager.update`: sem particula em cena o laco
        # nao toca em nada, e a lista vazia sobrevive de frame a frame (R27.3).
        index = 0
        while index < len(self.particles):
            if self.particles[index].alive:
                index += 1
            else:
                del self.particles[index]

    def draw(self, renderer: render.Renderer) -> None:
        for particle in self.particles:
            particle.draw(renderer)
