"""Camada de renderizacao: uma interface, dois caminhos de desenho (R26).

A v2 passava uma `pygame.Surface` de modulo em modulo e desenhava nela. A v3 quer a
GPU do aparelho, mas nao pode exigi-la: o projeto vai ate a API 21 do Android, onde
um renderizador acelerado nao e garantido. Este modulo resolve os dois lados de uma
vez — expoe uma interface pequena (sete operacoes, secao 33.1 do design) que
`bird`, `pipes`, `ground`, `decor`, `particles`, `biome` e `ui` usam sem saber qual
caminho esta ativo (R26.4), e escolhe o caminho sozinho numa cascata de tres niveis
(R26.1, R26.2, R26.3):

| Nivel | Tentativa | `backend` |
|---|---|---|
| 1 | `Renderer(window, accelerated=1, vsync=True)` | `gpu-accelerated` |
| 2 | `Renderer(window, accelerated=-1, vsync=True)` | `gpu-software` |
| 3 | `SurfaceRenderer` — `Surface.blit`, o caminho da v2 | `surface` |

Cada queda de nivel e registrada em log com o erro que a causou (R26.5) e nenhuma
falha escapa de `create()`: o jogo nunca deixa de abrir por causa do renderizador,
mesma disciplina de degradacao graciosa que o audio segue desde a v1 (R8.4).

Ver specs/v3/design.md secao 33.
"""

import logging
import os
from typing import Any

import pygame

from src import scale

logger = logging.getLogger(__name__)

try:
    from pygame._sdl2 import video
except ImportError:  # pragma: no cover - build de pygame sem o modulo _sdl2
    video = None  # ty: ignore[invalid-assignment]

ENV_SCALE_QUALITY = "SDL_RENDER_SCALE_QUALITY"
"""Nome de ambiente do hint `SDL_HINT_RENDER_SCALE_QUALITY`.

`0` e vizinho mais proximo: simultaneamente o mais barato e o unico correto para
arte em pixel, porque filtragem linear borraria a estetica voxel do jogo (R26.7)."""

BACKEND_ACCELERATED = "gpu-accelerated"
BACKEND_SOFTWARE = "gpu-software"
BACKEND_SURFACE = "surface"

Color = tuple[int, int, int] | tuple[int, int, int, int]
Dest = pygame.Rect | tuple[int, int]
"""Destino de um desenho: um `Rect` (o desenho e esticado para ele) ou apenas o canto
superior esquerdo (o desenho sai no tamanho nativo da imagem)."""

_OPAQUE = 255


class Image:
    """Uma imagem pronta para desenhar, no formato que o renderizador ativo entende.

    Nenhum modulo de jogo constroi uma diretamente: todas nascem de
    `Renderer.make_image`, a partir de uma `Surface` gerada por codigo na
    inicializacao (R7.1). `alpha` e de leitura e escrita, e e o que o fade de bioma
    (R5.4) e o escurecimento das telas de pausa e game over usam.
    """

    __slots__ = ()

    size: tuple[int, int]
    """Largura e altura em pixels de canvas."""

    raw: Any
    """A imagem de verdade — `Texture` na GPU, `Surface` fora dela. So o renderizador
    que a criou desempacota este campo; para os modulos de jogo a imagem e opaca."""

    @property
    def alpha(self) -> int:
        """Opacidade da imagem inteira, de 0 (invisivel) a 255 (opaca)."""
        raise NotImplementedError

    @alpha.setter
    def alpha(self, value: int) -> None:
        raise NotImplementedError


class Renderer:
    """Interface de desenho comum aos dois caminhos (R26.4).

    Sete operacoes cobrem o jogo inteiro. A que carrega mais peso e `draw` com `area`
    opcional: e ela que permite recortar uma faixa de uma strip pre-renderizada, que
    e o mecanismo do atlas (design secao 34) — no caminho de GPU vira o `srcrect` do
    `Renderer.blit`, e no de superficie o terceiro argumento de `Surface.blit`.
    """

    size: tuple[int, int]
    """Tamanho do canvas logico. Todo desenho e feito nessas coordenadas; levar o
    canvas para a tela real e problema do renderizador, nao de quem desenha."""

    backend: str
    """Caminho efetivamente em uso, exposto ao log e a instrumentacao (R26.5)."""

    def make_image(self, surface: pygame.Surface) -> Image:
        """Converte uma `Surface` numa imagem do renderizador ativo."""
        raise NotImplementedError

    def clear(self, color: Color) -> None:
        """Preenche o canvas inteiro, apagando o frame anterior."""
        raise NotImplementedError

    def draw(self, image: Image, dest: Dest, area: pygame.Rect | None = None) -> None:
        """Desenha `image` (ou o recorte `area` dela) em `dest`."""
        raise NotImplementedError

    def fill(self, color: Color, rect: pygame.Rect) -> None:
        """Preenche um retangulo com uma cor, misturando quando ela tem alfa."""
        raise NotImplementedError

    def present(self) -> None:
        """Publica o frame montado, levando o canvas logico para a tela real."""
        raise NotImplementedError

    def to_logical(self, x: float, y: float) -> tuple[float, float]:
        """Converte um ponto em pixels reais da janela para coordenada de canvas.

        Os dois caminhos convertem a mesma coisa da mesma forma, e e isso que permite
        a `input.py` tratar mouse e toque por um caminho unico (R34.1)."""
        raise NotImplementedError

    def snapshot(self) -> pygame.Surface:
        """Le o canvas de volta como `Surface`. Diagnostico e testes apenas.

        No caminho de GPU e uma transferencia de VRAM para RAM, cara demais para o
        laco principal. Chamar antes de `present()`."""
        raise NotImplementedError


class GpuImage(Image):
    """Imagem residente na GPU: uma `Texture` do `pygame._sdl2.video`."""

    __slots__ = ("raw", "size")

    raw: "video.Texture"

    def __init__(self, texture: "video.Texture") -> None:
        """Envolve uma textura ja enviada para a GPU."""
        self.raw = texture
        self.size = (texture.width, texture.height)

    @property
    def alpha(self) -> int:
        """Opacidade aplicada pela GPU na hora do desenho, sem tocar nos pixels."""
        return self.raw.alpha

    @alpha.setter
    def alpha(self, value: int) -> None:
        self.raw.alpha = value


class SurfaceImage(Image):
    """Imagem em memoria principal: uma `pygame.Surface`, o caminho da v2."""

    __slots__ = ("raw", "size")

    raw: pygame.Surface

    def __init__(self, surface: pygame.Surface) -> None:
        """Envolve uma superficie ja convertida para o formato do display."""
        self.raw = surface
        self.size = surface.get_size()

    @property
    def alpha(self) -> int:
        """Alfa de superficie inteira. `None` do pygame vira 255, para que ler o
        valor logo apos criar a imagem devolva o mesmo que no caminho de GPU."""
        value = self.raw.get_alpha()
        return _OPAQUE if value is None else value

    @alpha.setter
    def alpha(self, value: int) -> None:
        self.raw.set_alpha(value)


class GpuRenderer(Renderer):
    """Desenho pela GPU, sobre `pygame._sdl2.video` (design secao 33.2).

    `logical_size` faz o proprio SDL escalar o canvas para a janela, na GPU — o mesmo
    que `pygame.SCALED` fazia na v2, mas agora com todo o desenho anterior tambem na
    GPU. `vsync=True` elimina quadros desperdicados e rasgo de imagem (R26.6).
    """

    def __init__(
        self,
        window: "video.Window",
        renderer: "video.Renderer",
        canvas: tuple[int, int],
        backend: str,
    ) -> None:
        """Assume a posse de uma janela e de um renderizador SDL ja criados."""
        self.window = window
        self.sdl = renderer
        self.sdl.logical_size = canvas
        self.size = canvas
        self.backend = backend

    def make_image(self, surface: pygame.Surface) -> Image:
        """Envia a superficie para a GPU uma unica vez (R27.2).

        O `blend_mode` e fixado em mistura alfa para casar com o caminho de
        superficie, onde `convert_alpha()` sempre produz uma imagem com alfa."""
        texture = video.Texture.from_surface(self.sdl, surface)
        texture.blend_mode = pygame.BLENDMODE_BLEND
        return GpuImage(texture)

    def clear(self, color: Color) -> None:
        """Preenche o canvas inteiro com `color`."""
        self.sdl.draw_color = color
        self.sdl.clear()

    def draw(self, image: Image, dest: Dest, area: pygame.Rect | None = None) -> None:
        """Desenha a textura, esticando-a quando `dest` traz um tamanho."""
        self.sdl.blit(image.raw, _dest_rect(dest, image, area), area)

    def fill(self, color: Color, rect: pygame.Rect) -> None:
        """Preenche `rect`, ligando a mistura alfa so quando a cor pede."""
        self.sdl.draw_blend_mode = pygame.BLENDMODE_BLEND if _has_alpha(color) else pygame.BLENDMODE_NONE
        self.sdl.draw_color = color
        self.sdl.fill_rect(rect)

    def present(self) -> None:
        """Troca o buffer da GPU."""
        self.sdl.present()

    def to_logical(self, x: float, y: float) -> tuple[float, float]:
        """Desfaz a escala de `logical_size`, pelo proprio SDL."""
        return self.sdl.coordinates_from_window((x, y))

    def snapshot(self) -> pygame.Surface:
        """Le o alvo de renderizacao de volta para uma `Surface`."""
        return self.sdl.to_surface()


class SurfaceRenderer(Renderer):
    """Desenho por `Surface.blit`, o caminho da v2 (design secao 33.4).

    E a ultima rede de seguranca da cascata, e tambem o que mantem a suite de testes
    simples: funciona em qualquer lugar onde o pygame funcione, inclusive sob
    `SDL_VIDEODRIVER=dummy`.

    O desenho acontece num canvas fora da tela, que `present()` escala para a janela
    com barras nas sobras. Nao se usa `pygame.SCALED` aqui de proposito: com ele o
    SDL entrega o mouse ja convertido mas o toque nao, e `to_logical` teria
    significados diferentes conforme o backend — exatamente a assimetria que a v3
    esta desfazendo (R34.1).
    """

    def __init__(self, canvas: tuple[int, int], window: tuple[int, int], *, fullscreen: bool = False) -> None:
        """Cria o display real e o canvas fora da tela onde o jogo desenha."""
        flags = pygame.FULLSCREEN if fullscreen else pygame.RESIZABLE
        self.window = pygame.display.set_mode(window, flags)
        self.surface = pygame.Surface(canvas)
        self.size = canvas
        self.backend = BACKEND_SURFACE
        # superficies reaproveitadas entre frames: recria-las a cada `present()` ou a
        # cada `fill()` com alfa alocaria alguns megabytes por frame, que e
        # exatamente o que a v3 esta eliminando (R27.3).
        self._scaled: pygame.Surface | None = None
        self._blend: pygame.Surface | None = None

    def make_image(self, surface: pygame.Surface) -> Image:
        """Converte para o formato do display, com alfa por pixel (R27.4).

        Sem display inicializado a conversao levanta `pygame.error`; nesse caso a
        superficie original serve, so mais lenta — nunca vale impedir o jogo de
        abrir por causa de uma otimizacao."""
        try:
            return SurfaceImage(surface.convert_alpha())
        except pygame.error:
            return SurfaceImage(surface)

    def clear(self, color: Color) -> None:
        """Preenche o canvas inteiro com `color`."""
        self.surface.fill(color)

    def draw(self, image: Image, dest: Dest, area: pygame.Rect | None = None) -> None:
        """Desenha a superficie, escalando so quando `dest` pede outro tamanho."""
        rect = _dest_rect(dest, image, area)
        source = image.raw
        if rect.size != (area.size if area is not None else image.size):
            # o caminho de GPU estica a textura para o `dstrect`; aqui isso precisa
            # ser feito a mao, para que os dois backends desenhem a mesma coisa.
            source = pygame.transform.scale(source.subsurface(area) if area else source, rect.size)
            area = None
        self.surface.blit(source, rect, area)

    def fill(self, color: Color, rect: pygame.Rect) -> None:
        """Preenche `rect`, misturando quando a cor tem alfa.

        A superficie de mistura e cacheada por tamanho: o escurecimento de PAUSADO e
        de GAME_OVER cobre o canvas inteiro todo frame, e aloca-la a cada um era
        justamente a maior fonte de lixo por frame da v2 (design secao 30)."""
        if not _has_alpha(color):
            self.surface.fill(color, rect)
            return
        self.surface.blit(self._blend_surface(rect.size, color), rect)

    def present(self) -> None:
        """Escala o canvas para a janela e publica o frame."""
        factor, offset_x, offset_y = scale.fit_scale(*self.size, *self.window.get_size())
        target = (round(self.size[0] * factor), round(self.size[1] * factor))
        if self._scaled is None or self._scaled.get_size() != target:
            self._scaled = pygame.Surface(target)
        # `scale` e vizinho mais proximo, ao contrario de `smoothscale`: e o mesmo
        # criterio do hint de qualidade do caminho de GPU (R26.7).
        pygame.transform.scale(self.surface, target, self._scaled)
        if offset_x or offset_y:
            self.window.fill((0, 0, 0))
        self.window.blit(self._scaled, (round(offset_x), round(offset_y)))
        pygame.display.flip()

    def to_logical(self, x: float, y: float) -> tuple[float, float]:
        """Desfaz a escala e o deslocamento aplicados por `present()`."""
        factor, offset_x, offset_y = scale.fit_scale(*self.size, *self.window.get_size())
        return (x - offset_x) / factor, (y - offset_y) / factor

    def snapshot(self) -> pygame.Surface:
        """Copia o canvas fora da tela."""
        return self.surface.copy()

    def _blend_surface(self, size: tuple[int, int], color: Color) -> pygame.Surface:
        """Superficie de mistura do tamanho pedido, reaproveitada entre chamadas."""
        if self._blend is None or self._blend.get_size() != size:
            self._blend = pygame.Surface(size, pygame.SRCALPHA)
        self._blend.fill(color)
        return self._blend


def create(
    canvas: tuple[int, int],
    window: tuple[int, int],
    *,
    fullscreen: bool = False,
    title: str = "",
) -> Renderer:
    """Cria o melhor renderizador disponivel para este aparelho (R26.1, R26.2, R26.3).

    Desce a cascata de tres niveis e devolve o primeiro que funcionar, registrando em
    log o erro de cada queda (R26.5). Nunca levanta excecao: o ultimo nivel e o
    caminho de superficie da v2, que funciona em qualquer lugar onde o pygame
    funcione.
    """
    os.environ.setdefault(ENV_SCALE_QUALITY, "0")

    sdl_window = _open_sdl_window(window, fullscreen=fullscreen, title=title)
    if sdl_window is not None:
        for accelerated, backend in ((1, BACKEND_ACCELERATED), (-1, BACKEND_SOFTWARE)):
            try:
                sdl_renderer = video.Renderer(sdl_window, accelerated=accelerated, vsync=True)
            except Exception as exc:
                logger.warning("renderizador %s indisponivel: %s", backend, exc)
                continue
            return GpuRenderer(sdl_window, sdl_renderer, canvas, backend)
        sdl_window.destroy()

    logger.warning("sem renderizador de GPU; caindo para o caminho %s", BACKEND_SURFACE)
    return SurfaceRenderer(canvas, window, fullscreen=fullscreen)


def _open_sdl_window(window: tuple[int, int], *, fullscreen: bool, title: str) -> "video.Window | None":
    """Abre a janela do `_sdl2`, ou None quando nao da.

    A janela do caminho de GPU nao pode vir de `pygame.display.set_mode`: o SDL
    recusa criar um renderizador para uma janela que ja tem superficie associada.
    Por isso ela e criada aqui, e o modulo `display` do pygame deixa de ser o dono
    da janela nesse caminho."""
    if video is None:
        logger.warning("pygame._sdl2 indisponivel nesta build do pygame")
        return None
    try:
        return video.Window(title, size=window, fullscreen=fullscreen, resizable=not fullscreen)
    except Exception as exc:
        logger.warning("janela do _sdl2 indisponivel: %s", exc)
        return None


def _dest_rect(dest: Dest, image: Image, area: pygame.Rect | None) -> pygame.Rect:
    """Normaliza `dest` para um `Rect`, completando o tamanho quando so ha posicao."""
    if isinstance(dest, pygame.Rect):
        return dest
    size = area.size if area is not None else image.size
    return pygame.Rect(dest[0], dest[1], size[0], size[1])


def _has_alpha(color: Color) -> bool:
    """Indica se a cor pede mistura, isto e, se tem componente alfa abaixo de 255."""
    return len(color) > 3 and color[-1] < _OPAQUE
