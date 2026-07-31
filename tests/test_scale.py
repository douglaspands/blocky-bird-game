from src.scale import fit_scale

BASE_W, BASE_H = 480, 720


def test_matching_aspect_gives_scale_one_no_offset():
    assert fit_scale(BASE_W, BASE_H, BASE_W, BASE_H) == (1.0, 0.0, 0.0)


def test_wider_window_scales_by_height_and_letterboxes_width():
    """Android TV 16:9 (1920x1080): mais largo que a base — a escala e ditada
    pela altura, e o excedente horizontal sobra como pillarbox (offset_x > 0)."""
    scale, off_x, off_y = fit_scale(BASE_W, BASE_H, 1920, 1080)
    assert scale == 1080 / BASE_H
    assert off_y == 0
    assert off_x > 0


def test_taller_window_scales_by_width_and_letterboxes_height():
    """Celular alongado (1080x2400): mais estreito que a base — a escala e
    ditada pela largura, e o excedente vertical sobra como letterbox (offset_y > 0)."""
    scale, off_x, off_y = fit_scale(BASE_W, BASE_H, 1080, 2400)
    assert scale == 1080 / BASE_W
    assert off_x == 0
    assert off_y > 0


def test_scaled_canvas_never_exceeds_window():
    """Para qualquer proporcao de janela, o canvas escalado cabe inteiro dentro
    da janela (o requisito central do letterbox: nunca corta a imagem)."""
    for window_w, window_h in [(1920, 1080), (1080, 2400), (1600, 1200), (900, 720), (300, 900)]:
        scale, off_x, off_y = fit_scale(BASE_W, BASE_H, window_w, window_h)
        assert BASE_W * scale <= window_w + 1e-6
        assert BASE_H * scale <= window_h + 1e-6
        assert off_x >= -1e-6
        assert off_y >= -1e-6


def test_invalid_size_falls_back_to_identity():
    assert fit_scale(BASE_W, BASE_H, 0, 720) == (1.0, 0.0, 0.0)
    assert fit_scale(BASE_W, BASE_H, 480, -1) == (1.0, 0.0, 0.0)
    assert fit_scale(0, BASE_H, 480, 720) == (1.0, 0.0, 0.0)
