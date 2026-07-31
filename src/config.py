"""Constantes globais do jogo."""

SCREEN_W = 480
SCREEN_H = 720  # resolucao logica FIXA (proporcao 2:3), calibracao da task 12 — nunca
# muda com o aparelho; `pygame.SCALED` (em game.py) escala e aplica letterbox
# automatico para caber na tela real, sem cortar nada (task 41, ver design.md
# secao 20.1.5). Combinado com `orientation = portrait` no buildozer.spec, a
# barra que sobra e sempre no topo/base, nunca nas laterais.

FPS = 60
TITLE = "Blocky Bird"
CREDITS = "por Douglas e Pedro"

GRAVITY = 0.45
FLAP_IMPULSE = -8.5
MAX_FALL_SPEED = 12

GROUND_H = 96
PIPE_SPACING = 260
BLOCK = 48
PIPE_W = BLOCK  # colisao deve casar com a largura da coluna de blocos renderizada
GAP_MARGIN = 80
HITBOX_SCALE = 0.85


def ground_y() -> int:
    """Topo do chao em coordenadas jogaveis."""
    return SCREEN_H - GROUND_H
