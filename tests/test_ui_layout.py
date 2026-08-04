"""Verifica que nenhuma tela sobrepoe textos, mesmo com valores extremos (R19.5).

Desde a task 50 a verificacao e sobre as chamadas registradas pelo `FakeRenderer`, e
nao mais sobre um espiao monkeypatchado em `ui.draw_text`: o retangulo de cada linha
vem do tamanho real da imagem que foi desenhada, entao o teste mede o que o jogador
veria em vez de recalcular a metrica por fora.
"""

import itertools

import pygame
import pytest

from src import config, render, ui
from src.viewport import PLAY_H, PLAY_W
from tests.fakes import FakeRenderer

GROUND_Y = PLAY_H - config.GROUND_H


def _rects_for_screen(draw_fn, *args) -> list[pygame.Rect]:
    """Roda uma tela de estado e devolve o retangulo de cada linha de texto."""
    renderer = FakeRenderer((PLAY_W, PLAY_H))
    draw_fn(renderer, *args)
    return [rect for _, rect in renderer.texts]


def _assert_texts_in_bounds(rects: list[pygame.Rect]) -> None:
    for r in rects:
        assert r.left >= 20
        assert r.right <= PLAY_W - 20
        assert r.bottom <= GROUND_Y


def _assert_no_overlaps(rects: list[pygame.Rect]) -> None:
    for a, b in itertools.combinations(rects, 2):
        assert not a.colliderect(b)


def test_ready_screen_texts_do_not_overlap() -> None:
    rects = _rects_for_screen(ui.draw_ready_screen, 999999)
    assert len(rects) == 4  # titulo, creditos, instrucao, recorde
    _assert_texts_in_bounds(rects)
    _assert_no_overlaps([*rects, ui.mute_icon_rect()])


def test_hud_score_text_in_bounds() -> None:
    rects = _rects_for_screen(ui.draw_hud_score, 999999)
    _assert_texts_in_bounds(rects)
    _assert_no_overlaps([*rects, ui.mute_icon_rect()])


def test_paused_overlay_texts_do_not_overlap() -> None:
    rects = _rects_for_screen(ui.draw_paused_overlay)
    _assert_texts_in_bounds(rects)
    _assert_no_overlaps([*rects, ui.mute_icon_rect()])


def test_game_over_screen_texts_do_not_overlap() -> None:
    rects = _rects_for_screen(ui.draw_game_over_screen, 999999, 999999)
    assert len(rects) == 4
    _assert_texts_in_bounds(rects)
    _assert_no_overlaps([*rects, ui.mute_icon_rect()])


def test_dim_overlay_is_a_single_fill_over_the_whole_canvas() -> None:
    """O escurecimento cobre o canvas inteiro com uma cor translucida.

    Na v2 era uma `Surface` de tela cheia criada a cada frame — a maior fonte de lixo
    por frame que a secao 30 do design mediu. Agora e uma chamada de `fill`."""
    renderer = FakeRenderer((PLAY_W, PLAY_H))
    ui.draw_paused_overlay(renderer)
    assert (ui.OVERLAY_COLOR, pygame.Rect(0, 0, PLAY_W, PLAY_H)) in renderer.fills


def test_dim_overlay_allocates_no_surface_per_frame(monkeypatch: pytest.MonkeyPatch) -> None:
    """A afirmacao acima e sobre a chamada; esta e sobre a memoria, e precisa do
    renderizador de verdade.

    Num `FakeRenderer` nada alocaria de qualquer forma — o `fill` so anota a cor. Quem
    de fato precisava de uma superficie e o caminho de superficie, que mistura o alfa
    a mao, e e `SurfaceRenderer._blend_surface` que a reaproveita entre frames. No
    caminho de GPU a mistura e do SDL e nao ha superficie nenhuma."""
    canvas = (PLAY_W, PLAY_H)
    renderer = render.SurfaceRenderer(canvas, canvas)
    ui.draw_paused_overlay(renderer)  # primeiro frame: enche os caches

    monkeypatch.setattr(pygame, "Surface", _forbidden_surface)
    for _ in range(10):
        ui.draw_paused_overlay(renderer)


def _forbidden_surface(*args: object, **kwargs: object) -> object:
    raise AssertionError("Surface alocada durante o desenho do overlay")


def test_mute_icon_is_one_draw_call_per_state() -> None:
    """O icone tem riscas diagonais, que o renderizador nao preenche: e imagem.

    Sao duas no total, uma por estado, e desenhar de novo nao constroi nada novo."""
    renderer = FakeRenderer((PLAY_W, PLAY_H))
    ui.draw_mute_icon(renderer, muted=False)
    ui.draw_mute_icon(renderer, muted=True)
    ui.draw_mute_icon(renderer, muted=False)

    rects = renderer.drawn("mute_icon")
    assert len(rects) == 3
    assert all(rect == ui.mute_icon_rect() for rect in rects)
    assert len(renderer._images) == 2
