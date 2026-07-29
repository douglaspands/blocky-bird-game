"""Classe Bird: fisica e animacao do passaro (R1)."""

import pygame

from src.config import BLOCK, FLAP_IMPULSE, GRAVITY, HITBOX_SCALE, MAX_FALL_SPEED

WING_FRAME_INTERVAL = 6
MAX_ANGLE_UP = 30
MAX_ANGLE_DOWN = -60
ANGLE_FALL_STEP = 3


class Bird:
    def __init__(self, x: float, y: float) -> None:
        self.pos = pygame.Vector2(x, y)
        self.vel_y = 0.0
        self.angle = 0.0
        self.frame = 0
        self.size = BLOCK
        self._frame_timer = 0

    def flap(self) -> None:
        self.vel_y = FLAP_IMPULSE
        self.angle = MAX_ANGLE_UP

    def update(self) -> None:
        self.vel_y = min(self.vel_y + GRAVITY, MAX_FALL_SPEED)
        self.pos.y += self.vel_y

        if self.pos.y < 0:
            self.pos.y = 0
            self.vel_y = 0

        if self.vel_y < 0:
            self.angle = MAX_ANGLE_UP
        else:
            self.angle = max(MAX_ANGLE_DOWN, self.angle - ANGLE_FALL_STEP)

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

    def draw(self, surface: pygame.Surface, textures: dict[str, pygame.Surface]) -> None:
        tex = textures[f"bee_{self.frame}"]
        rotated = pygame.transform.rotate(tex, self.angle)
        rect = rotated.get_rect(center=(self.pos.x + self.size / 2, self.pos.y + self.size / 2))
        surface.blit(rotated, rect)
