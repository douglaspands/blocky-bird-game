"""InputManager: unifica teclado, mouse, toque e controle Xbox em acoes abstratas (R10, R15)."""

import pygame

from src import ui
from src.config import SCREEN_H, SCREEN_W
from src.scale import fit_scale

BUTTON_A = 0
BUTTON_Y = 3
BUTTON_START = 7

FLAP_KEYS = (pygame.K_SPACE, pygame.K_UP, pygame.K_RETURN, pygame.K_KP_ENTER)
PAUSE_KEYS = (pygame.K_ESCAPE, pygame.K_p)
MUTE_KEYS = (pygame.K_m,)
BACK_KEYS = (pygame.K_AC_BACK,)
LEFT_KEYS = (pygame.K_LEFT,)
RIGHT_KEYS = (pygame.K_RIGHT,)

ACTION_FLAP = "flap"
ACTION_PAUSE = "pause"
ACTION_MUTE = "mute"
ACTION_BACK = "back"
ACTION_FOCUS_LOST = "focus_lost"
ACTION_LEFT = "left"
ACTION_RIGHT = "right"

# eventos de ciclo de vida do app (R16.1): WINDOWFOCUSLOST cobre o desktop (alt-tab)
# como fallback nas plataformas que nao emitem os eventos de app do SDL.
FOCUS_LOST_EVENTS = (pygame.APP_WILLENTERBACKGROUND, pygame.APP_DIDENTERBACKGROUND, pygame.WINDOWFOCUSLOST)


def _touch_to_logical(norm_x: float, norm_y: float) -> tuple[float, float]:
    """Converte coordenada de toque normalizada (0.0-1.0, relativa a janela
    inteira) para o espaco logico fixo 480x720, desfazendo o letterbox/
    pillarbox que `pygame.SCALED` aplica automaticamente (R14.3). Mouse ja
    chega pre-convertido pelo SDL; so toque precisa disso."""
    win_w, win_h = pygame.display.get_window_size()
    scale, off_x, off_y = fit_scale(SCREEN_W, SCREEN_H, win_w, win_h)
    return (norm_x * win_w - off_x) / scale, (norm_y * win_h - off_y) / scale


class InputManager:
    def __init__(self) -> None:
        pygame.joystick.init()
        self.joysticks: dict[int, pygame.joystick.JoystickType] = {}
        for device_index in range(pygame.joystick.get_count()):
            self._add_joystick(device_index)

    def _add_joystick(self, device_index: int) -> None:
        joystick = pygame.joystick.Joystick(device_index)
        self.joysticks[joystick.get_instance_id()] = joystick

    def _remove_joystick(self, instance_id: int) -> None:
        self.joysticks.pop(instance_id, None)

    def _handle_tap(self, actions: set[str], lx: float, ly: float) -> None:
        """Toque/clique fora da area logica (na barra de letterbox/pillarbox) e
        ignorado; no icone de mudo alterna mudo; em qualquer outro ponto da
        area de jogo, voa (R15.1, R15.4)."""
        if not (0 <= lx <= SCREEN_W and 0 <= ly <= SCREEN_H):
            return
        if ui.MUTE_ICON_RECT.collidepoint(lx, ly):
            actions.add(ACTION_MUTE)
        else:
            actions.add(ACTION_FLAP)

    def poll(self) -> tuple[set[str], bool]:
        """Consome a fila de eventos e retorna (acoes abstratas, pedido de fechar janela)."""
        actions: set[str] = set()
        quit_requested = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_requested = True
            elif event.type in FOCUS_LOST_EVENTS:
                actions.add(ACTION_FOCUS_LOST)
            elif event.type == pygame.KEYDOWN:
                if event.key in FLAP_KEYS:
                    actions.add(ACTION_FLAP)
                elif event.key in PAUSE_KEYS:
                    actions.add(ACTION_PAUSE)
                elif event.key in MUTE_KEYS:
                    actions.add(ACTION_MUTE)
                elif event.key in BACK_KEYS:
                    actions.add(ACTION_BACK)
                elif event.key in LEFT_KEYS:
                    actions.add(ACTION_LEFT)
                elif event.key in RIGHT_KEYS:
                    actions.add(ACTION_RIGHT)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # com pygame.SCALED, event.pos ja vem em coordenadas logicas (R9.1)
                self._handle_tap(actions, *event.pos)
            elif event.type == pygame.FINGERDOWN:
                self._handle_tap(actions, *_touch_to_logical(event.x, event.y))
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == BUTTON_A:
                    actions.add(ACTION_FLAP)
                elif event.button == BUTTON_START:
                    actions.add(ACTION_PAUSE)
                elif event.button == BUTTON_Y:
                    actions.add(ACTION_MUTE)
            elif event.type == pygame.JOYDEVICEADDED:
                self._add_joystick(event.device_index)
            elif event.type == pygame.JOYDEVICEREMOVED:
                self._remove_joystick(event.instance_id)

        return actions, quit_requested
