"""Sistema de particulas de bloco quebrando na colisao (R3.2)."""

import math
import random

import pygame

GRAVITY = 0.35
MIN_LIFETIME = 20
MAX_LIFETIME = 40
MIN_SPEED = 2.0
MAX_SPEED = 6.0
MIN_SIZE = 4
MAX_SIZE = 8


class Particle:
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

    def update(self) -> None:
        self.vel.y += GRAVITY
        self.pos += self.vel
        self.lifetime -= 1

    @property
    def alive(self) -> bool:
        return self.lifetime > 0

    def draw(self, surface: pygame.Surface) -> None:
        rect = pygame.Rect(0, 0, self.size, self.size)
        rect.center = (round(self.pos.x), round(self.pos.y))
        pygame.draw.rect(surface, self.color, rect)


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
        self.particles = [p for p in self.particles if p.alive]

    def draw(self, surface: pygame.Surface) -> None:
        for particle in self.particles:
            particle.draw(surface)
