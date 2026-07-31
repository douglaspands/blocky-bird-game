"""Constantes globais do jogo."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.viewport import Viewport

FPS = 60
TITLE = "Blocky Bee"
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

_viewport: "Viewport | None" = None


def set_viewport(vp: "Viewport") -> None:
    """Define o viewport ativo. Chamado pelo `Game` depois de criar o display e de
    novo a cada redimensionamento da janela (R23.6)."""
    global _viewport
    _viewport = vp


def viewport() -> "Viewport":
    """Viewport ativo.

    Sem display criado (testes de unidade, scripts), o padrao e o canvas 2:3 —
    identico a area jogavel, que e exatamente o comportamento da v2."""
    global _viewport
    if _viewport is None:
        from src import viewport as viewport_module

        _viewport = viewport_module.compute(viewport_module.PLAY_W, viewport_module.PLAY_H)
    return _viewport


def screen_w() -> int:
    """Largura do canvas logico ativo (R23.4).

    Deixou de ser constante de modulo na v3: o canvas tem a proporcao da tela real,
    entao a largura so existe depois que o display foi criado. Funcao pelo mesmo
    motivo de `ground_y()` — uma constante importada congelaria o valor de quem
    importou antes do viewport ser definido."""
    return viewport().canvas[0]


def screen_h() -> int:
    """Altura do canvas logico ativo (R23.4). Ver `screen_w()`."""
    return viewport().canvas[1]


def ground_y() -> int:
    """Topo do chao em coordenadas jogaveis."""
    return screen_h() - GROUND_H
