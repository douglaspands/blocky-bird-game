"""Geracao procedural de texturas voxel (blocos 16x16 escalados)."""

import random
from collections.abc import Callable

import pygame

from src.render import convert

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


Box = tuple[tuple[int, int, int], int, int, int, int]
"""Um cubo de um sprite: a cor e o retangulo (x, y, largura, altura) dentro dos 16x16."""


def _voxel(boxes: list[Box]) -> pygame.Surface:
    """Monta um sprite 16x16 empilhando cubos, na ordem em que aparecem.

    `make_bee` posiciona pixel a pixel, o que cabia num sprite so. Para os nove mobs de
    R25.3, com dois frames cada, a lista de cubos e a mesma ideia escrita de forma
    legivel: cada linha e uma parte do corpo, o que vem depois pinta por cima do que
    veio antes, e o frame de idle e a mesma lista com um ou dois cubos movidos."""
    surf = pygame.Surface((TEX_SIZE, TEX_SIZE), pygame.SRCALPHA)
    for color, x, y, w, h in boxes:
        surf.fill(color, pygame.Rect(x, y, w, h))
    return surf


CREEPER_SKIN = (94, 173, 92)
CREEPER_DARK = (66, 138, 68)
CREEPER_FACE = (24, 34, 24)


def make_creeper(frame: int = 0) -> pygame.Surface:
    """Creeper: cabeca quadrada com a face mais reconhecivel do jogo, quatro patas."""
    front, back = (4, 3) if frame == 0 else (3, 4)
    return _voxel(
        [
            (CREEPER_SKIN, 4, 0, 8, 8),
            (CREEPER_FACE, 5, 2, 2, 2),
            (CREEPER_FACE, 9, 2, 2, 2),
            (CREEPER_FACE, 7, 4, 2, 3),  # boca central
            (CREEPER_FACE, 6, 5, 1, 2),  # presas
            (CREEPER_FACE, 9, 5, 1, 2),
            (CREEPER_SKIN, 5, 8, 6, 4),
            (CREEPER_DARK, 5, 9, 2, 2),
            (CREEPER_DARK, 9, 10, 2, 2),
            (CREEPER_SKIN, 4, 12, 3, front),  # patas alternam no idle
            (CREEPER_SKIN, 9, 12, 3, back),
        ]
    )


WITCH_ROBE = (92, 62, 140)
WITCH_HAT = (46, 34, 62)
WITCH_SKIN = (172, 150, 128)
WITCH_NOSE = (140, 118, 100)
WITCH_POTION = (120, 220, 120)


def make_witch(frame: int = 0) -> pygame.Surface:
    """Bruxa: chapeu de aba larga, manto roxo e o frasco de pocao na mao."""
    lift = frame  # o frasco sobe e desce
    return _voxel(
        [
            (WITCH_HAT, 6, 0, 4, 3),
            (WITCH_HAT, 3, 3, 10, 1),  # aba
            (WITCH_SKIN, 5, 4, 6, 4),
            (WITCH_HAT, 5, 4, 6, 1),  # franja
            ((40, 30, 30), 6, 6, 1, 1),
            ((40, 30, 30), 9, 6, 1, 1),
            (WITCH_NOSE, 7, 6, 2, 2),
            (WITCH_ROBE, 4, 8, 8, 8),
            (WITCH_HAT, 4, 15, 8, 1),
            (WITCH_SKIN, 3, 9, 1, 3),
            (WITCH_SKIN, 12, 9, 1, 3),
            (WITCH_POTION, 12, 11 - lift, 2, 2),
        ]
    )


VILLAGER_ROBE = (110, 78, 52)
VILLAGER_SKIN = (196, 156, 118)
VILLAGER_NOSE = (168, 128, 94)
VILLAGER_HAIR = (72, 52, 36)
VILLAGER_APRON = (86, 60, 40)


def make_villager(frame: int = 0) -> pygame.Surface:
    """Aldeao: tunica marrom, bracos cruzados e o nariz que e a marca da especie."""
    arms = frame
    return _voxel(
        [
            (VILLAGER_SKIN, 5, 1, 6, 5),
            (VILLAGER_HAIR, 5, 0, 6, 2),
            ((40, 32, 28), 6, 3, 1, 1),
            ((40, 32, 28), 9, 3, 1, 1),
            (VILLAGER_NOSE, 7, 3, 2, 3),
            (VILLAGER_ROBE, 4, 6, 8, 10),
            (VILLAGER_APRON, 4, 9 + arms, 8, 2),  # bracos cruzados sobem e descem
        ]
    )


ENDER_BODY = (18, 18, 24)
ENDER_EYE = (206, 118, 244)


def make_enderman(frame: int = 0) -> pygame.Surface:
    """Enderman: silhueta preta e esticada, com os olhos roxos como unica cor."""
    reach = frame
    return _voxel(
        [
            (ENDER_BODY, 5, 0, 6, 4),
            (ENDER_EYE, 5, 2, 2, 1),
            (ENDER_EYE, 9, 2, 2, 1),
            (ENDER_BODY, 6, 4, 4, 5),
            (ENDER_BODY, 4, 4, 1, 6 + reach),  # bracos compridos
            (ENDER_BODY, 11, 4, 1, 6 + reach),
            (ENDER_BODY, 6, 9, 1, 7),
            (ENDER_BODY, 9, 9, 1, 7),
        ]
    )


SPIDER_BODY = (52, 42, 40)
SPIDER_LEG = (34, 28, 26)
SPIDER_EYE = (208, 52, 44)


def make_spider(frame: int = 0) -> pygame.Surface:
    """Aranha: corpo baixo, oito patas e os olhos vermelhos."""
    step = frame
    legs: list[Box] = []
    for y, direction in ((4, 1), (7, -1), (10, 1), (13, -1)):
        legs.append((SPIDER_LEG, 0, y + direction * step, 5, 1))
        legs.append((SPIDER_LEG, 11, y + direction * step, 5, 1))
    return _voxel(
        [
            *legs,  # antes do corpo: as patas saem de tras dele
            (SPIDER_BODY, 4, 5, 8, 6),
            (SPIDER_BODY, 5, 2, 6, 3),
            (SPIDER_EYE, 5, 3, 2, 1),
            (SPIDER_EYE, 9, 3, 2, 1),
        ]
    )


BONE = (226, 226, 220)
BONE_DARK = (176, 176, 170)
SKULL_EYE = (28, 28, 30)


def make_skeleton(frame: int = 0) -> pygame.Surface:
    """Esqueleto: cranio com as orbitas vazias, costelas e membros finos."""
    lift = frame
    return _voxel(
        [
            (BONE, 5, 0, 6, 5),
            (SKULL_EYE, 6, 2, 1, 2),
            (SKULL_EYE, 9, 2, 1, 2),
            (BONE_DARK, 7, 4, 2, 1),  # maxilar
            (BONE, 6, 5, 4, 6),
            (BONE_DARK, 6, 7, 4, 1),  # costelas
            (BONE_DARK, 6, 9, 4, 1),
            (BONE, 5, 5 + lift, 1, 5),  # bracos sobem e descem
            (BONE, 10, 5 + lift, 1, 5),
            (BONE, 6, 11, 1, 5),
            (BONE, 9, 11, 1, 5),
        ]
    )


GHAST_BODY = (226, 226, 226)
GHAST_SHADE = (196, 196, 198)
GHAST_FACE = (196, 44, 40)


def make_ghast(frame: int = 0) -> pygame.Surface:
    """Ghast: cubo branco flutuante com os tentaculos ondulando embaixo."""
    tail = frame
    return _voxel(
        [
            (GHAST_BODY, 3, 1, 10, 9),
            (GHAST_SHADE, 3, 8, 10, 1),
            (GHAST_FACE, 5, 4, 2, 2),
            (GHAST_FACE, 9, 4, 2, 2),
            (GHAST_FACE, 6, 7, 4, 1),
            (GHAST_BODY, 4, 10, 2, 4 + tail),  # tentaculos ondulam
            (GHAST_BODY, 7, 10, 2, 6 - tail),
            (GHAST_BODY, 10, 10, 2, 3 + tail),
        ]
    )


BLAZE_CORE = (255, 216, 92)
BLAZE_ROD = (250, 158, 40)
BLAZE_FACE = (60, 40, 20)


def make_blaze(frame: int = 0) -> pygame.Surface:
    """Blaze: nucleo em brasa cercado pelas varas, que giram entre os dois frames."""
    rods = ((2, 5), (12, 4), (4, 11), (11, 10)) if frame == 0 else ((3, 3), (11, 6), (2, 9), (12, 12))
    boxes: list[Box] = [(BLAZE_ROD, x, y, 2, 3) for x, y in rods]
    boxes += [
        (BLAZE_CORE, 5, 2, 6, 5),
        (BLAZE_FACE, 6, 4, 1, 1),
        (BLAZE_FACE, 9, 4, 1, 1),
        (BLAZE_ROD, 5, 7, 6, 5),
        (BLAZE_CORE, 6, 8, 4, 3),
    ]
    return _voxel(boxes)


PIGLIN_SKIN = (232, 164, 150)
PIGLIN_SNOUT = (206, 128, 122)
PIGLIN_TUNIC = (146, 112, 58)
PIGLIN_GOLD = (232, 196, 84)


def make_piglin(frame: int = 0) -> pygame.Surface:
    """Piglin: focinho, orelhas de fora e o peitoral dourado."""
    step = frame
    return _voxel(
        [
            (PIGLIN_SKIN, 5, 1, 6, 5),
            (PIGLIN_SKIN, 3, 2, 2, 2),  # orelhas
            (PIGLIN_SKIN, 11, 2, 2, 2),
            ((48, 32, 30), 6, 2, 1, 1),
            ((48, 32, 30), 9, 2, 1, 1),
            (PIGLIN_SNOUT, 6, 4, 4, 2),
            (PIGLIN_TUNIC, 5, 6, 6, 5),
            (PIGLIN_GOLD, 5, 6, 6, 1),
            (PIGLIN_SKIN, 4, 7, 1, 4),
            (PIGLIN_SKIN, 11, 7, 1, 4),
            (PIGLIN_TUNIC, 5, 11, 2, 4 + step),  # pernas alternam
            (PIGLIN_TUNIC, 9, 11, 2, 5 - step),
        ]
    )


MOB_MAKERS: dict[str, Callable[[int], pygame.Surface]] = {
    "creeper": make_creeper,
    "witch": make_witch,
    "villager": make_villager,
    "enderman": make_enderman,
    "spider": make_spider,
    "skeleton": make_skeleton,
    "ghast": make_ghast,
    "blaze": make_blaze,
    "piglin": make_piglin,
}
"""Os nove mobs decorativos de R25.3, todos gerados por codigo — nenhuma imagem
externa e nenhum material de terceiros, a mesma disciplina dos blocos (R7.1).

Quem distribui e desenha e `mobs.py`; aqui ficam so as formas, porque este e o modulo
que ja sabia pintar voxel e porque assim `mobs.py` nao depende de nenhum modulo de
jogo (R25.4)."""


def scale_pixel_perfect(surface: pygame.Surface, size: int) -> pygame.Surface:
    return pygame.transform.scale(surface, (size, size))


def generate_all(block_size: int) -> dict[str, pygame.Surface]:
    """Gera todas as texturas base 16x16 e escala pixel-perfect para block_size (R7.1).

    Cada textura sai ja no formato de pixel do display (R27.4). Estas sao as
    superficies mais reusadas do jogo — a mesma pedra vira dezenas de blocos de
    coluna por frame, e alimenta tambem as faixas laterais e os sprites rotacionados
    da abelha —, entao converte-las na geracao vale por todos esses usos de uma vez.
    """
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
    return {name: convert(scale_pixel_perfect(surf, block_size)) for name, surf in raw.items()}
