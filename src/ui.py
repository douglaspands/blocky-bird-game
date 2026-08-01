"""HUD e telas de estado, com fonte pixelada e sombra dura (R7.5, R7.6)."""

import pygame

from src import config, pixelfont, render
from src.config import CREDITS

SHADOW_COLOR = (40, 30, 20)
SHADOW_OFFSET = 3
OVERLAY_COLOR = (0, 0, 0, 140)
GOLD = (255, 215, 60)

MUTE_ICON_SIZE = 40
MUTE_ICON_MARGIN = 14


HUD_SCORE_MARGIN = 40
"""Distancia do topo da area jogavel ate o centro da pontuacao, quando nao ha faixa
de ceu para receber o HUD. E a posicao da v1/v2."""


def max_text_w() -> int:
    """Largura maxima de um texto: a area jogavel menos 20px de margem de cada lado.

    Medida contra a area jogavel, e nao contra o canvas, para que o texto nunca
    escorra por cima das faixas laterais numa tela larga (R25.2)."""
    return config.play().width - 40


def mute_icon_rect() -> pygame.Rect:
    """Geometria do botao de mudo, no canto superior direito do canvas (R15.4).

    Fica no canto da tela de verdade, e nao no da area jogavel: e o ponto mais
    alcancavel no celular, e uma faixa decorativa pode receber controle de interface
    (R25.6). Verticalmente ele mora na faixa de ceu quando ela o comporta (R25.7);
    se a faixa for curta demais, desce para dentro da area jogavel em vez de ficar
    metade em cada uma.

    Funcao, e nao constante, porque o canvas so tem dimensao depois que o display
    existe. `input.py` importa daqui para o hit-test, mantendo desenho e posicao do
    botao como uma unica fonte de verdade."""
    vp = config.viewport()
    needed = MUTE_ICON_MARGIN + MUTE_ICON_SIZE
    top = MUTE_ICON_MARGIN if vp.sky_band.height >= needed else vp.play.top + MUTE_ICON_MARGIN
    return pygame.Rect(
        vp.width - MUTE_ICON_MARGIN - MUTE_ICON_SIZE,
        top,
        MUTE_ICON_SIZE,
        MUTE_ICON_SIZE,
    )


def _scale_for(base_size: int) -> int:
    """Converte o base_size (tamanho de fonte da v1) num fator inteiro de pixel."""
    return max(1, base_size // 2)


def _text_width(n_chars: int, scale: int) -> int:
    return scale * (pixelfont.GLYPH_W * n_chars + pixelfont.SPACING * max(n_chars - 1, 0))


_FIT_SCALE_CACHE: dict[tuple[int, int, int], int] = {}
"""Resultados de `_fit_scale`, por (numero de caracteres, escala pedida, limite).

Pequeno e limitado por construcao: a escala so depende do *comprimento* do texto, nao
do texto — a fonte e monoespacada —, entao a pontuacao subindo de 0 a 999 usa tres
entradas, e nao mil."""


def _fit_scale(text: str, scale: int) -> int:
    """Reduz a escala ate o texto caber em MAX_TEXT_W (a fonte bitmap e proporcionalmente
    mais larga que a SysFont usada na v1, entao alguns textos longos estourariam a tela
    sem este ajuste).

    O laco de medicao roda uma vez por combinacao e nunca mais: `draw_text` e `_stack`
    chamam esta funcao para cada linha de cada frame, sempre com os mesmos argumentos
    (R27.3). O limite entra na chave porque `max_text_w()` e derivado do viewport — hoje
    ele nao muda no redimensionamento (a area jogavel e fixa), e amarra-lo a chave e o
    que garante que continue correto se um dia mudar."""
    limit = max_text_w()
    key = (len(text), scale, limit)
    fitted = _FIT_SCALE_CACHE.get(key)
    if fitted is None:
        fitted = scale
        while fitted > 1 and _text_width(key[0], fitted) > limit:
            fitted -= 1
        _FIT_SCALE_CACHE[key] = fitted
    return fitted


def _text_image(
    renderer: render.Renderer, text: str, scale: int, color: tuple[int, int, int]
) -> render.Image:
    """Linha de texto ja renderizada, guardada por (texto, escala, cor).

    `pixelfont.render` ja cacheia a superficie; o cache do renderizador evita
    reenvia-la a cada frame, que e o que importa no caminho de GPU (R27.2)."""
    return renderer.image(("text", text, scale, color), lambda: pixelfont.render(text, scale, color))


def draw_text(
    renderer: render.Renderer,
    text: str,
    center: tuple[int, int],
    base_size: int = 12,
    color: tuple[int, int, int] = (255, 255, 255),
) -> None:
    scale = _fit_scale(text, _scale_for(base_size))
    shadow = _text_image(renderer, text, scale, SHADOW_COLOR)
    main = _text_image(renderer, text, scale, color)
    renderer.draw(shadow, _centered(shadow, center[0] + SHADOW_OFFSET, center[1] + SHADOW_OFFSET))
    renderer.draw(main, _centered(main, *center))


def _centered(image: render.Image, center_x: int, center_y: int) -> tuple[int, int]:
    """Canto superior esquerdo que centra `image` no ponto dado."""
    width, height = image.size
    return center_x - width // 2, center_y - height // 2


def _stack(
    renderer: render.Renderer,
    center_x: int,
    top_y: int,
    lines: list[tuple[str, int, tuple[int, int, int]]],
    margin: int = 8,
) -> int:
    """Empilha linhas de texto verticalmente pela altura real renderizada (R19.3).

    Ao contrario de deltas fixos em pixels, a posicao de cada linha depende da
    altura de fato ocupada pela linha anterior (GLYPH_H * escala + sombra), entao
    duas linhas nunca colidem mesmo se a escala de uma delas mudar. Retorna o y
    onde a proxima linha comecaria, para permitir compor um espacamento extra.
    """
    y = top_y
    for text, base_size, color in lines:
        scale = _fit_scale(text, _scale_for(base_size))
        height = pixelfont.GLYPH_H * scale
        draw_text(renderer, text, (center_x, y + height // 2), base_size=base_size, color=color)
        y += height + SHADOW_OFFSET + margin
    return y


def _dim_overlay(renderer: render.Renderer) -> None:
    """Escurece o canvas inteiro para as telas de pausa e de fim de jogo.

    Um `fill` com alfa, e nao mais uma `Surface` de tela cheia criada por frame — era
    a maior fonte de lixo por frame da v2 (design secao 30)."""
    renderer.fill(OVERLAY_COLOR, pygame.Rect(0, 0, config.screen_w(), config.screen_h()))


def draw_ready_screen(renderer: render.Renderer, highscore: int) -> None:
    play = config.play()
    next_y = _stack(
        renderer,
        play.centerx,
        play.top + play.height // 4,
        [
            ("BLOCKY BEE", 12, (255, 220, 60)),
            (CREDITS.upper(), 5, (230, 230, 230)),
        ],
    )
    instruction = "ESPACO / CLIQUE PARA VOAR"
    instruction_scale = _fit_scale(instruction, _scale_for(9))
    instruction_y = next_y + 16 + (pixelfont.GLYPH_H * instruction_scale) // 2
    draw_text(
        renderer,
        instruction,
        (play.centerx, instruction_y),
        base_size=9,
        color=GOLD,
    )
    draw_text(
        renderer,
        f"RECORDE: {highscore}",
        (play.centerx, config.ground_y() - 24),
        base_size=8,
        color=GOLD,
    )


def _paint_mute_icon(muted: bool) -> pygame.Surface:
    """Pinta o botao de mudo num quadrado de `MUTE_ICON_SIZE`, em coordenadas locais.

    As duas riscas do estado mudo sao diagonais, e o renderizador so preenche
    retangulos — entao o icone e pintado uma vez por estado e vira imagem. Sao duas no
    total, exatamente as que a task 56 tambem preve."""
    size = MUTE_ICON_SIZE
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    rect = pygame.Rect(0, 0, size, size)
    pygame.draw.rect(surface, (20, 16, 10), rect)
    pygame.draw.rect(surface, GOLD, rect, width=2)

    color = (220, 70, 60) if muted else (255, 255, 255)
    cx, cy = rect.center
    unit = size // 8
    # corpo do alto-falante: bloco quadrado + haste, em retangulos (estetica blocky)
    pygame.draw.rect(surface, color, (cx - 3 * unit, cy - unit, 2 * unit, 2 * unit))
    pygame.draw.rect(surface, color, (cx - unit, cy - 3 * unit, unit, 6 * unit))

    if muted:
        pygame.draw.line(surface, color, (rect.left + 8, rect.top + 8), (rect.right - 8, rect.bottom - 8), 3)
        pygame.draw.line(surface, color, (rect.left + 8, rect.bottom - 8), (rect.right - 8, rect.top + 8), 3)
    else:
        pygame.draw.rect(surface, color, (cx + unit, cy - 2 * unit, unit, 4 * unit))
        pygame.draw.rect(surface, color, (cx + 2 * unit, cy - 3 * unit, unit, 6 * unit))
    return surface


def draw_mute_icon(renderer: render.Renderer, muted: bool) -> None:
    """Botao de mudo tocavel no canto da tela, estilo voxel (R15.4)."""
    image = renderer.image(("mute_icon", muted), lambda: _paint_mute_icon(muted))
    renderer.draw(image, mute_icon_rect().topleft)


def hud_score_center(base_size: int = 12) -> tuple[int, int]:
    """Onde a pontuacao do HUD e desenhada.

    Quando existe faixa de ceu e ela comporta o texto, a pontuacao vai para o meio
    dela, liberando a area de jogo (R25.7). Numa tela 2:3, sem faixa, cai exatamente
    onde caia na v2."""
    vp = config.viewport()
    sky = vp.sky_band
    text_h = pixelfont.GLYPH_H * _scale_for(base_size) + SHADOW_OFFSET
    if sky.height >= text_h:
        return vp.play.centerx, sky.centery
    return vp.play.centerx, vp.play.top + HUD_SCORE_MARGIN


def draw_hud_score(renderer: render.Renderer, score: int) -> None:
    draw_text(renderer, str(score), hud_score_center(), base_size=12)


def draw_paused_overlay(renderer: render.Renderer) -> None:
    play = config.play()
    _dim_overlay(renderer)
    _stack(
        renderer,
        play.centerx,
        play.centery - 24,
        [
            ("PAUSADO", 12, (255, 255, 255)),
            ("SETAS: MUDO", 5, (210, 210, 210)),
        ],
    )


def draw_game_over_screen(renderer: render.Renderer, score: int, highscore: int) -> None:
    play = config.play()
    _dim_overlay(renderer)
    _stack(
        renderer,
        play.centerx,
        play.centery - 90,
        [
            ("GAME OVER", 12, (220, 60, 50)),
            (f"PONTOS: {score}", 8, (255, 255, 255)),
            (f"RECORDE: {highscore}", 8, (255, 255, 255)),
            ("ESPACO / CLIQUE PARA REINICIAR", 5, (220, 220, 220)),
        ],
    )
