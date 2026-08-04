"""Decoracao de fundo com parallax, duas camadas por bioma (R7.4)."""

import random
from collections.abc import Callable, Iterator

import pygame

from src import config, render

FAR_FACTOR = 0.3
NEAR_FACTOR = 0.6

STRIP_SPANS = 3
"""Quantas larguras de canvas a faixa de uma camada cobre, no minimo.

O numero e um acordo entre memoria e repeticao. As formas do parallax sao
deterministicas por indice, mas nao periodicas: a faixa e que impoe um periodo, e a
partir dele o fundo se repete. Tres larguras dao dezenas de segundos de rolagem antes
do ciclo fechar — mais que uma partida tipica — sem que uma camada custe mais que
alguns megabytes."""

MIN_STRIP_TILES = 4
"""Piso de ladrilhos por faixa, para uma camada de periodo grande num canvas estreito
nao virar uma faixa de dois ladrilhos, onde a repeticao seria obvia."""

Drawer = Callable[[render.Renderer, int, int, int], None]

_STRIP_TOPS: dict[object, int] = {}
"""Onde comeca o conteudo de cada faixa, medido na construcao (ver `_build`).

Memoiza uma funcao pura da chave da faixa — um inteiro, nunca pixels — e por isso
pode viver no modulo: duas faixas com a mesma chave tem o mesmo topo, tenham sido
construidas por qual `DecorManager` for. Guardar o valor junto com a imagem no cache
do renderizador exigiria que `Renderer.image` soubesse carregar metadado, o que so
esta camada precisa."""


CLOUD_UNIT = 14
CLOUD_SHAPES = [
    # cada linha: (deslocamento em unidades, largura em unidades), de cima para baixo
    [(2, 4), (1, 6), (0, 8), (1, 6)],
    [(3, 3), (1, 6), (0, 9), (2, 5)],
    [(2, 3), (0, 7), (1, 6)],
]

HILL_UNIT = 18
HILL_SHAPES = [
    # cada linha: (deslocamento em unidades, largura em unidades), de cima para baixo (topo -> chao)
    [(3, 2), (2, 4), (1, 6), (0, 8)],
    [(4, 1), (2, 5), (1, 7), (0, 9)],
    [(2, 3), (1, 5), (0, 7)],
]


def _draw_block_shape(
    renderer: render.Renderer,
    shape: list[tuple[int, int]],
    x: int,
    top_y: int,
    unit: int,
    color: tuple[int, int, int],
) -> None:
    """Desenha uma forma quadriculada (pilha de retangulos), estilo voxel Minecraft."""
    for row_i, (col_offset, width_units) in enumerate(shape):
        y = top_y + row_i * unit
        rect = pygame.Rect(x + col_offset * unit, y, width_units * unit, unit)
        renderer.fill(color, rect)


def _draw_clouds(renderer: render.Renderer, x: int, idx: int, ground_y: int) -> None:
    rng = random.Random(idx * 13 + 1)
    shape = rng.choice(CLOUD_SHAPES)
    top_y = 40 + rng.randint(0, 100)
    _draw_block_shape(renderer, shape, x, top_y, CLOUD_UNIT, (255, 255, 255))


def _draw_hills(renderer: render.Renderer, x: int, idx: int, ground_y: int) -> None:
    rng = random.Random(idx * 17 + 2)
    shape = rng.choice(HILL_SHAPES)
    top_y = ground_y - len(shape) * HILL_UNIT
    _draw_block_shape(renderer, shape, x, top_y, HILL_UNIT, (90, 160, 70))


STALACTITE_COLOR = (55, 55, 62)
LAVA_COLOR = (230, 100, 20)
PILLAR_COLOR = (50, 30, 35)


def _paint_triangle(size: tuple[int, int], color: tuple[int, int, int]) -> pygame.Surface:
    """Pinta um triangulo apontando para baixo, do tamanho pedido."""
    width, height = size
    surface = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.polygon(surface, color, [(0, 0), (width, 0), (width // 2, height)])
    return surface


def _paint_ellipse(size: tuple[int, int], color: tuple[int, int, int]) -> pygame.Surface:
    """Pinta uma elipse preenchendo o retangulo do tamanho pedido."""
    surface = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.ellipse(surface, color, pygame.Rect((0, 0), size))
    return surface


def _draw_stalactites(renderer: render.Renderer, x: int, idx: int, ground_y: int) -> None:
    """Estalactite: a unica forma do parallax que nao e retangulo.

    O renderizador so preenche retangulos, entao o triangulo e pintado numa
    superficie e guardado como imagem, chaveada pelo seu tamanho — os sorteios
    produzem poucas combinacoes distintas, e a partir da segunda aparicao de cada uma
    o desenho e uma copia de pixels ja prontos.
    """
    rng = random.Random(idx * 19 + 3)
    size = (rng.randint(20, 40), rng.randint(40, 100))
    image = renderer.image(("stalactite", size), lambda: _paint_triangle(size, STALACTITE_COLOR))
    renderer.draw(image, (x, 0))


def ore_vein_shapes(x: int, idx: int, ground_y: int) -> Iterator[tuple[tuple[int, int, int], pygame.Rect]]:
    """Gera os quatro cubos de um veio de minerio, com a cor sorteada por `idx`.

    Publico e devolvendo formas, em vez de desenhar, porque tem dois consumidores que
    pintam em alvos diferentes: a camada de parallax da Cave, que preenche pelo
    renderizador, e as faixas laterais, que constroem uma superficie uma unica vez
    (`bands.py`, R25.2).
    """
    rng = random.Random(idx * 23 + 4)
    y = rng.randint(150, ground_y - 150)
    color = rng.choice([(120, 190, 255), (255, 215, 60), (200, 200, 210)])
    for _ in range(4):
        ox = rng.randint(-15, 15)
        oy = rng.randint(-15, 15)
        yield color, pygame.Rect(x + ox, y + oy, 6, 6)


def _draw_ore_veins(renderer: render.Renderer, x: int, idx: int, ground_y: int) -> None:
    for color, rect in ore_vein_shapes(x, idx, ground_y):
        renderer.fill(color, rect)


def _draw_lava_pools(renderer: render.Renderer, x: int, idx: int, ground_y: int) -> None:
    """Poca de lava: elipse assentada na linha do chao, pela mesma razao da estalactite."""
    rng = random.Random(idx * 29 + 5)
    size = (rng.randint(100, 180), rng.randint(20, 40))
    image = renderer.image(("lava_pool", size), lambda: _paint_ellipse(size, LAVA_COLOR))
    renderer.draw(image, (x, ground_y - size[1]))


def _draw_pillars(renderer: render.Renderer, x: int, idx: int, ground_y: int) -> None:
    rng = random.Random(idx * 31 + 6)
    w = rng.randint(24, 40)
    h = rng.randint(100, 220)
    renderer.fill(PILLAR_COLOR, pygame.Rect(x, ground_y - h, w, h))


_LAYERS: dict[str, tuple[tuple[int, Drawer], tuple[int, Drawer]]] = {
    "overworld": ((220, _draw_clouds), (150, _draw_hills)),
    "cave": ((130, _draw_stalactites), (100, _draw_ore_veins)),
    "nether": ((200, _draw_lava_pools), (170, _draw_pillars)),
}


class _StripPainter(render.Renderer):
    """Renderizador que pinta numa superficie, usado so para construir as faixas.

    Os desenhadores acima continuam escritos contra `render.Renderer`, exatamente como
    quando pintavam o canvas do frame. O que mudou foi o alvo: em vez do canvas, eles
    pintam uma vez numa faixa, que depois e desenhada inteira. Trocar o alvo em vez de
    reescrever os desenhadores e o que torna a equivalencia visual verificavel — a
    forma continua saindo do mesmo codigo de antes.

    So `draw` e `fill` sao implementados porque so eles sao chamados na construcao; o
    resto da interface pertence a quem publica frames, e uma faixa nao publica nada.
    """

    def __init__(self, surface: pygame.Surface) -> None:
        """Assume uma superficie ja alocada como alvo de pintura."""
        super().__init__()
        self.surface = surface
        self.size = surface.get_size()
        self.backend = "strip"

    def make_image(self, surface: pygame.Surface) -> render.Image:
        """Guarda a superficie como esta.

        Sem passar por `render.convert`: a faixa e alvo de construcao, e nao a tela.
        Converter aqui alinharia a forma ao formato do display so para pinta-la uma
        vez; quem paga o custo por desenho e a faixa pronta, convertida quando ela
        vira imagem do renderizador de verdade.
        """
        return render.SurfaceImage(surface)

    def draw(self, image: render.Image, dest: render.Dest, area: pygame.Rect | None = None) -> None:
        """Copia a forma para a faixa, misturando pelo alfa dela."""
        self.surface.blit(image.raw, dest, area)

    def fill(self, color: render.Color, rect: pygame.Rect) -> None:
        """Preenche um retangulo da faixa."""
        self.surface.fill(color, rect)


def _tile_count(period: int, canvas_w: int) -> int:
    """Ladrilhos de uma faixa: o bastante para cobrir `STRIP_SPANS` canvas."""
    return max(MIN_STRIP_TILES, -(-STRIP_SPANS * canvas_w // period))


def _make_strip(drawer: Drawer, period: int, tiles: int, ground_y: int) -> pygame.Surface:
    """Pinta `tiles` ladrilhos numa faixa periodica de `period * tiles` de largura.

    A faixa e desenhada com wrap-around, o que a torna periodica na largura: o pixel
    de mundo `p` sai do pixel `p % largura` dela. Duas consequencias, e as duas estao
    neste laco.

    A primeira e que o ladrilho de indice `i` do mundo vira o ladrilho `i % tiles` da
    faixa — a sequencia infinita de formas passa a se repetir a cada `tiles`. E a
    unica diferenca visual em relacao ao caminho anterior, e o preco de nao instanciar
    um `random.Random` por ladrilho por frame (R27.3).

    A segunda e a razao do laco comecar em -1 e terminar em `tiles`: uma forma pode
    ser mais larga que o periodo (a colina de `HILL_SHAPES[1]` mede 162 contra 150) e
    transbordar para o ladrilho vizinho. Na emenda da faixa esse vizinho e a outra
    ponta, entao as duas pontas sao pintadas mais uma vez do lado de fora, para que a
    parte que transborda caia onde o wrap-around vai busca-la.
    """
    strip = pygame.Surface((period * tiles, ground_y), pygame.SRCALPHA)
    painter = _StripPainter(strip)
    for index in range(-1, tiles + 1):
        drawer(painter, index * period, index % tiles, ground_y)
    return strip


def _build(key: object, drawer: Drawer, period: int, tiles: int, ground_y: int) -> pygame.Surface:
    """Constroi a faixa e descarta as linhas vazias acima e abaixo do conteudo.

    Uma camada ocupa uma faixa horizontal estreita da altura do canvas — nuvens la em
    cima, colinas rentes ao chao — e guardar o vazio entre elas custaria varias vezes
    o tamanho do conteudo. O recorte sai de `get_bounding_rect`, medido nos pixels de
    verdade, e nao de uma altura declarada a mao por camada: assim ele nunca discorda
    do que o desenhador desenhou.
    """
    strip = _make_strip(drawer, period, tiles, ground_y)
    band = strip.get_bounding_rect()
    _STRIP_TOPS[key] = band.top
    return strip.subsurface(0, band.top, strip.get_width(), max(band.height, 1)).copy()


class DecorManager:
    """Acompanha o deslocamento das duas camadas de parallax de fundo."""

    def __init__(self) -> None:
        """Inicia as duas camadas sem deslocamento."""
        self.far_scrolled = 0.0
        self.near_scrolled = 0.0

    def update(self, speed: float) -> None:
        """Avanca o deslocamento das duas camadas, cada uma no seu fator de parallax."""
        self.far_scrolled += speed * FAR_FACTOR
        self.near_scrolled += speed * NEAR_FACTOR

    def draw(self, renderer: render.Renderer, decor_id: str, *, far: bool = True, near: bool = True) -> None:
        """Duas faixas pre-renderizadas, ate quatro desenhos por frame (R27.2, R27.3).

        A v2 refazia as duas camadas a cada frame: uma dezena de ladrilhos, cada um
        com um `random.Random` novo — um Mersenne Twister de 624 palavras — so para
        sortear de novo a mesma forma que o indice ja determinava. Aqui o sorteio
        acontece uma vez, na construcao da faixa, e o frame vira um ou dois recortes
        por camada.

        `far` e `near` desligam cada camada por nivel de qualidade (R29.2). Quem decide
        e o `Game`, com a tabela de `quality.py`: este modulo nao conhece niveis, so
        recebe o que desenhar — a mesma disciplina de mao unica que mantem `mobs.py`
        sem dependencia de jogo (R25.4). A deriva continua sendo atualizada em
        `update()` mesmo com a camada desligada, para que voltar ao nivel de cima nao
        produza um salto no cenario.
        """
        # a linha do chao vem da area jogavel, nao da base do canvas: colinas, poças
        # de lava e pilares tem que assentar no chao de verdade, nao afundar na faixa
        # decorativa de baixo (R25.1).
        ground_y = config.ground_y()
        if far:
            self._layer(renderer, decor_id, 0, self.far_scrolled, ground_y)
        if near:
            self._layer(renderer, decor_id, 1, self.near_scrolled, ground_y)

    def _layer(
        self, renderer: render.Renderer, decor_id: str, layer: int, scrolled: float, ground_y: int
    ) -> None:
        """Desenha uma camada, cobrindo o canvas com ate dois recortes da faixa.

        O rolamento vira deslocamento da origem, como no chao (R27.2) — a diferenca e
        que aqui a faixa nao e mais larga que o canvas por uma folga fixa, e sim
        periodica: quando a origem chega perto do fim, o que falta vem do comeco, e e
        so isso que o segundo recorte faz.

        Ladrilha ate a largura do canvas logico (R25.5) — mais larga que a area
        jogavel sempre que a tela nao e 2:3, entao o parallax cobre a tela toda em vez
        de parar nos 480px de mundo.
        """
        period, drawer = _LAYERS[decor_id][layer]
        canvas_w = renderer.size[0]
        tiles = _tile_count(period, canvas_w)
        key = ("decor", decor_id, layer, period, tiles, ground_y)
        image = renderer.image(key, lambda: _build(key, drawer, period, tiles, ground_y))
        top = _STRIP_TOPS[key]
        width, height = image.size

        offset = round(scrolled) % width
        first = min(width - offset, canvas_w)
        renderer.draw(image, (0, top), pygame.Rect(offset, 0, first, height))
        if first < canvas_w:
            renderer.draw(image, (first, top), pygame.Rect(0, 0, canvas_w - first, height))
