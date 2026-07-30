"""Constantes globais do jogo."""

SCREEN_W = 480
BASE_SCREEN_H = 720  # altura de referencia (proporcao 2:3 com SCREEN_W), calibracao da task 12
# Altura logica REAL da area jogavel — dinamica desde a task 39 (retrato sem
# pillarbox: acompanha a proporcao do aparelho, largura sempre fixa em SCREEN_W).
# Atualizada por `game.Game.__init__`. Como e mutavel em runtime, sempre acessar
# como `config.SCREEN_H` (import do modulo); `from src.config import SCREEN_H`
# congelaria o valor no momento do import, antes do calculo dinamico rodar.
SCREEN_H: int = BASE_SCREEN_H

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
    """Topo do chao em coordenadas jogaveis — usa a altura dinamica atual (task 39)."""
    return SCREEN_H - GROUND_H


def height_scale() -> float:
    """Fator de escala vertical em relacao a BASE_SCREEN_H.

    Usado para manter a dificuldade (abertura/margem das colunas, R2/R5) numa
    proporcao consistente da tela quando SCREEN_H muda dinamicamente (task 39)
    — sem isso, um aparelho com mais altura logica real ganharia espaco de
    reacao extra de graca, ficando mais facil.
    """
    return SCREEN_H / BASE_SCREEN_H
