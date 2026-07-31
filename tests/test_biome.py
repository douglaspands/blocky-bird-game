import pygame

from src.biome import BANNER_FRAMES, BIOMES, FADE_FRAMES, BiomeManager
from tests.fakes import FakeRenderer


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


def test_draw_background_covers_a_canvas_larger_than_the_play_area():
    """No Android o canvas real pode ser maior que a area jogavel 480x720 (R14.3) —
    o gradiente de ceu precisa cobrir o canvas inteiro, nao so a base."""
    renderer = FakeRenderer((480, 1067))
    BiomeManager().draw_background(renderer)
    ((key, rect),) = renderer.draws
    assert key == ("sky", "overworld", 480, 1067)
    assert rect == pygame.Rect(0, 0, 480, 1067)


def test_draw_background_rebuilds_the_gradient_when_the_canvas_changes_size():
    """Trocar o canvas entre frames (redimensionamento, R23.6) nao pode reaproveitar
    o gradiente do tamanho antigo — a chave inclui o tamanho justamente por isso."""
    renderer = FakeRenderer((480, 720))
    bm = BiomeManager()
    bm.draw_background(renderer)
    renderer.resize((480, 1067))
    bm.draw_background(renderer)

    keys = [key for key, _ in renderer.draws]
    assert keys == [("sky", "overworld", 480, 720), ("sky", "overworld", 480, 1067)]
    assert renderer.draws[-1][1].height == 1067


def test_the_biome_fade_uses_image_alpha():
    """O fade cruzado (R5.4) desenha o bioma anterior opaco e o novo por cima, com o
    alfa subindo — no caminho de GPU isso e uma propriedade da textura, nao pixels."""
    renderer = FakeRenderer((480, 720))
    bm = BiomeManager()
    bm.update(BIOMES[1].threshold)
    assert bm.fade_timer == FADE_FRAMES

    bm.draw_background(renderer)
    previous, current = renderer.draws
    assert previous[0] == ("sky", "overworld", 480, 720)
    assert current[0] == ("sky", "cave", 480, 720)
    assert renderer._images[previous[0]].alpha == 255
    assert renderer._images[current[0]].alpha == 0  # o novo ainda nao apareceu
