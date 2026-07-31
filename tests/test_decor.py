import pygame

from src import config
from src.decor import DecorManager
from src.viewport import compute


def test_draw_tiles_across_a_canvas_wider_than_base_area():
    """No Android TV o canvas real pode ser mais largo que a area jogavel 480px
    (R14.3) — o parallax precisa ladrilhar ate a largura real da surface, nao so
    ate os 480px base, senao sobraria barra preta na extensao."""
    dm = DecorManager()
    surface = pygame.Surface((1280, 720))
    dm.draw(surface, "overworld")  # nao deve lancar; cobre decor.py::_tile e os drawers

    surface_stone = pygame.Surface((1280, 720))
    dm.draw(surface_stone, "cave")
    surface_nether = pygame.Surface((1280, 720))
    dm.draw(surface_nether, "nether")


def test_draw_anchors_ground_relative_decor_to_the_play_area():
    """Hills/lava/pilares assentam na linha do chao da area jogavel, nao na base do
    canvas — senao afundariam na faixa decorativa de chao de um celular alongado
    (task 46, R25.1)."""
    config.set_viewport(compute(1080, 2400))
    dm = DecorManager()
    tall = pygame.Surface(config.viewport().canvas)
    assert config.ground_y() < tall.get_height() - 96  # ha faixa de chao abaixo
    dm.draw(tall, "overworld")  # nao deve lancar (ex.: y negativo instavel)
    dm.draw(tall, "nether")
