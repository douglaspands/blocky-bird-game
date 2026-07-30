from src.screen_adapt import adapted_canvas_size

BASE_W, BASE_H = 480, 720


def test_device_narrower_than_base_extends_height():
    """Celular alongado (ex.: Galaxy S20 FE, 1080x2400) sobraria barra em cima/baixo
    com o canvas base — estica a altura ate a proporcao bater, largura intocada."""
    w, h = adapted_canvas_size(BASE_W, BASE_H, 1080, 2400)
    assert w == BASE_W
    assert h > BASE_H
    assert abs(w / h - 1080 / 2400) < 1e-3


def test_device_wider_than_base_extends_width():
    """Android TV 16:9 em paisagem sobraria pillarbox com o canvas base — estica a
    largura ate a proporcao bater, altura intocada."""
    w, h = adapted_canvas_size(BASE_W, BASE_H, 1920, 1080)
    assert h == BASE_H
    assert w > BASE_W
    assert abs(w / h - 1920 / 1080) < 1e-3


def test_device_matching_base_aspect_is_unchanged():
    w, h = adapted_canvas_size(BASE_W, BASE_H, 960, 1440)
    assert (w, h) == (BASE_W, BASE_H)


def test_invalid_device_size_falls_back_to_base():
    assert adapted_canvas_size(BASE_W, BASE_H, 0, 2400) == (BASE_W, BASE_H)
    assert adapted_canvas_size(BASE_W, BASE_H, 1080, 0) == (BASE_W, BASE_H)
    assert adapted_canvas_size(BASE_W, BASE_H, -1, 2400) == (BASE_W, BASE_H)


def test_extended_canvas_never_shrinks_base():
    """A area jogavel 480x720 precisa sempre caber dentro do canvas (subsurface
    centralizada/ancorada no chao em game.py) — nenhum eixo pode ficar menor que a
    base, so igual ou maior."""
    for device_w, device_h in [(1080, 2400), (1920, 1080), (1600, 1200), (1080, 1920)]:
        w, h = adapted_canvas_size(BASE_W, BASE_H, device_w, device_h)
        assert w >= BASE_W
        assert h >= BASE_H
