import pygame

from src.biome import BANNER_FRAMES, FADE_FRAMES, BiomeManager


def test_starts_on_overworld():
    bm = BiomeManager()
    assert bm.current.id == "overworld"
    assert bm.fade_timer == 0
    assert bm.banner_timer == 0


def test_no_transition_below_threshold():
    bm = BiomeManager()
    for score in (0, 5, 9):
        transitioned = bm.update(score)
        assert transitioned is False
        assert bm.current.id == "overworld"


def test_threshold_10_activates_cave():
    bm = BiomeManager()
    transitioned = bm.update(10)
    assert transitioned is True
    assert bm.current.id == "cave"
    assert bm.fade_timer == FADE_FRAMES
    assert bm.banner_timer == BANNER_FRAMES


def test_threshold_25_activates_nether():
    bm = BiomeManager()
    bm.update(10)
    transitioned = bm.update(25)
    assert transitioned is True
    assert bm.current.id == "nether"


def test_staying_in_same_biome_decrements_timers():
    bm = BiomeManager()
    bm.update(10)
    assert bm.fade_timer == FADE_FRAMES
    bm.update(10)
    assert bm.fade_timer == FADE_FRAMES - 1
    assert bm.banner_timer == BANNER_FRAMES - 1


def test_timers_do_not_go_below_zero():
    bm = BiomeManager()
    bm.update(10)
    for _ in range(FADE_FRAMES + BANNER_FRAMES + 10):
        bm.update(10)
    assert bm.fade_timer == 0
    assert bm.banner_timer == 0


def test_score_jumping_straight_to_nether_activates_nether_directly():
    bm = BiomeManager()
    transitioned = bm.update(30)
    assert transitioned is True
    assert bm.current.id == "nether"


def test_draw_background_fills_canvas_larger_than_base_area():
    """No Android o canvas real pode ser maior que a area jogavel 480x720 (R14.3) —
    o gradiente de ceu precisa cobrir a surface inteira recebida, nao so a base."""
    bm = BiomeManager()
    surface = pygame.Surface((480, 1067))
    bm.draw_background(surface)  # nao deve lancar excecao nem deixar area sem desenhar
    assert surface.get_at((0, 0))[:3] != (0, 0, 0)
    assert surface.get_at((0, 1066))[:3] != (0, 0, 0)


def test_draw_background_regenerates_gradient_on_canvas_size_change():
    """Trocar o tamanho da surface entre chamadas (ex.: Game reconstruido com
    outro canvas) nao deve deixar gradiente cacheado do tamanho antigo."""
    bm = BiomeManager()
    small = pygame.Surface((480, 720))
    bm.draw_background(small)
    big = pygame.Surface((480, 1067))
    bm.draw_background(big)  # nao deve lancar (ex.: blit de surface menor numa maior)
    assert big.get_at((0, 1066))[:3] != (0, 0, 0)
