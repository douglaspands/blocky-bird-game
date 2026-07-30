"""InputManager: unifica teclado, mouse, toque e controle Xbox em acoes abstratas (R10, R15)."""

import pygame

from src import ui
from src.config import SCREEN_H, SCREEN_W

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


class InputManager:
    def __init__(
        self,
        canvas_size: tuple[int, int] = (SCREEN_W, SCREEN_H),
        offset: tuple[int, int] = (0, 0),
    ) -> None:
        """`canvas_size` e a resolucao logica real passada ao `SCALED` (pode ser
        maior que 480x720 no Android, esticada para preencher a tela — R14.3); `offset`
        e onde a area jogavel 480x720 fica ancorada dentro desse canvas. Ambos default
        para o caso simples (canvas == area jogavel, sem deslocamento), usado no
        desktop e nos testes que nao passam esses argumentos."""
        pygame.joystick.init()
        self.joysticks: dict[int, pygame.joystick.JoystickType] = {}
        self._canvas_w, self._canvas_h = canvas_size
        self._offset_x, self._offset_y = offset
        for device_index in range(pygame.joystick.get_count()):
            self._add_joystick(device_index)

    def _add_joystick(self, device_index: int) -> None:
        joystick = pygame.joystick.Joystick(device_index)
        self.joysticks[joystick.get_instance_id()] = joystick

    def _remove_joystick(self, instance_id: int) -> None:
        self.joysticks.pop(instance_id, None)

    def _touch_to_canvas(self, norm_x: float, norm_y: float) -> tuple[float, float]:
        """Converte coordenada de toque normalizada (0.0-1.0, relativa a janela inteira)
        para o espaco do canvas (a resolucao logica passada ao SCALED), desfazendo o
        letterbox/pillarbox residual do SDL (R14.3)."""
        win_w, win_h = pygame.display.get_window_size()
        scale = min(win_w / self._canvas_w, win_h / self._canvas_h)
        draw_w, draw_h = self._canvas_w * scale, self._canvas_h * scale
        off_x, off_y = (win_w - draw_w) / 2, (win_h - draw_h) / 2
        cx = (norm_x * win_w - off_x) / scale
        cy = (norm_y * win_h - off_y) / scale
        return cx, cy

    def _handle_tap(self, actions: set[str], cx: float, cy: float) -> None:
        """Toque/clique fora do canvas real (barra residual, se sobrar por
        arredondamento) e ignorado; no icone de mudo alterna mudo; em qualquer outro
        ponto do canvas voa — inclusive na area de ceu/parallax estendida, que deixou
        de ser barra preta (R15.1, R15.4, R14.3)."""
        if not (0 <= cx <= self._canvas_w and 0 <= cy <= self._canvas_h):
            return
        gx, gy = cx - self._offset_x, cy - self._offset_y
        if ui.MUTE_ICON_RECT.collidepoint(gx, gy):
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
                # com pygame.SCALED, event.pos ja vem em coordenadas do canvas (R9.1)
                self._handle_tap(actions, *event.pos)
            elif event.type == pygame.FINGERDOWN:
                self._handle_tap(actions, *self._touch_to_canvas(event.x, event.y))
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
