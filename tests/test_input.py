import pygame

from src import ui
from src.input import ACTION_BACK, ACTION_FLAP, ACTION_LEFT, ACTION_MUTE, ACTION_RIGHT, InputManager


def _make_input(size=(480, 720)):
    pygame.display.set_mode(size, pygame.SCALED | pygame.RESIZABLE)
    # descarta eventos de janela da criacao do display (ex.: WindowFocusLost sob
    # SDL_VIDEODRIVER=dummy com SDL 2.32/pygame-ce), senao contaminam poll()
    pygame.event.clear()
    return InputManager()


def test_finger_tap_in_game_area_flaps():
    im = _make_input()
    pygame.event.post(pygame.event.Event(pygame.FINGERDOWN, x=0.5, y=0.5, touch_id=1, finger_id=1))
    actions, _ = im.poll()
    assert actions == {ACTION_FLAP}


def test_finger_tap_on_mute_icon_mutes_not_flaps():
    im = _make_input()
    win_w, win_h = pygame.display.get_window_size()
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
    deve gerar nenhuma acao (R14.3, task 41 — restaura o letterbox/pillarbox
    padrao do `pygame.SCALED`, revertendo o zoom/corte da task 40)."""
    im = _make_input(size=(900, 720))

    # x=0.05 normalizado numa janela de 900px cai bem dentro da barra esquerda
    pygame.event.post(pygame.event.Event(pygame.FINGERDOWN, x=0.05, y=0.5, touch_id=1, finger_id=1))
    actions, _ = im.poll()
    assert actions == set()

    # confirma que o centro da MESMA janela continua funcionando (nao e so um bug geral)
    pygame.event.post(pygame.event.Event(pygame.FINGERDOWN, x=0.5, y=0.5, touch_id=1, finger_id=1))
    actions, _ = im.poll()
    assert actions == {ACTION_FLAP}
