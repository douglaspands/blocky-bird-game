"""InputManager: unifica teclado, mouse, toque e controle Xbox em acoes abstratas (R10, R15)."""

import pygame

from src import config, render, ui

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
ACTION_RESIZE = "resize"

# eventos de ciclo de vida do app (R16.1): WINDOWFOCUSLOST cobre o desktop (alt-tab)
# como fallback nas plataformas que nao emitem os eventos de app do SDL.
FOCUS_LOST_EVENTS = (pygame.APP_WILLENTERBACKGROUND, pygame.APP_DIDENTERBACKGROUND, pygame.WINDOWFOCUSLOST)


class InputManager:
    def __init__(self, renderer: render.Renderer) -> None:
        self.renderer = renderer
        pygame.joystick.init()
        self.joysticks: dict[int, pygame.joystick.JoystickType] = {}
        for device_index in range(pygame.joystick.get_count()):
            self._add_joystick(device_index)

    def _add_joystick(self, device_index: int) -> None:
        joystick = pygame.joystick.Joystick(device_index)
        self.joysticks[joystick.get_instance_id()] = joystick

    def _remove_joystick(self, instance_id: int) -> None:
        self.joysticks.pop(instance_id, None)

    def _tap(self, actions: set[str], window_x: float, window_y: float) -> None:
        """Converte um ponto da janela para o canvas e resolve a acao.

        Mouse e toque passam pelo mesmo `to_logical` do renderizador ativo, sem
        nenhuma regra divergente entre eles (R34.2). Na v2 o tratamento era
        assimetrico — `pygame.SCALED` pre-convertia o mouse e so o toque era
        convertido a mao —, e a assimetria desapareceu junto com o `SCALED` (design
        secao 33.4)."""
        self._handle_tap(actions, *self.renderer.to_logical(window_x, window_y))

    def _handle_tap(self, actions: set[str], lx: float, ly: float) -> None:
        """Toque/clique em qualquer ponto do canvas voa; no icone de mudo alterna
        mudo; fora do canvas e ignorado (R34.1, R34.3, R15.1, R15.4).

        O recorte e contra o **canvas**, e nao contra a area jogavel. Na v2 o que
        caisse fora dos 480x720 era barra preta de letterbox, moldura morta do SDL, e
        descartar era certo; na v3 aquele espaco e faixa decorativa desenhada e, num
        celular 20:9, ocupa mais tela que o jogo — justamente onde o polegar cai
        (R25.6, design secao 32.8). Como o canvas tem a proporcao da tela e a cobre
        por construcao, o descarte de R34.3 so sobra para o arredondamento da
        conversao."""
        if not (0 <= lx <= config.screen_w() and 0 <= ly <= config.screen_h()):
            return
        if ui.mute_icon_rect().collidepoint(lx, ly):
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
            elif event.type == pygame.WINDOWRESIZED:
                # so acontece no desktop: no Android a janela e a tela inteira e a
                # orientacao esta travada (R23.5, R23.6).
                actions.add(ACTION_RESIZE)
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
                # `event.pos` vem em pixels reais da janela
                self._tap(actions, *event.pos)
            elif event.type == pygame.FINGERDOWN:
                # o toque chega normalizado (0.0-1.0) sobre a janela inteira
                win_w, win_h = self.renderer.window_size
                self._tap(actions, event.x * win_w, event.y * win_h)
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
