"""InputManager: unifica teclado, mouse e controle Xbox em acoes abstratas (R10)."""

import pygame

BUTTON_A = 0
BUTTON_Y = 3
BUTTON_START = 7

FLAP_KEYS = (pygame.K_SPACE, pygame.K_UP)
PAUSE_KEYS = (pygame.K_ESCAPE, pygame.K_p)
MUTE_KEYS = (pygame.K_m,)

ACTION_FLAP = "flap"
ACTION_PAUSE = "pause"
ACTION_MUTE = "mute"


class InputManager:
    def __init__(self) -> None:
        pygame.joystick.init()
        self.joysticks: dict[int, pygame.joystick.Joystick] = {}
        for device_index in range(pygame.joystick.get_count()):
            self._add_joystick(device_index)

    def _add_joystick(self, device_index: int) -> None:
        joystick = pygame.joystick.Joystick(device_index)
        joystick.init()
        self.joysticks[joystick.get_instance_id()] = joystick

    def _remove_joystick(self, instance_id: int) -> None:
        self.joysticks.pop(instance_id, None)

    def poll(self) -> tuple[set[str], bool]:
        """Consome a fila de eventos e retorna (acoes abstratas, pedido de fechar janela)."""
        actions: set[str] = set()
        quit_requested = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_requested = True
            elif event.type == pygame.KEYDOWN:
                if event.key in FLAP_KEYS:
                    actions.add(ACTION_FLAP)
                elif event.key in PAUSE_KEYS:
                    actions.add(ACTION_PAUSE)
                elif event.key in MUTE_KEYS:
                    actions.add(ACTION_MUTE)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                actions.add(ACTION_FLAP)
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
