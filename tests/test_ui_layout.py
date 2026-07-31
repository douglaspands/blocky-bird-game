"""Verifica que nenhuma tela sobrepoe textos, mesmo com valores extremos (R19.5)."""

import itertools

import pygame
import pytest

from src import config, pixelfont, ui
from src.viewport import PLAY_H, PLAY_W

GROUND_Y = PLAY_H - config.GROUND_H


def _rects_for_screen(monkeypatch: pytest.MonkeyPatch, draw_fn, *args) -> list[pygame.Rect]:
    """Instrumenta ui.draw_text para capturar os Rects (texto + sombra) em vez de so desenhar."""
    rects: list[pygame.Rect] = []
    original_draw_text = ui.draw_text

    def spy(surface, text, center, base_size=12, color=(255, 255, 255)):
        original_draw_text(surface, text, center, base_size=base_size, color=color)
        scale = ui._fit_scale(text, ui._scale_for(base_size))
        width = ui._text_width(len(text), scale)
        height = pixelfont.GLYPH_H * scale
        rect = pygame.Rect(0, 0, width, height)
        rect.center = center
        rect.width += ui.SHADOW_OFFSET
        rect.height += ui.SHADOW_OFFSET
        rects.append(rect)

    monkeypatch.setattr(ui, "draw_text", spy)
    surface = pygame.Surface((PLAY_W, PLAY_H))
    draw_fn(surface, *args)
    return rects


def _assert_texts_in_bounds(rects: list[pygame.Rect]) -> None:
    for r in rects:
        assert r.left >= 20
        assert r.right <= PLAY_W - 20
        assert r.bottom <= GROUND_Y


def _assert_no_overlaps(rects: list[pygame.Rect]) -> None:
    for a, b in itertools.combinations(rects, 2):
        assert not a.colliderect(b)


def test_ready_screen_texts_do_not_overlap(monkeypatch: pytest.MonkeyPatch) -> None:
    rects = _rects_for_screen(monkeypatch, ui.draw_ready_screen, 999999)
    _assert_texts_in_bounds(rects)
    _assert_no_overlaps([*rects, ui.mute_icon_rect()])


def test_hud_score_text_in_bounds(monkeypatch: pytest.MonkeyPatch) -> None:
    rects = _rects_for_screen(monkeypatch, ui.draw_hud_score, 999999)
    _assert_texts_in_bounds(rects)
    _assert_no_overlaps([*rects, ui.mute_icon_rect()])


def test_paused_overlay_texts_do_not_overlap(monkeypatch: pytest.MonkeyPatch) -> None:
    rects = _rects_for_screen(monkeypatch, ui.draw_paused_overlay)
    _assert_texts_in_bounds(rects)
    _assert_no_overlaps([*rects, ui.mute_icon_rect()])


def test_game_over_screen_texts_do_not_overlap(monkeypatch: pytest.MonkeyPatch) -> None:
    rects = _rects_for_screen(monkeypatch, ui.draw_game_over_screen, 999999, 999999)
    _assert_texts_in_bounds(rects)
    _assert_no_overlaps([*rects, ui.mute_icon_rect()])
