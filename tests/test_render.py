"""Camada de render: cascata de compatibilidade e equivalencia entre os backends (R26)."""

import logging
import os

import pygame
import pytest

from src import pixelfont, render, textures
from src.config import BLOCK

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


# --- hints do SDL (R26.7, design secao 40) --------------------------------------


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


def test_draw_call_batching_is_requested(monkeypatch: pytest.MonkeyPatch, new_renderer) -> None:
    """Agrupa desenhos consecutivos de mesma textura numa submissao so ao driver."""
    monkeypatch.delenv(render.ENV_RENDER_BATCHING, raising=False)
    new_renderer()
    assert os.environ[render.ENV_RENDER_BATCHING] == "1"


def test_batching_hint_does_not_override_the_environment(
    monkeypatch: pytest.MonkeyPatch, new_renderer
) -> None:
    """Desligar o agrupamento para isolar um problema de driver nao deve exigir
    editar codigo — mesma regra do hint de escala."""
    monkeypatch.setenv(render.ENV_RENDER_BATCHING, "0")
    new_renderer()
    assert os.environ[render.ENV_RENDER_BATCHING] == "0"


def test_the_hints_are_set_before_the_renderer_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    """O SDL le os dois hints na criacao do renderizador: defini-los depois nao teria
    efeito nenhum, e o teste que so olha o ambiente no fim nao veria a diferenca."""
    monkeypatch.delenv(render.ENV_SCALE_QUALITY, raising=False)
    monkeypatch.delenv(render.ENV_RENDER_BATCHING, raising=False)
    seen: list[tuple[str | None, str | None]] = []

    real = render.video.Renderer

    def spy(window, **kwargs):
        seen.append((os.environ.get(render.ENV_SCALE_QUALITY), os.environ.get(render.ENV_RENDER_BATCHING)))
        return real(window, **kwargs)

    monkeypatch.setattr(render.video, "Renderer", spy)
    renderer = render.create(CANVAS, WINDOW)
    try:
        assert seen, "ancora: o caminho de GPU foi mesmo tentado neste ambiente"
        assert seen[0] == ("0", "1")
    finally:
        if isinstance(renderer, render.GpuRenderer):
            renderer.window.destroy()


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


# --- conversao para o formato do display (R27.4) --------------------------------


def _no_display_format() -> None:
    """Deixa o processo sem formato de display, como no inicio de cada teste.

    E a condicao real do caminho de GPU, que nunca chama `display.set_mode` porque a
    janela vem do `_sdl2`."""
    pygame.display.quit()
    pygame.display.init()


def _spy_on_conversion(monkeypatch: pytest.MonkeyPatch, module) -> list[pygame.Surface]:
    """Anota o que `render.convert` devolveu dentro de `module`, sem trocar o que ele faz.

    A conversao continua sendo a de verdade; o espiao so registra o resultado, para
    que o teste possa afirmar que a superficie entregue e exatamente a que passou por
    ela — sob o driver `dummy` o formato do display coincide com o formato padrao do
    pygame, entao comparar mascaras nao distinguiria uma superficie convertida de uma
    que nunca passou pela conversao."""
    produced: list[pygame.Surface] = []

    def spy(surface: pygame.Surface) -> pygame.Surface:
        result = render.convert(surface)
        produced.append(result)
        return result

    monkeypatch.setattr(module, "convert", spy)
    return produced


def test_opaque_surface_is_converted_to_the_display_format() -> None:
    """O caso comum: um bloco sem transparencia vira uma superficie do formato do display."""
    display = pygame.display.set_mode(WINDOW)
    tile = pygame.Surface((8, 8))
    tile.fill((10, 120, 200))

    converted = render.convert(tile)

    assert converted is not tile  # `convert()` sempre devolve uma superficie nova
    assert converted.get_bitsize() == display.get_bitsize()
    assert converted.get_masks() == display.get_masks()
    assert converted.get_at((0, 0))[:3] == (10, 120, 200)


def test_conversion_of_an_opaque_surface_does_not_add_an_alpha_channel() -> None:
    """`convert_alpha()` numa superficie opaca a mandaria para o caminho de mistura
    a cada blit, sem nada para misturar — e o custo que a conversao existe para evitar."""
    pygame.display.set_mode(WINDOW)
    assert not render.convert(pygame.Surface((8, 8))).get_flags() & pygame.SRCALPHA


def test_conversion_keeps_per_pixel_transparency() -> None:
    """O outro lado: `convert()` numa superficie SRCALPHA apagaria o alfa por pixel —
    as asas da abelha e o vazado dos glifos virariam retangulos opacos."""
    pygame.display.set_mode(WINDOW)
    sprite = pygame.Surface((8, 8), pygame.SRCALPHA)
    sprite.set_at((4, 4), (240, 200, 30, 255))

    converted = render.convert(sprite)

    assert converted is not sprite
    assert converted.get_flags() & pygame.SRCALPHA
    assert converted.get_at((4, 4)) == (240, 200, 30, 255)
    assert converted.get_at((0, 0))[3] == 0  # o resto continua vazado


def test_conversion_without_a_display_returns_the_original_surface() -> None:
    """Sem formato de display a conversao levanta `pygame.error`; a superficie
    original serve, so mais lenta — nunca vale impedir o jogo de abrir por causa de
    uma otimizacao (R26.3)."""
    _no_display_format()
    tile = pygame.Surface((8, 8))
    assert render.convert(tile) is tile


def test_the_surface_path_converts_what_it_turns_into_an_image() -> None:
    """Neste caminho a imagem *e* uma `Surface`, e cada desenho dela e um blit."""
    renderer = render.SurfaceRenderer(CANVAS, WINDOW)
    tile = pygame.Surface((8, 8))
    assert renderer.make_image(tile).raw is not tile


def test_every_generated_texture_is_converted(monkeypatch: pytest.MonkeyPatch) -> None:
    """As texturas base sao as superficies mais reusadas do jogo (R27.4)."""
    pygame.display.set_mode(WINDOW)
    produced = _spy_on_conversion(monkeypatch, textures)

    generated = textures.generate_all(BLOCK)

    assert len(generated) == 8
    assert {id(surf) for surf in generated.values()} == {id(surf) for surf in produced}


def test_the_bee_texture_survives_the_conversion_with_its_transparency() -> None:
    """A unica textura com alfa por pixel: converte-la pelo caminho errado encheria
    de amarelo o fundo do sprite que `Bird.draw` rotaciona (R7.2)."""
    pygame.display.set_mode(WINDOW)
    bee = textures.generate_all(BLOCK)["bee_0"]
    assert bee.get_flags() & pygame.SRCALPHA
    assert bee.get_at((0, 0))[3] == 0  # o canto continua vazado


def test_the_font_cache_is_filled_with_converted_surfaces(monkeypatch: pytest.MonkeyPatch) -> None:
    """A conversao acontece ao preencher o cache, uma vez por (texto, escala, cor)."""
    pygame.display.set_mode(WINDOW)
    pixelfont._cache.clear()
    produced = _spy_on_conversion(monkeypatch, pixelfont)

    surface = pixelfont.render("SCORE 1", 2, (255, 255, 255))

    assert produced == [surface]
    assert pixelfont.render("SCORE 1", 2, (255, 255, 255)) is surface
    assert len(produced) == 1  # a chamada seguinte veio do cache, sem converter de novo
    assert surface.get_flags() & pygame.SRCALPHA  # o vazado dos glifos sobreviveu


def test_textures_and_text_are_still_produced_without_a_display() -> None:
    """Condicao real, e nao hipotetica: e assim que a suite roda sob o driver
    `dummy` antes de qualquer `set_mode`, e assim que o caminho de GPU roda sempre."""
    _no_display_format()
    pixelfont._cache.clear()

    generated = textures.generate_all(BLOCK)
    text = pixelfont.render("GAME OVER", 2, (255, 255, 255))

    assert generated["dirt"].get_size() == (BLOCK, BLOCK)
    assert text.get_height() == pixelfont.GLYPH_H * 2


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
