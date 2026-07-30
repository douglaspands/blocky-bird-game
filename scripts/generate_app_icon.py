"""Gera o icone do app (a abelha do jogo, R21) por codigo, reaproveitando
textures.make_bee — sem imagem externa nem dependencia de Pillow.

Gera em assets/:
  app_icon_512.png            icone da janela do desktop + fonte do .ico
  app_icon.ico                multi-resolucao (16-256px) para o .exe do PyInstaller
  android_icon_legacy.png     icone Android para API < 26 (sem icone adaptativo)
  android_icon_foreground.png camada de primeiro plano do icone adaptativo (Android 8+)
  android_icon_background.png camada de fundo do icone adaptativo (Android 8+)

Ver specs/v3/design.md secao 29.
"""

import io
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame

pygame.init()

from src import textures  # noqa: E402
from src.biome import BIOMES  # noqa: E402

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

ICON_SIZE = 512
ADAPTIVE_CANVAS = 432
SAFE_ZONE_FRACTION = 66 / 108  # zona segura do icone adaptativo Android (R21.5)
ICO_SIZES = [16, 32, 48, 64, 128, 256]

SKY_TOP, SKY_BOTTOM = BIOMES[0].sky_top, BIOMES[0].sky_bottom
GRASS = (95, 159, 53)
DIRT = (134, 96, 67)


def _vertical_gradient(
    surface: pygame.Surface, top: tuple[int, int, int], bottom: tuple[int, int, int]
) -> None:
    h = surface.get_height()
    for y in range(h):
        t = y / max(h - 1, 1)
        color = tuple(round(a + (b - a) * t) for a, b in zip(top, bottom, strict=True))
        pygame.draw.line(surface, color, (0, y), (surface.get_width(), y))


def _scale_nearest_fit(surface: pygame.Surface, max_side: int) -> pygame.Surface:
    """Escala mantendo a proporcao ate o maior lado caber em max_side, sem suavizar
    (vizinho-mais-proximo, mesma tecnica de textures.scale_pixel_perfect — R7.1)."""
    w, h = surface.get_size()
    scale = max_side / max(w, h)
    new_size = (max(1, round(w * scale)), max(1, round(h * scale)))
    return pygame.transform.scale(surface, new_size)


def make_background_layer(size: int) -> pygame.Surface:
    """Camada de fundo: gradiente de ceu do Overworld, opaca, sem a abelha (R21.4)."""
    surf = pygame.Surface((size, size))
    _vertical_gradient(surf, SKY_TOP, SKY_BOTTOM)
    return surf


def make_foreground_layer(size: int = ADAPTIVE_CANVAS) -> pygame.Surface:
    """Camada de primeiro plano: so a abelha, dentro da zona segura de mascara (R21.5)."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    max_side = int(size * SAFE_ZONE_FRACTION)
    bee = _scale_nearest_fit(textures.make_bee(0), max_side)
    surf.blit(bee, bee.get_rect(center=(size // 2, size // 2)))
    return surf


def make_composed_icon(size: int = ICON_SIZE) -> pygame.Surface:
    """Icone 'terminado' (fundo + abelha), usado onde nao ha mascara de sistema:
    janela do desktop, .exe do Windows, icone legado do Android (R21.6)."""
    surf = pygame.Surface((size, size))
    _vertical_gradient(surf, SKY_TOP, SKY_BOTTOM)

    ground_h = round(size * 0.16)
    ground_top = size - ground_h
    grass_h = max(1, round(ground_h * 0.25))
    pygame.draw.rect(surf, GRASS, (0, ground_top, size, grass_h))
    pygame.draw.rect(surf, DIRT, (0, ground_top + grass_h, size, ground_h - grass_h))

    bee = _scale_nearest_fit(textures.make_bee(0), round(size * 0.62))
    bee_rect = bee.get_rect(center=(size // 2, round(size * 0.44)))
    surf.blit(bee, bee_rect)
    return surf


def _encode_png(surface: pygame.Surface) -> bytes:
    buf = io.BytesIO()
    pygame.image.save(surface, buf, "icon.png")
    return buf.getvalue()


def build_ico(source: pygame.Surface, out_path: Path, sizes: list[int] = ICO_SIZES) -> None:
    """Monta um .ico multi-resolucao so com pygame + struct (sem Pillow, R9.2).

    O formato ICO moderno (Vista+) aceita cada entrada como um PNG completo em
    vez de um bitmap cru — o que torna isso viavel sem lib externa de imagem.
    """
    entries = [(size, _encode_png(pygame.transform.smoothscale(source, (size, size)))) for size in sizes]

    header = struct.pack("<HHH", 0, 1, len(entries))  # ICONDIR: reservado, tipo=1 (icone), contagem
    dir_entries = b""
    image_data = b""
    offset = len(header) + len(entries) * 16  # cada ICONDIRENTRY tem 16 bytes
    for size, png_bytes in entries:
        wh = 0 if size >= 256 else size  # 0 significa 256 no formato ICO
        dir_entries += struct.pack("<BBBBHHII", wh, wh, 0, 0, 1, 32, len(png_bytes), offset)
        image_data += png_bytes
        offset += len(png_bytes)

    out_path.write_bytes(header + dir_entries + image_data)


def main() -> None:
    ASSETS_DIR.mkdir(exist_ok=True)

    composed = make_composed_icon(ICON_SIZE)
    pygame.image.save(composed, str(ASSETS_DIR / "app_icon_512.png"))
    pygame.image.save(composed, str(ASSETS_DIR / "android_icon_legacy.png"))
    build_ico(composed, ASSETS_DIR / "app_icon.ico")

    pygame.image.save(make_foreground_layer(), str(ASSETS_DIR / "android_icon_foreground.png"))
    pygame.image.save(make_background_layer(ADAPTIVE_CANVAS), str(ASSETS_DIR / "android_icon_background.png"))

    print(f"icones salvos em {ASSETS_DIR}")


if __name__ == "__main__":
    main()
