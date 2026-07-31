"""Camada de render: cascata de compatibilidade e equivalencia entre os backends (R26)."""

import logging
import os

import pygame
import pytest

from src import render

CANVAS = (480, 720)
WINDOW = (960, 720)


@pytest.fixture
def new_renderer():
    """Cria renderizadores e garante que a janela de cada um seja fechada no fim.

    Sem isto, uma janela do `_sdl2` sobreviveria ao teste que a criou e o proximo
    teste comecaria com uma janela orfa aberta."""
    created: list[render.Renderer] = []

    def factory(canvas: tuple[int, int] = CANVAS, window: tuple[int, int] = WINDOW, **kwargs):
        renderer = render.create(canvas, window, **kwargs)
        created.append(renderer)
        return renderer

    yield factory

    for renderer in created:
        if isinstance(renderer, render.GpuRenderer):
            renderer.window.destroy()


def _fake_sdl_renderer(monkeypatch: pytest.MonkeyPatch, *, fails_for) -> list[dict]:
    """Substitui `video.Renderer` por uma versao que falha nos niveis escolhidos.

    Devolve a lista de kwargs de cada tentativa, que e como os testes verificam o
    `vsync` pedido (R26.6) sem depender de um driver especifico."""
    real = render.video.Renderer
    attempts: list[dict] = []

    def fake(window, **kwargs):
        attempts.append(kwargs)
        if kwargs.get("accelerated") in fails_for:
            raise pygame.error("driver indisponivel (simulado)")
        return real(window, accelerated=-1, vsync=kwargs.get("vsync", False))

    monkeypatch.setattr(render.video, "Renderer", fake)
    return attempts


def _scene(renderer: render.Renderer) -> None:
    """Sequencia de desenho identica nos dois backends, exercitando as sete operacoes."""
    tile = pygame.Surface((16, 16))
    for x in range(16):
        for y in range(16):
            tile.set_at((x, y), (x * 16, y * 16, 64))
    image = renderer.make_image(tile)

    renderer.clear((30, 60, 90))
    renderer.draw(image, (10, 20))  # tamanho nativo
    renderer.draw(image, pygame.Rect(60, 20, 64, 64))  # esticado pelo dest
    renderer.draw(image, (10, 100), pygame.Rect(0, 0, 8, 8))  # recorte de strip
    renderer.draw(image, pygame.Rect(60, 100, 32, 32), pygame.Rect(8, 8, 8, 8))  # recorte esticado
    renderer.fill((200, 40, 40), pygame.Rect(0, 200, 120, 40))


# --- cascata (R26.1, R26.2, R26.3, R26.5) ---------------------------------------


def test_first_level_is_the_accelerated_renderer(monkeypatch: pytest.MonkeyPatch, new_renderer) -> None:
    """Com aceleracao disponivel, e ela que sai — sem configuracao nenhuma (R26.1)."""
    _fake_sdl_renderer(monkeypatch, fails_for=())
    renderer = new_renderer()
    assert renderer.backend == render.BACKEND_ACCELERATED


def test_accelerated_renderer_is_asked_for_vsync(monkeypatch: pytest.MonkeyPatch, new_renderer) -> None:
    """Sincronizacao vertical: nem quadro desperdicado, nem rasgo de imagem (R26.6)."""
    attempts = _fake_sdl_renderer(monkeypatch, fails_for=())
    new_renderer()
    assert attempts == [{"accelerated": 1, "vsync": True}]


def test_cascade_falls_to_the_sdl_chosen_renderer(monkeypatch: pytest.MonkeyPatch, new_renderer) -> None:
    """Sem driver acelerado, o SDL escolhe o que houver antes de desistir da GPU (R26.2)."""
    attempts = _fake_sdl_renderer(monkeypatch, fails_for=(1,))
    renderer = new_renderer()
    assert renderer.backend == render.BACKEND_SOFTWARE
    assert [a["accelerated"] for a in attempts] == [1, -1]


def test_cascade_falls_to_the_surface_path(monkeypatch: pytest.MonkeyPatch, new_renderer) -> None:
    """Sem renderizador nenhum, o jogo continua abrindo pelo caminho da v2 (R26.3)."""
    _fake_sdl_renderer(monkeypatch, fails_for=(1, -1))
    renderer = new_renderer()
    assert renderer.backend == render.BACKEND_SURFACE
    assert isinstance(renderer, render.SurfaceRenderer)


def test_cascade_falls_to_the_surface_path_without_the_sdl2_module(
    monkeypatch: pytest.MonkeyPatch, new_renderer
) -> None:
    """Uma build de pygame sem `_sdl2` nao impede o jogo de abrir."""
    monkeypatch.setattr(render, "video", None)
    assert new_renderer().backend == render.BACKEND_SURFACE


def test_cascade_never_raises_to_the_caller(monkeypatch: pytest.MonkeyPatch, new_renderer) -> None:
    """Nem a falha ao abrir a janela do `_sdl2` escapa de `create()` (R26.3)."""

    def explode(*args, **kwargs):
        raise pygame.error("janela indisponivel (simulado)")

    monkeypatch.setattr(render.video, "Window", explode)
    assert new_renderer().backend == render.BACKEND_SURFACE


def test_every_fallback_is_logged(monkeypatch: pytest.MonkeyPatch, new_renderer, caplog) -> None:
    """O motivo de cada queda vai para o log (R26.5)."""
    _fake_sdl_renderer(monkeypatch, fails_for=(1, -1))
    with caplog.at_level(logging.WARNING, logger=render.__name__):
        new_renderer()
    messages = [record.getMessage() for record in caplog.records]
    assert any(render.BACKEND_ACCELERATED in m and "simulado" in m for m in messages)
    assert any(render.BACKEND_SOFTWARE in m and "simulado" in m for m in messages)
    assert any(render.BACKEND_SURFACE in m for m in messages)


def test_backend_of_the_real_environment_is_one_of_the_three(new_renderer) -> None:
    """Sem simulacao nenhuma, o nivel efetivo e sempre um dos tres da tabela."""
    renderer = new_renderer()
    assert renderer.backend in (render.BACKEND_ACCELERATED, render.BACKEND_SOFTWARE, render.BACKEND_SURFACE)
    assert renderer.size == CANVAS


# --- hint de escala (R26.7) -----------------------------------------------------


def test_nearest_neighbour_scaling_is_requested(monkeypatch: pytest.MonkeyPatch, new_renderer) -> None:
    """Filtragem linear borraria a arte em pixel; o hint pede vizinho mais proximo."""
    monkeypatch.delenv(render.ENV_SCALE_QUALITY, raising=False)
    new_renderer()
    assert os.environ[render.ENV_SCALE_QUALITY] == "0"


def test_scale_quality_hint_does_not_override_the_environment(
    monkeypatch: pytest.MonkeyPatch, new_renderer
) -> None:
    """Investigar outra qualidade de escala nao deve exigir editar codigo."""
    monkeypatch.setenv(render.ENV_SCALE_QUALITY, "1")
    new_renderer()
    assert os.environ[render.ENV_SCALE_QUALITY] == "1"


# --- equivalencia entre os dois backends (R26.4) --------------------------------


def _both_backends(monkeypatch: pytest.MonkeyPatch) -> tuple[render.GpuRenderer, render.SurfaceRenderer]:
    """Cria um renderizador de GPU e um de superficie com o mesmo canvas."""
    gpu = render.create(CANVAS, WINDOW)
    assert isinstance(gpu, render.GpuRenderer)
    _fake_sdl_renderer(monkeypatch, fails_for=(1, -1))
    surface = render.create(CANVAS, WINDOW)
    assert isinstance(surface, render.SurfaceRenderer)
    return gpu, surface


def test_both_backends_draw_the_same_frame(monkeypatch: pytest.MonkeyPatch) -> None:
    """A mesma sequencia de chamadas produz o mesmo resultado observavel (R26.4)."""
    gpu, surface = _both_backends(monkeypatch)
    try:
        _scene(gpu)
        _scene(surface)
        from_gpu, from_surface = gpu.snapshot(), surface.snapshot()
        assert from_gpu.get_size() == from_surface.get_size() == CANVAS
        different = [
            (x, y)
            for x in range(0, CANVAS[0], 3)
            for y in range(0, CANVAS[1], 3)
            if from_gpu.get_at((x, y))[:3] != from_surface.get_at((x, y))[:3]
        ]
        assert different == []
    finally:
        gpu.window.destroy()


def test_both_backends_apply_image_alpha_the_same_way(monkeypatch: pytest.MonkeyPatch) -> None:
    """`Image.alpha` e o que sustenta o fade de bioma (R5.4) nos dois caminhos."""
    gpu, surface = _both_backends(monkeypatch)
    try:
        for renderer in (gpu, surface):
            tile = pygame.Surface((40, 40))
            tile.fill((255, 255, 255))
            image = renderer.make_image(tile)
            assert image.size == (40, 40)
            assert image.alpha == 255
            image.alpha = 128
            assert image.alpha == 128
            renderer.clear((0, 0, 0))
            renderer.draw(image, (0, 0))
        # meio branco sobre preto: os dois chegam ao mesmo cinza, a menos de
        # arredondamento do arranjo de mistura de cada caminho
        gpu_pixel = gpu.snapshot().get_at((10, 10))
        surface_pixel = surface.snapshot().get_at((10, 10))
        assert all(abs(a - b) <= 2 for a, b in zip(gpu_pixel[:3], surface_pixel[:3], strict=True))
    finally:
        gpu.window.destroy()


def test_both_backends_blend_a_translucent_fill(monkeypatch: pytest.MonkeyPatch) -> None:
    """O escurecimento de PAUSADO/GAME_OVER e um `fill` com alfa nos dois caminhos."""
    gpu, surface = _both_backends(monkeypatch)
    try:
        for renderer in (gpu, surface):
            renderer.clear((200, 200, 200))
            renderer.fill((0, 0, 0, 128), pygame.Rect(0, 0, 100, 100))
        gpu_pixel = gpu.snapshot().get_at((10, 10))
        surface_pixel = surface.snapshot().get_at((10, 10))
        assert all(abs(a - b) <= 2 for a, b in zip(gpu_pixel[:3], surface_pixel[:3], strict=True))
        assert gpu_pixel[0] < 200  # a mistura de fato aconteceu
    finally:
        gpu.window.destroy()


def test_both_backends_convert_window_coordinates_the_same_way(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mouse e toque chegam em pixels de janela; `to_logical` os traz para o canvas.

    E a simetria que `input.py` passa a explorar na task 51 (R34.1)."""
    gpu, surface = _both_backends(monkeypatch)
    try:
        for point in ((240.0, 0.0), (480.0, 360.0), (959.0, 719.0)):
            from_gpu = gpu.to_logical(*point)
            from_surface = surface.to_logical(*point)
            assert all(abs(a - b) <= 1 for a, b in zip(from_gpu, from_surface, strict=True))
        # canvas 480x720 numa janela 960x720: escala 1, barras de 240px nas laterais
        assert surface.to_logical(240.0, 0.0) == (0.0, 0.0)
        assert surface.to_logical(0.0, 0.0)[0] < 0  # ponto na barra, fora do canvas
    finally:
        gpu.window.destroy()


# --- caminho de superficie -------------------------------------------------------


def test_surface_path_reuses_its_scaled_buffer() -> None:
    """`present()` nao pode alocar uma superficie de alguns MB por frame (R27.3)."""
    renderer = render.SurfaceRenderer(CANVAS, WINDOW)
    renderer.clear((0, 0, 0))
    renderer.present()
    first = renderer._scaled
    renderer.present()
    assert renderer._scaled is first


def test_surface_path_reuses_its_blend_buffer() -> None:
    """Mesmo motivo, para o retangulo translucido do escurecimento."""
    renderer = render.SurfaceRenderer(CANVAS, WINDOW)
    rect = pygame.Rect(0, 0, *CANVAS)
    renderer.fill((0, 0, 0, 120), rect)
    first = renderer._blend
    renderer.fill((0, 0, 0, 120), rect)
    assert renderer._blend is first
