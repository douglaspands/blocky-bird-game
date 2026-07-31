import importlib.util
import struct
from pathlib import Path

import pygame

_SPEC = importlib.util.spec_from_file_location(
    "generate_app_icon", Path(__file__).resolve().parent.parent / "scripts" / "generate_app_icon.py"
)
assert _SPEC is not None and _SPEC.loader is not None
icon_gen = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(icon_gen)


def test_foreground_bee_fits_within_safe_zone():
    fg = icon_gen.make_foreground_layer(icon_gen.ADAPTIVE_CANVAS)

    max_side = icon_gen.ADAPTIVE_CANVAS * icon_gen.SAFE_ZONE_FRACTION
    opaque = pygame.mask.from_surface(fg)
    rect = opaque.get_bounding_rects()[0] if opaque.count() else pygame.Rect(0, 0, 0, 0)

    assert rect.width <= max_side + 1
    assert rect.height <= max_side + 1


def test_background_layer_has_no_alpha_channel():
    bg = icon_gen.make_background_layer(icon_gen.ADAPTIVE_CANVAS)

    assert bg.get_size() == (icon_gen.ADAPTIVE_CANVAS, icon_gen.ADAPTIVE_CANVAS)
    assert not bg.get_flags() & pygame.SRCALPHA


def test_composed_icon_has_requested_size():
    composed = icon_gen.make_composed_icon(256)

    assert composed.get_size() == (256, 256)


def test_build_ico_contains_all_sizes_and_round_trips(tmp_path):
    source = icon_gen.make_composed_icon(icon_gen.ICON_SIZE)
    out_path = tmp_path / "icon.ico"

    icon_gen.build_ico(source, out_path, sizes=[16, 32, 256])

    data = out_path.read_bytes()
    reserved, ico_type, count = struct.unpack_from("<HHH", data, 0)
    assert (reserved, ico_type, count) == (0, 1, 3)

    for i, expected_size in enumerate([16, 32, 256]):
        width, height, _, _, _, _, size_bytes, offset = struct.unpack_from("<BBBBHHII", data, 6 + i * 16)
        decoded_side = 256 if width == 0 else width
        assert decoded_side == expected_size
        assert height == width

        png_bytes = data[offset : offset + size_bytes]
        import io

        decoded = pygame.image.load(io.BytesIO(png_bytes), "icon.png")
        assert decoded.get_size() == (expected_size, expected_size)
