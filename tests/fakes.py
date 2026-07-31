"""`FakeRenderer`: renderizador de teste que registra chamadas em vez de pintar pixels.

Depois da task 50 nenhum modulo de desenho recebe mais uma `pygame.Surface` — todos
recebem um `render.Renderer`. Isso abre a porta para testar desenho pelo que foi
*pedido* em vez de pelo que ficou na tela: "desenhou o icone de mudo dentro da faixa
de ceu" e uma afirmacao mais legivel, e muito mais rapida de verificar, do que "o
pixel (452, 18) e dourado" (design secao 33.5).

Cada imagem carrega a chave com que foi pedida a `Renderer.image`, e e por ela que os
testes reconhecem o que foi desenhado: `("text", "PAUSADO", 6, cor)`, `("mute_icon",
True)`, `"dirt"`, `("sky", "cave", 480, 720)`.
"""

from collections.abc import Callable

import pygame

from src import render
from src.scale import fit_scale


class FakeImage(render.Image):
    """Imagem de teste: guarda a superficie de origem e a chave que a criou."""

    __slots__ = ("_alpha", "key", "raw", "size")

    def __init__(self, surface: pygame.Surface, key: object = None) -> None:
        """Envolve a superficie construida pela fabrica, sem converter nada."""
        self.raw = surface
        self.size = surface.get_size()
        self.key = key
        self._alpha = 255

    @property
    def alpha(self) -> int:
        """Opacidade registrada, para os testes de fade de bioma (R5.4)."""
        return self._alpha

    @alpha.setter
    def alpha(self, value: int) -> None:
        self._alpha = value


class FakeRenderer(render.Renderer):
    """Renderizador que so anota o que lhe pediram.

    `calls` guarda a sequencia completa, na ordem — que e o que permite afirmar sobre
    oclusao (quem foi desenhado depois de quem). Os auxiliares `draws`, `fills` e
    `texts` filtram os casos mais usados.
    """

    def __init__(self, canvas: tuple[int, int] = (480, 720), window: tuple[int, int] | None = None) -> None:
        """Cria o renderizador com um canvas logico e, opcionalmente, outra janela."""
        super().__init__()
        self.size = canvas
        self.backend = "fake"
        self._window = window or canvas
        self.calls: list[tuple] = []

    @property
    def window_size(self) -> tuple[int, int]:
        """Tamanho da janela simulada."""
        return self._window

    def make_image(self, surface: pygame.Surface) -> render.Image:
        """Imagem sem chave, para quem chama `make_image` diretamente."""
        return FakeImage(surface)

    def image(self, key: object, factory: Callable[[], pygame.Surface]) -> render.Image:
        """Constroi uma vez por chave e guarda a chave dentro da imagem."""
        image = self._images.get(key)
        if image is None:
            image = FakeImage(factory(), key)
            self._images[key] = image
        return image

    def clear(self, color: render.Color) -> None:
        """Registra a limpeza do canvas."""
        self.calls.append(("clear", color))

    def draw(self, image: render.Image, dest: render.Dest, area: pygame.Rect | None = None) -> None:
        """Registra o desenho ja com o retangulo de destino resolvido."""
        key = image.key if isinstance(image, FakeImage) else None
        self.calls.append(("draw", key, render._dest_rect(dest, image, area), area))

    def fill(self, color: render.Color, rect: pygame.Rect) -> None:
        """Registra o preenchimento."""
        self.calls.append(("fill", color, pygame.Rect(rect)))

    def present(self) -> None:
        """Registra a publicacao do frame."""
        self.calls.append(("present",))

    def to_logical(self, x: float, y: float) -> tuple[float, float]:
        """Mesma conta do caminho de superficie, para os testes de entrada."""
        factor, offset_x, offset_y = fit_scale(*self.size, *self._window)
        return (x - offset_x) / factor, (y - offset_y) / factor

    def resize(self, canvas: tuple[int, int]) -> None:
        """Troca o canvas logico."""
        self.size = canvas

    # --- leitura das chamadas registradas ---------------------------------------

    @property
    def draws(self) -> list[tuple[object, pygame.Rect]]:
        """Pares (chave da imagem, retangulo de destino), na ordem de desenho."""
        return [(key, rect) for kind, key, rect, _ in self._of("draw")]

    @property
    def fills(self) -> list[tuple[render.Color, pygame.Rect]]:
        """Pares (cor, retangulo), na ordem."""
        return [(color, rect) for _, color, rect in self._of("fill")]

    def drawn(self, tag: object) -> list[pygame.Rect]:
        """Retangulos das imagens cuja chave e `tag` ou comeca por `tag`."""
        return [rect for key, rect in self.draws if key == tag or (isinstance(key, tuple) and key[0] == tag)]

    @property
    def texts(self) -> list[tuple[str, pygame.Rect]]:
        """Pares (texto, retangulo do texto com a sombra), um por linha desenhada.

        `ui.draw_text` emite sempre sombra e texto, nessa ordem e com a mesma chave a
        menos da cor; a uniao dos dois retangulos e a area que a linha de fato ocupa —
        o mesmo que a v2 media somando `SHADOW_OFFSET` a largura e a altura."""
        found: list[tuple[str, pygame.Rect]] = []
        pending: tuple[str, pygame.Rect] | None = None
        for key, rect in self.draws:
            if not (isinstance(key, tuple) and key[0] == "text"):
                continue
            text = str(key[1])
            if pending is not None and pending[0] == text:
                found.append((text, pending[1].union(rect)))
                pending = None
            else:
                pending = (text, rect)
        return found

    def _of(self, kind: str) -> list[tuple]:
        return [call for call in self.calls if call[0] == kind]
