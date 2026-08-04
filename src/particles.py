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
    """Um fragmento de bloco em queda livre, com cor amostrada da textura atingida.

    Sem `__dict__` por instancia: sao 16 por explosao, todas iguais em forma (R27.3).
    """

    __slots__ = ("color", "lifetime", "pos", "rect", "size", "vel")

    def __init__(
        self,
        pos: tuple[float, float],
        vel: tuple[float, float],
        lifetime: int,
        size: int,
        color: tuple[int, int, int],
    ) -> None:
        """Cria a particula em `pos`, com velocidade, duracao, tamanho e cor dados."""
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
        """Avanca um passo: gravidade, posicao, contagem regressiva de vida."""
        self.vel.y += GRAVITY
        self.pos += self.vel
        self.lifetime -= 1
        self._sync_rect()

    def _sync_rect(self) -> None:
        self.rect.centerx = round(self.pos.x)
        self.rect.centery = round(self.pos.y)

    @property
    def alive(self) -> bool:
        """Verdadeiro enquanto a duracao restante for maior que zero."""
        return self.lifetime > 0

    def draw(self, renderer: render.Renderer) -> None:
        """Desenha a particula como um quadrado solido na sua cor."""
        renderer.fill(self.color, self.rect)


class ParticleSystem:
    """Conjunto de particulas vivas: dispara explosoes e atualiza/desenha todas."""

    def __init__(self) -> None:
        """Inicia sem nenhuma particula em cena."""
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
        """Atualiza todas as particulas e remove as que ja expiraram."""
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
        """Desenha todas as particulas vivas."""
        for particle in self.particles:
            particle.draw(renderer)
