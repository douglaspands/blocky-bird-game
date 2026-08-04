"""Definicoes de bioma e gerenciador de transicao (R5, R2.5, R7.3)."""

from dataclasses import dataclass

import pygame

from src import config, render, ui

FADE_FRAMES = 60  # <= 1s a 60 FPS (R5.4)
BANNER_FRAMES = 90


@dataclass(frozen=True)
class Biome:
    """Parametros de um bioma: threshold de ativacao, velocidade, texturas e ceu."""

    id: str
    name: str
    threshold: int
    speed: float
    gap_size: int
    sky_top: tuple[int, int, int]
    sky_bottom: tuple[int, int, int]
    block_main: str
    block_edge: str
    decor: str


BIOMES: list[Biome] = [
    Biome(
        "overworld",
        "Overworld",
        0,
        2.5,
        160,
        (135, 206, 235),
        (200, 230, 245),
        "dirt",
        "grass_side",
        "overworld",
    ),
    Biome(
        "cave",
        "Cave",
        10,
        3.0,
        145,
        (25, 25, 35),
        (60, 58, 70),
        "stone",
        "cobblestone",
        "cave",
    ),
    Biome(
        "nether",
        "Nether",
        25,
        3.3,
        140,
        (80, 15, 10),
        (150, 60, 20),
        "netherrack",
        "obsidian",
        "nether",
    ),
]


def _lerp_color(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    r, g, b = (round(x + (y - x) * t) for x, y in zip(c1, c2, strict=True))
    return (r, g, b)


def _make_gradient(
    top: tuple[int, int, int], bottom: tuple[int, int, int], width: int, height: int
) -> pygame.Surface:
    surf = pygame.Surface((width, height))
    for y in range(height):
        t = y / max(height - 1, 1)
        pygame.draw.line(surf, _lerp_color(top, bottom, t), (0, y), (width, y))
    return surf


def _biome_for_score(score: int) -> Biome:
    active = BIOMES[0]
    for biome in BIOMES:
        if score >= biome.threshold:
            active = biome
    return active


class BiomeManager:
    """Acompanha o bioma ativo e as transicoes de fade/banner conforme o score."""

    def __init__(self) -> None:
        """Inicia no primeiro bioma (Overworld), sem fade nem banner em curso."""
        self.current = BIOMES[0]
        self.previous = BIOMES[0]
        self.fade_timer = 0
        self.banner_timer = 0

    def update(self, score: int) -> bool:
        """Detecta cruzamento de threshold (R5.1) e ativa fade + banner (R5.4).

        Retorna True se houve transicao.
        """
        target = _biome_for_score(score)
        if target.id != self.current.id:
            self.previous = self.current
            self.current = target
            self.fade_timer = FADE_FRAMES
            self.banner_timer = BANNER_FRAMES
            return True
        self.fade_timer = max(0, self.fade_timer - 1)
        self.banner_timer = max(0, self.banner_timer - 1)
        return False

    def _gradient(self, renderer: render.Renderer, biome: Biome) -> render.Image:
        """Gradiente de ceu do bioma, construido uma vez por tamanho de canvas (R14.3).

        A chave inclui o tamanho porque o canvas real so e conhecido em runtime e pode
        mudar num redimensionamento (R23.6).
        """
        width, height = renderer.size
        return renderer.image(
            ("sky", biome.id, width, height),
            lambda: _make_gradient(biome.sky_top, biome.sky_bottom, width, height),
        )

    def draw_background(self, renderer: render.Renderer) -> None:
        """Desenha o ceu do bioma atual, cruzando com o anterior durante o fade."""
        current_grad = self._gradient(renderer, self.current)
        if self.fade_timer > 0:
            prev_grad = self._gradient(renderer, self.previous)
            prev_grad.alpha = 255
            renderer.draw(prev_grad, (0, 0))
            current_grad.alpha = round(255 * (1 - self.fade_timer / FADE_FRAMES))
            renderer.draw(current_grad, (0, 0))
        else:
            current_grad.alpha = 255
            renderer.draw(current_grad, (0, 0))

    def draw_banner(self, renderer: render.Renderer) -> None:
        """Desenha o nome do bioma no topo da area jogavel enquanto o banner dura."""
        if self.banner_timer > 0:
            play = config.play()
            ui.draw_text(renderer, self.current.name.upper(), (play.centerx, play.top + 110), base_size=16)
