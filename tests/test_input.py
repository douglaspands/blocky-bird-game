import pygame

from src import ui
from src.input import ACTION_BACK, ACTION_FLAP, ACTION_LEFT, ACTION_MUTE, ACTION_RIGHT, InputManager


def _make_input(size=(480, 720), canvas_size=(480, 720), offset=(0, 0)):
    pygame.display.set_mode(size, pygame.SCALED | pygame.RESIZABLE)
    # descarta eventos de janela da criacao do display (ex.: WindowFocusLost sob
    # SDL_VIDEODRIVER=dummy com SDL 2.32/pygame-ce), senao contaminam poll()
    pygame.event.clear()
    return InputManager(canvas_size=canvas_size, offset=offset)


def test_finger_tap_in_game_area_flaps():
    im = _make_input()
    pygame.event.post(pygame.event.Event(pygame.FINGERDOWN, x=0.5, y=0.5, touch_id=1, finger_id=1))
    actions, _ = im.poll()
    assert actions == {ACTION_FLAP}


def test_finger_tap_on_mute_icon_mutes_not_flaps():
    im = _make_input()
    win_w, win_h = pygame.display.get_window_size()
    rect = ui.MUTE_ICON_RECT
    nx, ny = rect.centerx / win_w, rect.centery / win_h
    pygame.event.post(pygame.event.Event(pygame.FINGERDOWN, x=nx, y=ny, touch_id=1, finger_id=1))
    actions, _ = im.poll()
    assert actions == {ACTION_MUTE}


def test_mouse_click_on_mute_icon_mutes_not_flaps():
    """Mesma logica que o toque: no desktop, clicar no icone nao deve voar (evita
    disparar flap junto quando um toque real gera tambem um MOUSEBUTTONDOWN sintetico)."""
    im = _make_input()
    rect = ui.MUTE_ICON_RECT
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


def test_tap_in_extended_canvas_area_flaps():
    """No Android, o canvas real pode ser maior que a area jogavel 480x720 (R14.3) —
    a area extra (antes barra preta, agora ceu/parallax estendido) deve voar ao
    toque tambem, sem zona morta no meio da tela."""
    canvas_size = (480, 1067)
    offset = (0, 347)  # area jogavel ancorada embaixo do canvas (ver game.py)
    im = _make_input(size=canvas_size, canvas_size=canvas_size, offset=offset)

    # y=100px do canvas cai bem acima do topo da area jogavel (offset_y=347)
    pygame.event.post(
        pygame.event.Event(pygame.FINGERDOWN, x=0.5, y=100 / canvas_size[1], touch_id=1, finger_id=1)
    )
    actions, _ = im.poll()
    assert actions == {ACTION_FLAP}


def test_tap_on_mute_icon_with_offset_mutes_not_flaps():
    """O icone de mudo continua em coordenadas locais da area jogavel — o hit-test
    precisa descontar o offset do canvas para acha-lo (R15.4, R14.3)."""
    canvas_size = (480, 1067)
    offset = (0, 347)
    im = _make_input(size=canvas_size, canvas_size=canvas_size, offset=offset)

    rect = ui.MUTE_ICON_RECT
    canvas_x = rect.centerx + offset[0]
    canvas_y = rect.centery + offset[1]
    nx, ny = canvas_x / canvas_size[0], canvas_y / canvas_size[1]
    pygame.event.post(pygame.event.Event(pygame.FINGERDOWN, x=nx, y=ny, touch_id=1, finger_id=1))
    actions, _ = im.poll()
    assert actions == {ACTION_MUTE}


def test_finger_tap_outside_logical_area_is_ignored():
    """Numa janela mais larga que 480:720 (pillarbox), toque na barra preta nao
    deve gerar nenhuma acao."""
    im = _make_input(size=(900, 720))

    # x=0.05 normalizado numa janela de 900px cai bem dentro da barra esquerda
    pygame.event.post(pygame.event.Event(pygame.FINGERDOWN, x=0.05, y=0.5, touch_id=1, finger_id=1))
    actions, _ = im.poll()
    assert actions == set()

    # confirma que o centro da MESMA janela continua funcionando (nao e so um bug geral)
    pygame.event.post(pygame.event.Event(pygame.FINGERDOWN, x=0.5, y=0.5, touch_id=1, finger_id=1))
    actions, _ = im.poll()
    assert actions == {ACTION_FLAP}
