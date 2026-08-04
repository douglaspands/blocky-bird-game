"""Sprites da abelha pre-computados: 62 rotacoes na inicializacao (R27.2, R27.3).

A v2 chamava `pygame.transform.rotate` a cada frame, para reamostrar o mesmo sprite
no mesmo angulo que o frame anterior ja tinha usado — cada chamada aloca uma
superficie nova e refiltra 48x48 pixels. O conjunto de angulos alcancaveis sempre foi
finito e conhecido; a task 56 so torna isso explicito e paga o custo uma vez.
"""

import pygame
import pytest

from src import config, textures
from src.bird import ANGLES, MAX_ANGLE_DOWN, MAX_ANGLE_UP, Bird, precompute_sprites, quantize
from src.config import BLOCK
from src.game import Game
from src.viewport import PLAY_H, PLAY_W
from tests.fakes import FakeRenderer


@pytest.fixture
def tex() -> dict[str, pygame.Surface]:
    return textures.generate_all(BLOCK)


def _warm(tex: dict[str, pygame.Surface]) -> FakeRenderer:
    """Renderizador com as 62 texturas ja construidas, como apos `Game.__init__`."""
    renderer = FakeRenderer((PLAY_W, PLAY_H))
    precompute_sprites(renderer, tex)
    return renderer


def _full_flight(bird: Bird):
    """Tres subidas e quedas completas, uma de cada vez.

    A queda inteira importa: uma flapada so muda o angulo depois que `vel_y` fica
    positivo, o que leva 19 frames, e so entao a grade e percorrida de +30 a -60. Um
    padrao mais apertado que isso deixaria a abelha presa em +30 e o teste passaria
    sem exercitar quase nada."""
    for _ in range(3):
        bird.flap()
        for _ in range(60):
            bird.update()
            yield


# --- a grade de angulos, que a fisica ja produzia ---------------------------------


def test_the_angle_grid_has_thirty_one_values() -> None:
    """31 angulos x 2 frames de asa = as 62 texturas que o design previu."""
    assert len(ANGLES) == 31
    assert ANGLES[0] == MAX_ANGLE_DOWN
    assert ANGLES[-1] == MAX_ANGLE_UP


def test_the_physics_never_leaves_the_grid() -> None:
    """Ancora da grade: ela nao e uma aproximacao imposta ao movimento, e o conjunto
    exato de angulos que `flap` e `update` produzem. Se um dia deixar de ser, e aqui
    que se descobre — e nao por uma textura faltando na tela."""
    bird = Bird(100, 300)
    seen = {bird.angle}
    for _ in _full_flight(bird):
        seen.add(bird.angle)
    bird.update_idle()
    seen.add(bird.angle)
    assert seen <= set(ANGLES)
    assert len(seen) == len(ANGLES)  # e passou por todos os 31, nao por um punhado


# --- a quantizacao ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("angle", "expected"),
    [(0.0, 0), (13.0, 12), (14.0, 15), (-58.4, -57), (29.9, 30)],
)
def test_an_off_grid_angle_snaps_to_the_nearest_texture(angle: float, expected: int) -> None:
    assert quantize(angle) == expected
    assert expected in ANGLES


@pytest.mark.parametrize("angle", [100.0, 30.1, -100.0, -61.0])
def test_an_angle_beyond_the_grid_is_clamped_to_its_ends(angle: float) -> None:
    """Nem o arredondamento pode sair da grade: fora dela nao ha textura nenhuma."""
    assert quantize(angle) in (MAX_ANGLE_DOWN, MAX_ANGLE_UP)


def test_drawing_an_off_grid_angle_uses_the_neighbouring_texture(tex) -> None:
    """A quantizacao chega ate o desenho, e nao para na funcao."""
    renderer = _warm(tex)
    built = len(renderer._images)
    bird = Bird(100, 300)
    bird.angle = 13.0
    bird.draw(renderer, tex)

    assert renderer.draws[-1][0] == ("bee", 0, 12)
    assert len(renderer._images) == built  # nada de novo foi construido


# --- o ganho: nenhuma rotacao dentro do frame -------------------------------------


def test_precompute_builds_every_combination_once(tex) -> None:
    renderer = _warm(tex)
    assert len(renderer._images) == 62
    assert set(renderer._images) == {("bee", frame, angle) for frame in (0, 1) for angle in ANGLES}

    precompute_sprites(renderer, tex)  # de novo nao reconstroi nada
    assert len(renderer._images) == 62


def test_no_rotation_happens_while_drawing(tex, monkeypatch: pytest.MonkeyPatch) -> None:
    """O que a task 56 entrega, na sua forma mais direta."""
    renderer = _warm(tex)
    monkeypatch.setattr(pygame.transform, "rotate", _forbidden)

    bird = Bird(100, 300)
    drawn = 0
    for _ in _full_flight(bird):
        bird.draw(renderer, tex)
        drawn += 1
    assert len(renderer.draws) == drawn == 180


def _forbidden(*args: object, **kwargs: object) -> object:
    raise AssertionError("transform.rotate chamado durante o desenho")


def test_the_v2_way_rotated_on_every_frame(tex, monkeypatch: pytest.MonkeyPatch) -> None:
    """Ancora do teste acima: sem ela, "nenhuma rotacao" nao diria o que foi evitado.

    Reproducao do `Bird.draw` da v2 — sem cache, sem grade —, que reamostrava o sprite
    inteiro a cada frame para chegar ao mesmo resultado do frame anterior."""
    rotated: list[int] = []
    real = pygame.transform.rotate
    monkeypatch.setattr(pygame.transform, "rotate", lambda s, a: rotated.append(a) or real(s, a))

    bird = Bird(100, 300)
    for _ in _full_flight(bird):
        pygame.transform.rotate(tex[f"bee_{bird.frame}"], round(bird.angle))  # o `draw` da v2

    assert len(rotated) == 180  # um por frame desenhado
    assert len(set(rotated)) == len(ANGLES)  # para so 31 resultados distintos


def test_a_bird_frame_is_a_single_draw_call(tex) -> None:
    renderer = _warm(tex)
    renderer.calls.clear()
    Bird(100, 300).draw(renderer, tex)
    assert len(renderer.calls) == 1


def test_the_sprite_is_centred_on_the_bird_regardless_of_rotation(tex) -> None:
    """A textura rotacionada e maior que o sprite, e o que tem que continuar no lugar
    e o centro — senao a abelha se descolaria da propria hitbox ao inclinar."""
    renderer = _warm(tex)
    bird = Bird(100, 300)
    for angle in (MAX_ANGLE_UP, 0, MAX_ANGLE_DOWN):
        bird.angle = angle
        bird.draw(renderer, tex)
        _, rect = renderer.draws[-1]
        assert abs(rect.centerx - bird.rect.centerx) <= 1
        assert abs(rect.centery - bird.rect.centery) <= 1


# --- as texturas sobrevivem ao ciclo de vida do renderizador ----------------------


def test_a_resize_rebuilds_the_sprites_outside_the_frame(monkeypatch: pytest.MonkeyPatch) -> None:
    """`forget_images` nao distingue o que depende do canvas: as 62 caem junto.

    Sem refaze-las no redimensionamento, elas voltariam uma por frame durante a
    primeira queda seguinte — dentro do frame, que e onde nao podem estar."""
    game = Game()
    assert _bee_keys(game.renderer) == 62

    game.apply_resize((1920, 1080))
    assert _bee_keys(game.renderer) == 62

    monkeypatch.setattr(pygame.transform, "rotate", _forbidden)
    game.bird.draw(game.renderer, game.textures)


def _bee_keys(renderer) -> int:
    return sum(1 for key in renderer._images if isinstance(key, tuple) and key[0] == "bee")


def test_the_canvas_does_not_enter_the_sprite_key(tex) -> None:
    """A abelha e desenhada em coordenadas de mundo, e o canvas so muda o que ha em
    volta dela (R24.1) — entao as 62 texturas servem qualquer tela, e um
    redimensionamento nao tem por que multiplica-las."""
    from src.viewport import compute

    renderer = _warm(tex)
    bird = Bird(100, 300)
    for screen in ((PLAY_W, PLAY_H), (1080, 2400), (1920, 1080)):
        config.set_viewport(compute(*screen))
        bird.draw(renderer, tex)
    assert len(renderer._images) == 62
