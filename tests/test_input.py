import pygame

from src import ui
from src.input import ACTION_BACK, ACTION_FLAP, ACTION_LEFT, ACTION_MUTE, ACTION_RIGHT, InputManager
from tests.fakes import FakeRenderer

CANVAS = (480, 720)


def _make_input(size=CANVAS):
    """InputManager sobre um renderizador de canvas 480x720 numa janela `size`.

    Desde a task 50 a conversao de coordenada e do renderizador, nao do
    `pygame.SCALED`: mouse e toque passam pelo mesmo `to_logical`."""
    pygame.event.clear()
    return InputManager(FakeRenderer(CANVAS, window=size))


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

    im = _make_input(size=window)
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=point))
    by_mouse, _ = im.poll()

    im = _make_input(size=window)
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


def test_finger_tap_outside_logical_area_is_ignored():
    """Numa janela mais larga que 480:720 (pillarbox), toque na barra preta nao
    deve gerar nenhuma acao (R14.3, task 41)."""
    im = _make_input(size=(900, 720))

    # x=0.05 normalizado numa janela de 900px cai bem dentro da barra esquerda
    pygame.event.post(pygame.event.Event(pygame.FINGERDOWN, x=0.05, y=0.5, touch_id=1, finger_id=1))
    actions, _ = im.poll()
    assert actions == set()

    # confirma que o centro da MESMA janela continua funcionando (nao e so um bug geral)
    pygame.event.post(pygame.event.Event(pygame.FINGERDOWN, x=0.5, y=0.5, touch_id=1, finger_id=1))
    actions, _ = im.poll()
    assert actions == {ACTION_FLAP}
