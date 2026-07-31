import pygame
import pytest

from src import config, ui
from src.game import Game, GameState
from src.input import ACTION_BACK, ACTION_FLAP, ACTION_LEFT, ACTION_MUTE, ACTION_RIGHT, InputManager
from src.viewport import PLAY_H, PLAY_W, compute
from tests.fakes import FakeRenderer

SQUARE_2_3 = (PLAY_W, PLAY_H)  # canvas 480x720: sem faixa nenhuma, a geometria da v2
PHONE = (1080, 2400)  # canvas 480x1067: faixa de ceu de 251px, faixa de chao de 96px
WIDE = (1920, 1080)  # canvas 1280x720: faixas laterais de 400px


def _make_input(screen=SQUARE_2_3, *, window=None):
    """InputManager sobre o canvas daquela tela, numa janela `window`.

    Desde a task 50 a conversao de coordenada e do renderizador, nao do
    `pygame.SCALED`: mouse e toque passam pelo mesmo `to_logical`. O viewport e
    ativado aqui porque o recorte de `_handle_tap` e contra o canvas (R34.3), e o
    canvas e quem sabe onde as faixas comecam."""
    config.set_viewport(compute(*screen))
    canvas = config.viewport().canvas
    pygame.event.clear()
    return InputManager(FakeRenderer(canvas, window=window or canvas))


def _tap_at(im, point):
    """Clica com o mouse num ponto da janela e devolve as acoes."""
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=point))
    return im.poll()[0]


def test_finger_tap_in_game_area_flaps():
    im = _make_input()
    pygame.event.post(pygame.event.Event(pygame.FINGERDOWN, x=0.5, y=0.5, touch_id=1, finger_id=1))
    actions, _ = im.poll()
    assert actions == {ACTION_FLAP}


def test_finger_tap_on_mute_icon_mutes_not_flaps():
    im = _make_input()
    win_w, win_h = im.renderer.window_size
    rect = ui.mute_icon_rect()
    nx, ny = rect.centerx / win_w, rect.centery / win_h
    pygame.event.post(pygame.event.Event(pygame.FINGERDOWN, x=nx, y=ny, touch_id=1, finger_id=1))
    actions, _ = im.poll()
    assert actions == {ACTION_MUTE}


def test_mouse_click_on_mute_icon_mutes_not_flaps():
    """Mesma logica que o toque: no desktop, clicar no icone nao deve voar (evita
    disparar flap junto quando um toque real gera tambem um MOUSEBUTTONDOWN sintetico)."""
    im = _make_input()
    rect = ui.mute_icon_rect()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center))
    actions, _ = im.poll()
    assert actions == {ACTION_MUTE}


def test_mouse_and_touch_at_the_same_physical_point_agree():
    """Os dois passam pelo mesmo `to_logical` do renderizador: numa janela com
    pillarbox, o mesmo ponto fisico tem que produzir a mesma acao (R34.2)."""
    window = (900, 720)
    point = (window[0] // 2, window[1] // 2)

    im = _make_input(window=window)
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=point))
    by_mouse, _ = im.poll()

    im = _make_input(window=window)
    event = pygame.event.Event(
        pygame.FINGERDOWN, x=point[0] / window[0], y=point[1] / window[1], touch_id=1, finger_id=1
    )
    pygame.event.post(event)
    by_touch, _ = im.poll()

    assert by_mouse == by_touch == {ACTION_FLAP}


def test_back_key_maps_to_back_action():
    im = _make_input()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_AC_BACK))
    actions, _ = im.poll()
    assert actions == {ACTION_BACK}


def test_return_and_kp_enter_flap():
    """Botao central do D-pad de controle remoto de Android TV (R14.4)."""
    im = _make_input()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    actions, _ = im.poll()
    assert actions == {ACTION_FLAP}

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_KP_ENTER))
    actions, _ = im.poll()
    assert actions == {ACTION_FLAP}


def test_left_right_keys_map_to_left_right_actions():
    im = _make_input()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT))
    actions, _ = im.poll()
    assert actions == {ACTION_LEFT}

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
    actions, _ = im.poll()
    assert actions == {ACTION_RIGHT}


def test_finger_tap_outside_the_canvas_is_ignored():
    """Coordenada convertida que cai fora do canvas nao gera acao (R34.3).

    No jogo real isso praticamente nao acontece: o canvas recebe a proporcao da tela,
    entao ele cobre a janela inteira e so o arredondamento da conversao pode escapar
    pela borda. Aqui a janela e forcada a 900x720 com um canvas de 480x720 justamente
    para o descarte existir e a guarda ficar exercitada."""
    im = _make_input(window=(900, 720))

    # x=0.05 normalizado numa janela de 900px cai bem a esquerda do canvas
    pygame.event.post(pygame.event.Event(pygame.FINGERDOWN, x=0.05, y=0.5, touch_id=1, finger_id=1))
    actions, _ = im.poll()
    assert actions == set()

    # confirma que o centro da MESMA janela continua funcionando (nao e so um bug geral)
    pygame.event.post(pygame.event.Event(pygame.FINGERDOWN, x=0.5, y=0.5, touch_id=1, finger_id=1))
    actions, _ = im.poll()
    assert actions == {ACTION_FLAP}


# --- Entrada sobre faixa decorativa (task 51, R34) ----------------------------


@pytest.mark.parametrize(
    ("screen", "band_name"),
    [(WIDE, "left_band"), (WIDE, "right_band"), (PHONE, "sky_band"), (PHONE, "ground_band")],
)
def test_tap_on_a_decorative_band_flaps(screen, band_name):
    """A regra da v2 descartava tudo que caisse fora dos 480x720. Na v3 a faixa e
    conteudo desenhado e, num celular alongado, ocupa mais tela que a propria area
    jogavel — transportar a regra antiga faria da maior parte da tela zona morta
    (R34.1, R25.6, design secao 32.8)."""
    im = _make_input(screen)
    band = getattr(config.viewport(), band_name)
    assert band.width and band.height  # a tela escolhida gera mesmo esta faixa
    assert not config.play().collidepoint(band.center)  # e o ponto esta fora do jogo

    assert _tap_at(im, band.center) == {ACTION_FLAP}


def test_tap_on_the_mute_icon_inside_the_sky_band_still_mutes():
    """O controle de interface e a unica excecao (R15.4, R25.6): o icone mora na faixa
    de ceu, e o toque nele nao pode virar flap so porque a faixa toda passou a voar."""
    im = _make_input(PHONE)
    rect = ui.mute_icon_rect()
    assert config.viewport().sky_band.contains(rect)

    assert _tap_at(im, rect.center) == {ACTION_MUTE}


def test_tap_on_a_band_starts_and_restarts_the_match():
    """R34.4: em PRONTO e em GAME_OVER a faixa vale como a area jogavel. E a
    verificacao de ponta a ponta — o ponto entra pelo evento do SDL e sai como
    transicao de estado, passando por `to_logical`, `_handle_tap` e `_flap_action`."""
    game = Game()
    config.set_viewport(compute(*WIDE))
    game.viewport = config.viewport()
    game.renderer = FakeRenderer(game.viewport.canvas)
    game.input = InputManager(game.renderer)
    game.reset()
    point = game.viewport.left_band.center

    assert game.state == GameState.PRONTO
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=point))
    game.handle_events()
    assert game.state == GameState.JOGANDO

    game.state = GameState.GAME_OVER
    game.score = 7
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=point))
    game.handle_events()
    assert game.state == GameState.PRONTO
    assert game.score == 0
