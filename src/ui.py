"""HUD e telas de estado, com fonte pixelada e sombra dura (R7.5, R7.6)."""

import pygame

from src import pixelfont
from src.config import CREDITS, GROUND_H, SCREEN_H, SCREEN_W

SHADOW_COLOR = (40, 30, 20)
SHADOW_OFFSET = 3
OVERLAY_COLOR = (0, 0, 0, 140)
GROUND_Y = SCREEN_H - GROUND_H
GOLD = (255, 215, 60)
MAX_TEXT_W = SCREEN_W - 40  # margem de 20px de cada lado

MUTE_ICON_SIZE = 40
MUTE_ICON_MARGIN = 14
MUTE_ICON_RECT = pygame.Rect(
    SCREEN_W - MUTE_ICON_MARGIN - MUTE_ICON_SIZE, MUTE_ICON_MARGIN, MUTE_ICON_SIZE, MUTE_ICON_SIZE
)


def _scale_for(base_size: int) -> int:
    """Converte o base_size (tamanho de fonte da v1) num fator inteiro de pixel."""
    return max(1, base_size // 2)


def _text_width(n_chars: int, scale: int) -> int:
    return scale * (pixelfont.GLYPH_W * n_chars + pixelfont.SPACING * max(n_chars - 1, 0))


def _fit_scale(text: str, scale: int) -> int:
    """Reduz a escala ate o texto caber em MAX_TEXT_W (a fonte bitmap e proporcionalmente
    mais larga que a SysFont usada na v1, entao alguns textos longos estourariam a tela
    sem este ajuste)."""
    n = len(text)
    while scale > 1 and _text_width(n, scale) > MAX_TEXT_W:
        scale -= 1
    return scale


def draw_text(
    surface: pygame.Surface,
    text: str,
    center: tuple[int, int],
    base_size: int = 12,
    color: tuple[int, int, int] = (255, 255, 255),
) -> None:
    scale = _fit_scale(text, _scale_for(base_size))
    shadow = pixelfont.render(text, scale, SHADOW_COLOR)
    main = pixelfont.render(text, scale, color)
    surface.blit(shadow, shadow.get_rect(center=(center[0] + SHADOW_OFFSET, center[1] + SHADOW_OFFSET)))
    surface.blit(main, main.get_rect(center=center))


def _stack(
    surface: pygame.Surface,
    center_x: int,
    top_y: int,
    lines: list[tuple[str, int, tuple[int, int, int]]],
    margin: int = 8,
) -> None:
    """Empilha linhas de texto verticalmente pela altura real renderizada (R19.3).

    Ao contrario de deltas fixos em pixels, a posicao de cada linha depende da
    altura de fato ocupada pela linha anterior (GLYPH_H * escala + sombra), entao
    duas linhas nunca colidem mesmo se a escala de uma delas mudar.
    """
    y = top_y
    for text, base_size, color in lines:
        scale = _fit_scale(text, _scale_for(base_size))
        height = pixelfont.GLYPH_H * scale
        draw_text(surface, text, (center_x, y + height // 2), base_size=base_size, color=color)
        y += height + SHADOW_OFFSET + margin


def _dim_overlay(surface: pygame.Surface) -> None:
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill(OVERLAY_COLOR)
    surface.blit(overlay, (0, 0))


def draw_ready_screen(surface: pygame.Surface, highscore: int) -> None:
    _stack(
        surface,
        SCREEN_W // 2,
        SCREEN_H // 4,
        [
            ("BLOCKY BIRD", 12, (255, 220, 60)),
            (CREDITS.upper(), 5, (230, 230, 230)),
            ("ESPACO / CLIQUE PARA VOAR", 6, (255, 255, 255)),
        ],
    )
    draw_text(
        surface,
        f"RECORDE: {highscore}",
        (SCREEN_W // 2, GROUND_Y - 24),
        base_size=8,
        color=GOLD,
    )


def draw_mute_icon(surface: pygame.Surface, muted: bool) -> None:
    """Botao de mudo tocavel no canto da tela, estilo voxel (R15.4)."""
    rect = MUTE_ICON_RECT
    pygame.draw.rect(surface, (20, 16, 10), rect)
    pygame.draw.rect(surface, GOLD, rect, width=2)

    color = (220, 70, 60) if muted else (255, 255, 255)
    cx, cy = rect.center
    unit = rect.width // 8
    # corpo do alto-falante: bloco quadrado + haste, em retangulos (estetica blocky)
    pygame.draw.rect(surface, color, (cx - 3 * unit, cy - unit, 2 * unit, 2 * unit))
    pygame.draw.rect(surface, color, (cx - unit, cy - 3 * unit, unit, 6 * unit))

    if muted:
        pygame.draw.line(surface, color, (rect.left + 8, rect.top + 8), (rect.right - 8, rect.bottom - 8), 3)
        pygame.draw.line(surface, color, (rect.left + 8, rect.bottom - 8), (rect.right - 8, rect.top + 8), 3)
    else:
        pygame.draw.rect(surface, color, (cx + unit, cy - 2 * unit, unit, 4 * unit))
        pygame.draw.rect(surface, color, (cx + 2 * unit, cy - 3 * unit, unit, 6 * unit))


def draw_hud_score(surface: pygame.Surface, score: int) -> None:
    draw_text(surface, str(score), (SCREEN_W // 2, 40), base_size=12)


def draw_paused_overlay(surface: pygame.Surface) -> None:
    _dim_overlay(surface)
    _stack(
        surface,
        SCREEN_W // 2,
        SCREEN_H // 2 - 24,
        [
            ("PAUSADO", 12, (255, 255, 255)),
            ("SETAS: MUDO", 5, (210, 210, 210)),
        ],
    )


def draw_game_over_screen(surface: pygame.Surface, score: int, highscore: int) -> None:
    _dim_overlay(surface)
    _stack(
        surface,
        SCREEN_W // 2,
        SCREEN_H // 2 - 90,
        [
            ("GAME OVER", 12, (220, 60, 50)),
            (f"PONTOS: {score}", 8, (255, 255, 255)),
            (f"RECORDE: {highscore}", 8, (255, 255, 255)),
            ("ESPACO / CLIQUE PARA REINICIAR", 5, (220, 220, 220)),
        ],
    )
