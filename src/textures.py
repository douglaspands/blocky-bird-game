"""Geracao procedural de texturas voxel (blocos 16x16 escalados)."""

import random

import pygame

TEX_SIZE = 16


def _shaded(base_color: tuple[int, int, int], seed: int, variation: float = 0.12) -> pygame.Surface:
    surf = pygame.Surface((TEX_SIZE, TEX_SIZE))
    rng = random.Random(seed)
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            factor = 1 + rng.uniform(-variation, variation)
            color = tuple(max(0, min(255, round(c * factor))) for c in base_color)
            surf.set_at((x, y), color)
    return surf


def make_dirt(seed: int = 1) -> pygame.Surface:
    return _shaded((134, 96, 67), seed)


def make_grass_side(seed: int = 2) -> pygame.Surface:
    surf = make_dirt(seed)
    rng = random.Random(seed + 1)
    for x in range(TEX_SIZE):
        for y in range(3):
            factor = 1 + rng.uniform(-0.12, 0.12)
            color = tuple(max(0, min(255, round(c * factor))) for c in (95, 159, 53))
            surf.set_at((x, y), color)
    return surf


def make_stone(seed: int = 3) -> pygame.Surface:
    return _shaded((128, 128, 128), seed)


def make_cobblestone(seed: int = 4) -> pygame.Surface:
    return _shaded((122, 122, 122), seed, variation=0.22)


def make_netherrack(seed: int = 5) -> pygame.Surface:
    return _shaded((110, 54, 48), seed, variation=0.18)


def make_obsidian(seed: int = 6) -> pygame.Surface:
    surf = _shaded((20, 16, 34), seed, variation=0.15)
    rng = random.Random(seed + 1)
    for _ in range(6):
        x = rng.randrange(TEX_SIZE)
        y = rng.randrange(TEX_SIZE)
        purple = tuple(max(0, min(255, c + rng.randint(20, 60))) for c in (60, 30, 90))
        surf.set_at((x, y), purple)
    return surf


def make_bee(frame: int = 0) -> pygame.Surface:
    """Abelha voxel: corpo amarelo com listras pretas, asas em 2 frames (R7.2)."""
    surf = pygame.Surface((TEX_SIZE, TEX_SIZE), pygame.SRCALPHA)
    body = (240, 200, 30)
    stripe = (30, 24, 10)
    wing = (220, 230, 235, 180)

    body_rows = range(4, 12)
    for y in body_rows:
        for x in range(3, 13):
            surf.set_at((x, y), body)

    for y in body_rows:
        for x in (4, 5, 8, 9):
            surf.set_at((x, y), stripe)

    for x in range(3, 13):
        surf.set_at((x, 4), stripe)
        surf.set_at((x, 11), stripe)

    wing_rows = range(2, 6) if frame == 0 else range(4, 8)
    for y in wing_rows:
        for x in range(9, 14):
            surf.set_at((x, y), wing)

    return surf


def scale_pixel_perfect(surface: pygame.Surface, size: int) -> pygame.Surface:
    return pygame.transform.scale(surface, (size, size))


def generate_all(block_size: int) -> dict[str, pygame.Surface]:
    """Gera todas as texturas base 16x16 e escala pixel-perfect para block_size (R7.1)."""
    raw = {
        "dirt": make_dirt(),
        "grass_side": make_grass_side(),
        "stone": make_stone(),
        "cobblestone": make_cobblestone(),
        "netherrack": make_netherrack(),
        "obsidian": make_obsidian(),
        "bee_0": make_bee(0),
        "bee_1": make_bee(1),
    }
    return {name: scale_pixel_perfect(surf, block_size) for name, surf in raw.items()}
