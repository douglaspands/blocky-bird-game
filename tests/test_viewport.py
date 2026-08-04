"""Canvas logico com a proporcao da tela e area jogavel fixa (R23, R24)."""

import pytest

from src import config, viewport
from src.viewport import MAX_GROUND_EXTRA, PLAY_H, PLAY_W, compute

# (nome, tela real, canvas esperado, ceu extra, chao extra) — a tabela da secao 32.3
SCREENS = [
    ("celular 20:9", (1080, 2400), (480, 1067), 251, 96),
    ("celular 16:9", (1080, 1920), (480, 853), 37, 96),
    ("janela padrao do desktop", (960, 720), (960, 720), 0, 0),
    ("monitor 16:9 maximizado", (1920, 1080), (1280, 720), 0, 0),
    ("exatamente 2:3", (480, 720), (480, 720), 0, 0),
]

IDS = [name for name, *_ in SCREENS]


@pytest.mark.parametrize(("screen", "canvas", "sky_extra", "ground_extra"), [s[1:] for s in SCREENS], ids=IDS)
def test_canvas_matches_the_design_table(screen, canvas, sky_extra, ground_extra):
    vp = compute(*screen)
    assert vp.canvas == canvas
    assert vp.sky_extra == sky_extra
    assert vp.ground_extra == ground_extra


@pytest.mark.parametrize("screen", [s[1] for s in SCREENS], ids=IDS)
def test_play_area_is_always_the_same_world_column(screen):
    """A dificuldade nao pode depender da tela: a area jogavel e sempre 480x720 de
    mundo, em qualquer proporcao (R24.1)."""
    assert compute(*screen).play.size == (PLAY_W, PLAY_H)


@pytest.mark.parametrize("screen", [s[1] for s in SCREENS], ids=IDS)
def test_canvas_never_shrinks_below_the_play_area(screen):
    vp = compute(*screen)
    assert vp.width >= PLAY_W
    assert vp.height >= PLAY_H


@pytest.mark.parametrize("screen", [s[1] for s in SCREENS], ids=IDS)
def test_canvas_keeps_the_real_aspect_ratio(screen):
    """A proporcao do canvas bate com a da tela (a menos do arredondamento para
    pixel inteiro), que e o que faz a escala final ser uniforme e nao sobrar barra
    em lado nenhum (R23.1, R23.2, R23.4)."""
    vp = compute(*screen)
    assert vp.width / vp.height == pytest.approx(screen[0] / screen[1], abs=0.002)


@pytest.mark.parametrize("screen", [s[1] for s in SCREENS], ids=IDS)
def test_bands_tile_the_canvas_without_losing_a_pixel(screen):
    """As faixas fecham exatamente com o canvas nos dois eixos — inclusive quando a
    sobra horizontal e impar, caso em que a faixa direita fica 1px mais larga."""
    vp = compute(*screen)
    assert vp.left_band.width + vp.play.width + vp.right_band.width == vp.width
    assert vp.sky_band.height + vp.play.height + vp.ground_band.height == vp.height
    assert vp.left_band.right == vp.play.left
    assert vp.right_band.right == vp.width
    assert vp.sky_band.bottom == vp.play.top
    assert vp.ground_band.bottom == vp.height


def test_odd_horizontal_leftover_goes_to_the_right_band():
    vp = compute(961, 720)
    assert vp.width == 961
    assert vp.left_band.width == 240
    assert vp.right_band.width == 241


def test_vertical_leftover_fills_the_ground_first_then_the_sky():
    """Ate 2 fileiras de bloco viram chao; o excedente vai para o ceu, que absorve
    altura sem parecer estranho (R25.1)."""
    vp = compute(480, 760)  # sobra 40px, menos que o teto do chao
    assert (vp.ground_extra, vp.sky_extra) == (40, 0)

    vp = compute(480, 900)  # sobra 180px: 96 de chao, 84 de ceu
    assert (vp.ground_extra, vp.sky_extra) == (MAX_GROUND_EXTRA, 84)


def test_square_screen_only_grows_horizontally():
    vp = compute(720, 720)
    assert vp.canvas == (720, 720)
    assert (vp.sky_extra, vp.ground_extra) == (0, 0)
    assert vp.left_band.width == 120


def test_invalid_screen_size_falls_back_to_the_play_area():
    """Um numero estranho nunca deve impedir o jogo de abrir (mesma disciplina de
    `scale.fit_scale`)."""
    assert compute(0, 0).canvas == (PLAY_W, PLAY_H)
    assert compute(-1920, 1080).canvas == (PLAY_W, PLAY_H)


def test_compute_is_idempotent_over_its_own_canvas():
    """Sustenta o `BLOCKY_CANVAS`: forcar o tamanho de tela equivale a forcar o
    canvas."""
    for _, screen, *_ in SCREENS:
        canvas = compute(*screen).canvas
        assert compute(*canvas).canvas == canvas


def test_forced_canvas_env_var(monkeypatch):
    monkeypatch.setenv(viewport.ENV_CANVAS, "480x1067")
    assert viewport.forced_size() == (480, 1067)
    assert viewport.screen_size() == (480, 1067)


@pytest.mark.parametrize("raw", ["", "480", "480x", "axb", "480x0", "-480x720", "480x720x9"])
def test_malformed_canvas_env_var_is_ignored(monkeypatch, raw):
    """Ferramenta de desenvolvimento: valor invalido cai no padrao em silencio."""
    monkeypatch.setenv(viewport.ENV_CANVAS, raw)
    assert viewport.forced_size() is None
    assert viewport.screen_size() == viewport.DESKTOP_WINDOW


def test_desktop_screen_size_is_wider_than_the_play_area(monkeypatch):
    """A janela padrao abre mais larga que a area jogavel, para as faixas laterais
    ficarem visiveis sem o jogador redimensionar nada (R23.7)."""
    monkeypatch.delenv(viewport.ENV_CANVAS, raising=False)
    monkeypatch.setattr("src.viewport.is_android", lambda: False)
    assert viewport.screen_size() == viewport.DESKTOP_WINDOW
    assert compute(*viewport.screen_size()).left_band.width > 0


def test_android_screen_size_is_the_native_resolution(monkeypatch):
    monkeypatch.delenv(viewport.ENV_CANVAS, raising=False)
    monkeypatch.setattr("src.viewport.is_android", lambda: True)
    monkeypatch.setattr("pygame.display.get_desktop_sizes", lambda: [(1080, 2400)])
    assert viewport.screen_size() == (1080, 2400)


def test_config_resolves_dimensions_from_the_active_viewport():
    """`config.screen_w`/`screen_h` deixaram de ser constantes de modulo: passam a
    responder ao viewport ativo, no mesmo padrao de `config.ground_y()`."""
    config.set_viewport(compute(1920, 1080))
    assert (config.screen_w(), config.screen_h()) == (1280, 720)

    config.set_viewport(compute(PLAY_W, PLAY_H))
    assert (config.screen_w(), config.screen_h()) == (PLAY_W, PLAY_H)
