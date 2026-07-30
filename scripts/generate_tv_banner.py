"""Gera assets/android_banner.png (320x180): banner do Android TV (R17.3),
inteiramente por codigo, reaproveitando as texturas/fonte do jogo (R7.1)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame

pygame.init()

from src import pixelfont, textures  # noqa: E402

W, H = 320, 180
SKY_TOP = (135, 206, 235)
SKY_BOTTOM = (200, 230, 245)
GRASS = (95, 159, 53)
DIRT = (134, 96, 67)


def _vertical_gradient(surface: pygame.Surface, top, bottom) -> None:
    h = surface.get_height()
    for y in range(h):
        t = y / max(h - 1, 1)
        color = tuple(round(a + (b - a) * t) for a, b in zip(top, bottom))
        pygame.draw.line(surface, color, (0, y), (surface.get_width(), y))


def main() -> None:
    surf = pygame.Surface((W, H))
    _vertical_gradient(surf, SKY_TOP, SKY_BOTTOM)

    ground_top = H - 22
    pygame.draw.rect(surf, GRASS, (0, ground_top, W, 6))
    pygame.draw.rect(surf, DIRT, (0, ground_top + 6, W, H - ground_top - 6))

    bee = textures.make_bee(0)
    bee = pygame.transform.scale(bee, (56, 56))
    surf.blit(bee, (18, H // 2 - 20))

    center = (W // 2 + 30, H // 2 - 6)
    shadow = pixelfont.render("BLOCKY", 3, (40, 30, 20))
    surf.blit(shadow, shadow.get_rect(center=(center[0] + 2, center[1] + 2)))
    title = pixelfont.render("BLOCKY", 3, (255, 220, 60))
    surf.blit(title, title.get_rect(center=center))

    center2 = (W // 2 + 30, H // 2 + 22)
    shadow2 = pixelfont.render("BIRD", 3, (40, 30, 20))
    surf.blit(shadow2, shadow2.get_rect(center=(center2[0] + 2, center2[1] + 2)))
    title2 = pixelfont.render("BIRD", 3, (255, 220, 60))
    surf.blit(title2, title2.get_rect(center=center2))

    out_path = Path(__file__).resolve().parent.parent / "assets" / "android_banner.png"
    out_path.parent.mkdir(exist_ok=True)
    pygame.image.save(surf, str(out_path))
    print(f"banner salvo em {out_path} ({W}x{H})")


if __name__ == "__main__":
    main()
