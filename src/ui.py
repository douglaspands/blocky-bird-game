"""HUD e telas de estado, com fonte pixelada e sombra dura (R7.5)."""

import pygame

from src.config import CREDITS, GROUND_H, SCREEN_H, SCREEN_W

FONT_NAME = "couriernew"
SHADOW_COLOR = (40, 30, 20)
SHADOW_OFFSET = 3
TEXT_SCALE = 3
OVERLAY_COLOR = (0, 0, 0, 140)
GROUND_Y = SCREEN_H - GROUND_H
GOLD = (255, 215, 60)

_font_cache: dict[int, pygame.font.Font] = {}


def _get_font(base_size: int) -> pygame.font.Font:
    font = _font_cache.get(base_size)
    if font is None:
        font = pygame.font.SysFont(FONT_NAME, base_size, bold=True)
        _font_cache[base_size] = font
    return font


def _render_pixel_text(text: str, base_size: int, color: tuple[int, int, int]) -> pygame.Surface:
    font = _get_font(base_size)
    small = font.render(text, False, color)
    w, h = small.get_size()
    return pygame.transform.scale(small, (max(w, 1) * TEXT_SCALE, max(h, 1) * TEXT_SCALE))


def draw_text(
    surface: pygame.Surface,
    text: str,
    center: tuple[int, int],
    base_size: int = 12,
    color: tuple[int, int, int] = (255, 255, 255),
) -> None:
    shadow = _render_pixel_text(text, base_size, SHADOW_COLOR)
    main = _render_pixel_text(text, base_size, color)
    surface.blit(shadow, shadow.get_rect(center=(center[0] + SHADOW_OFFSET, center[1] + SHADOW_OFFSET)))
    surface.blit(main, main.get_rect(center=center))


def _dim_overlay(surface: pygame.Surface) -> None:
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill(OVERLAY_COLOR)
    surface.blit(overlay, (0, 0))


def draw_ready_screen(surface: pygame.Surface, highscore: int) -> None:
    draw_text(surface, "BLOCKY BIRD", (SCREEN_W // 2, SCREEN_H // 3), base_size=18, color=(255, 220, 60))
    draw_text(
        surface,
        CREDITS.upper(),
        (SCREEN_W // 2, SCREEN_H // 3 + 28),
        base_size=8,
        color=(230, 230, 230),
    )
    draw_text(
        surface,
        "ESPACO / CLIQUE PARA VOAR",
        (SCREEN_W // 2, SCREEN_H // 3 + 70),
        base_size=10,
    )
    _draw_highscore_badge(surface, highscore)


def _draw_highscore_badge(surface: pygame.Surface, highscore: int) -> None:
    """Destaque do recorde no rodape da tela inicial, estilo placa voxel."""
    badge = pygame.Rect(0, 0, 220, 46)
    badge.centerx = SCREEN_W // 2
    badge.bottom = GROUND_Y - 24

    pygame.draw.rect(surface, (25, 20, 8), badge)
    pygame.draw.rect(surface, GOLD, badge, width=4)

    draw_text(surface, f"RECORDE: {highscore}", badge.center, base_size=12, color=GOLD)


def draw_hud_score(surface: pygame.Surface, score: int) -> None:
    draw_text(surface, str(score), (SCREEN_W // 2, 60), base_size=20)


def draw_paused_overlay(surface: pygame.Surface) -> None:
    _dim_overlay(surface)
    draw_text(surface, "PAUSADO", (SCREEN_W // 2, SCREEN_H // 2), base_size=18)


def draw_game_over_screen(surface: pygame.Surface, score: int, highscore: int) -> None:
    _dim_overlay(surface)
    draw_text(surface, "GAME OVER", (SCREEN_W // 2, SCREEN_H // 2 - 60), base_size=18, color=(220, 60, 50))
    draw_text(surface, f"PONTOS: {score}", (SCREEN_W // 2, SCREEN_H // 2), base_size=12)
    draw_text(surface, f"RECORDE: {highscore}", (SCREEN_W // 2, SCREEN_H // 2 + 30), base_size=12)
    draw_text(
        surface,
        "ESPACO / CLIQUE PARA REINICIAR",
        (SCREEN_W // 2, SCREEN_H // 2 + 70),
        base_size=9,
        color=(220, 220, 220),
    )
