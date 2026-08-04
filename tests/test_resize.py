"""Retrato travado no Android e recomputacao do canvas ao redimensionar (R23.5, R23.6)."""

import os

import pygame
import pytest

from src import config, mobs, textures, viewport
from src.bird import ANGLES
from src.game import RESIZE_SETTLE_FRAMES, Game
from src.input import ACTION_RESIZE, InputManager
from src.viewport import PLAY_H, PLAY_W
from tests.fakes import FakeRenderer


def test_portrait_orientation_hint_is_set(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reforca no SDL o `orientation = portrait` do buildozer.spec (R23.5)."""
    monkeypatch.delenv(viewport.ENV_ORIENTATION, raising=False)
    viewport.lock_portrait_orientation()
    assert os.environ[viewport.ENV_ORIENTATION] == "Portrait"


def test_orientation_hint_does_not_override_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Investigar paisagem nao deve exigir editar codigo."""
    monkeypatch.setenv(viewport.ENV_ORIENTATION, "LandscapeLeft")
    viewport.lock_portrait_orientation()
    assert os.environ[viewport.ENV_ORIENTATION] == "LandscapeLeft"


def test_window_resized_event_becomes_a_resize_action():
    pygame.event.clear()
    im = InputManager(FakeRenderer((960, 720)))
    pygame.event.post(pygame.event.Event(pygame.WINDOWRESIZED, x=1280, y=720))
    actions, _ = im.poll()
    assert ACTION_RESIZE in actions


def test_resize_recomputes_the_canvas_and_keeps_the_play_area():
    """O canvas acompanha a nova proporcao; a area jogavel nao se mexe (R23.6, R24.1)."""
    game = Game()
    assert game.viewport.canvas == viewport.DESKTOP_WINDOW

    game.apply_resize((1920, 1080))

    assert game.viewport.canvas == (1280, 720)
    assert game.viewport.play.size == (PLAY_W, PLAY_H)
    assert config.viewport().canvas == (1280, 720)  # o resto do jogo enxerga o novo canvas
    assert game.renderer.size == (1280, 720)


def test_resize_discards_the_images_keyed_by_canvas_size():
    """Gradiente de ceu e faixas laterais sao chaveados pelo tamanho do canvas: as
    versoes antigas nunca mais seriam pedidas e ficariam ocupando memoria de video.

    O que sobra depois sao exatamente as 62 rotacoes da abelha e os 18 sprites de mob,
    e eles sobram porque `apply_resize` os reconstroi de proposito (tasks 56 e 57):
    `forget_images` derruba tudo, inclusive o que nao depende do canvas, e refaze-los
    ali e o que impede que voltem um por frame durante o jogo."""
    game = Game()
    game.renderer = FakeRenderer(game.viewport.canvas)
    game.draw()
    assert game.renderer._images

    game.apply_resize((1920, 1080))
    bees = {("bee", frame, angle) for frame in (0, 1) for angle in ANGLES}
    mob_sprites = {("mob", kind, frame) for kind in textures.MOB_MAKERS for frame in mobs.IDLE_FRAMES}
    assert set(game.renderer._images) == bees | mob_sprites
    assert game.renderer.size == (1280, 720)


def test_resize_to_a_taller_window_moves_the_play_area_down():
    """As faixas sao recalculadas junto com o canvas, nao so o tamanho dele."""
    game = Game()
    game.apply_resize((1080, 2400))

    assert game.viewport.canvas == (480, 1067)
    assert game.viewport.play.top == game.viewport.sky_band.height == 251
    assert game.viewport.ground_band.height == 96
    assert config.ground_y() == game.viewport.play.bottom - config.GROUND_H


def test_resize_without_aspect_change_keeps_the_canvas_and_the_images():
    """Uma janela maior na MESMA proporcao produz o mesmo canvas — reconstruir os
    gradientes e as faixas ali seria puro desperdicio."""
    game = Game()
    game.renderer = FakeRenderer(game.viewport.canvas)
    game.draw()
    before = dict(game.renderer._images)

    game.apply_resize((1920, 1440))  # 4:3, como 960x720

    assert game.viewport.canvas == viewport.DESKTOP_WINDOW
    assert game.renderer._images == before


def test_resize_is_applied_only_after_the_drag_settles(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cada pixel de um arrasto emite um evento; aplicar todos recriaria o display
    dezenas de vezes por segundo."""
    game = Game()
    applied: list[tuple[int, int]] = []
    monkeypatch.setattr(game, "apply_resize", applied.append)

    game._pending_resize = (1920, 1080)
    game._resize_idle = 0
    for _ in range(RESIZE_SETTLE_FRAMES - 1):
        game._tick_resize()
    assert applied == []

    game._tick_resize()
    assert applied == [(1920, 1080)]

    game._tick_resize()  # nada pendente: nao repete
    assert applied == [(1920, 1080)]


def test_a_new_event_during_the_drag_restarts_the_wait(monkeypatch: pytest.MonkeyPatch) -> None:
    game = Game()
    applied: list[tuple[int, int]] = []
    monkeypatch.setattr(game, "apply_resize", applied.append)

    game._pending_resize = (1400, 900)
    game._resize_idle = 0
    for _ in range(RESIZE_SETTLE_FRAMES - 1):
        game._tick_resize()

    game._pending_resize = (1920, 1080)  # o arrasto continuou
    game._resize_idle = 0
    for _ in range(RESIZE_SETTLE_FRAMES - 1):
        game._tick_resize()
    assert applied == []

    game._tick_resize()
    assert applied == [(1920, 1080)]  # so o tamanho final e aplicado
