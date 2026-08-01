"""PipePair e PipeManager: obstaculos do jogo (R2)."""

import random

import pygame

from src import config, render
from src.config import BLOCK, GAP_MARGIN, PIPE_SPACING, PIPE_W


class PipePair:
    __slots__ = ("block_edge", "block_main", "bottom_rect", "gap_size", "gap_y", "scored", "top_rect", "x")
    """Sem `__dict__` por instancia: ha varias colunas vivas a cada instante e todas
    tem exatamente estes campos (R27.3)."""

    def __init__(self, x: float, gap_y: float, gap_size: int, block_main: str, block_edge: str) -> None:
        self.x = x
        self.gap_y = gap_y
        self.gap_size = gap_size
        self.block_main = block_main
        self.block_edge = block_edge
        self.scored = False
        self.top_rect = pygame.Rect(0, 0, PIPE_W, 0)
        """Metade de cima da coluna, do topo do canvas ate a beirada da abertura."""
        self.bottom_rect = pygame.Rect(0, 0, PIPE_W, 0)
        """Metade de baixo, da outra beirada da abertura ate a linha do chao.

        Os dois sao atributos persistentes, e nao `property`: um frame de jogo os le
        quatro vezes por coluna — duas na colisao e duas no desenho — e cada leitura
        construia um `pygame.Rect` novo (R27.3). Quem move a coluna ou troca o canvas
        de baixo dela precisa chamar `sync_rects`."""
        self.sync_rects()

    def sync_rects(self) -> None:
        """Reposiciona as duas metades para o `x` atual e para a linha do chao atual.

        Depende de `config.ground_y()`, que muda quando a janela e redimensionada — por
        isso `Game.apply_resize` chama isto, e nao so o passo de simulacao: entre o
        redimensionamento e o proximo `update` ha frames desenhados (PRONTO, PAUSADO,
        GAME_OVER) que usariam a altura antiga."""
        x = round(self.x)
        self.top_rect.x = x
        self.top_rect.height = round(self.gap_y - self.gap_size / 2)
        top = round(self.gap_y + self.gap_size / 2)
        self.bottom_rect.x = x
        self.bottom_rect.y = top
        self.bottom_rect.height = config.ground_y() - top

    def off_screen(self) -> bool:
        """Descarte na borda esquerda da area jogavel, nao do canvas (R2.4): o que
        sai dela ja esta atras da faixa decorativa e nao volta a ser visto."""
        return self.x + PIPE_W < config.play().left

    def visible(self) -> bool:
        """Se alguma parte da coluna cai dentro do canvas (R27.7).

        A v2 desenhava sempre um par a mais do que precisava: `_spawn` cria a coluna
        em `play.right`, que num canvas 2:3 e a propria borda da tela. Eram duas
        pilhas inteiras de blocos por frame num obstaculo que ninguem podia ver.

        O recorte e contra o canvas, e nao contra a area jogavel: numa tela larga a
        coluna passa um bom tempo entre a borda do canvas e a da area jogavel, e la
        ela existe de verdade — e a faixa lateral, desenhada depois, que a esconde
        (R24.4). Descartar antes disso deixaria a faixa transparente onde ela nao
        cobrisse."""
        return -PIPE_W < round(self.x) < config.screen_w()

    def draw(self, renderer: render.Renderer, textures: dict[str, pygame.Surface]) -> None:
        """Duas faixas pre-renderizadas, dois desenhos por coluna (R27.2).

        A pilha de blocos e sempre a mesma imagem — o que muda de coluna para coluna
        e onde ela e cortada. Entao cada par de blocos vira duas faixas de altura de
        canvas, uma com a fileira de borda embaixo (coluna de cima) e outra com ela
        em cima (coluna de baixo), e desenhar uma coluna vira escolher o recorte.

        As texturas continuam sendo as do bioma congelado na criacao da coluna
        (R2.5): o par entra na chave das faixas, entao uma coluna do overworld que
        sobreviva a entrada na cave continua saindo de terra e grama."""
        height = config.screen_h()
        main = textures[self.block_main]
        edge = textures[self.block_edge]
        x = round(self.x)

        top = self.top_rect
        if top.height > 0:
            strip = renderer.image(
                ("pipe_top", self.block_main, self.block_edge, height),
                lambda: _make_strip(main, edge, height, edge_at_top=False),
            )
            # o corte sai da base da faixa: e la que esta a fileira de borda, que
            # precisa cair exatamente na beirada da abertura.
            renderer.draw(strip, (x, 0), pygame.Rect(0, height - top.height, PIPE_W, top.height))

        bottom = self.bottom_rect
        if bottom.height > 0:
            strip = renderer.image(
                ("pipe_bottom", self.block_main, self.block_edge, height),
                lambda: _make_strip(main, edge, height, edge_at_top=True),
            )
            renderer.draw(strip, (x, bottom.top), pygame.Rect(0, 0, PIPE_W, bottom.height))


def _make_strip(
    main: pygame.Surface, edge: pygame.Surface, height: int, *, edge_at_top: bool
) -> pygame.Surface:
    """Pilha de blocos de altura de canvas, com a fileira de borda numa das pontas.

    A altura e a do canvas porque e o maior corte que qualquer coluna pode pedir: a
    abertura nunca encosta na borda de cima nem no chao, entao nenhuma das duas
    metades chega a ser mais alta que a tela.

    Opaca de proposito, como a faixa do chao: a coluna cobre o que estiver atras
    dela, e um canal alfa so mandaria o desenho para o caminho de mistura (R27.4)."""
    strip = pygame.Surface((PIPE_W, height))
    rows = range(0, height, BLOCK) if edge_at_top else range(height - BLOCK, -BLOCK, -BLOCK)
    for index, y in enumerate(rows):
        strip.blit(edge if index == 0 else main, (0, y))
    return strip


class PipeManager:
    def __init__(self, gap_size: int, block_main: str, block_edge: str) -> None:
        self.pipes: list[PipePair] = []
        # nasce na borda direita da AREA JOGAVEL, nao do canvas: e o que faz o tempo
        # entre o surgimento da coluna e a chegada a abelha ser identico em qualquer
        # proporcao de tela (R24.3).
        self._spawn(config.play().right, gap_size, block_main, block_edge)

    def _spawn(self, x: float, gap_size: int, block_main: str, block_edge: str) -> None:
        # a abertura e sorteada dentro da AREA JOGAVEL: com uma faixa de ceu acima,
        # `GAP_MARGIN` sozinho deixaria o centro da abertura cair na decoracao, fora
        # do alcance da abelha (R24.1, R25.1).
        gap_y = random.uniform(config.play().top + GAP_MARGIN, config.ground_y() - GAP_MARGIN)
        self.pipes.append(PipePair(x, gap_y, gap_size, block_main, block_edge))

    def update(self, speed: float, gap_size: int, block_main: str, block_edge: str) -> None:
        """Move as colunas (R2.3), spawna novas com o bioma atual (R2.1/R2.2/R2.5).

        Remove as que saem da tela (R2.4).
        """
        for pipe in self.pipes:
            pipe.x -= speed
            pipe.sync_rects()

        if self.pipes[-1].x <= config.play().right - PIPE_SPACING:
            self._spawn(self.pipes[-1].x + PIPE_SPACING, gap_size, block_main, block_edge)

        # remocao no lugar: a compreensao de lista que estava aqui construia uma lista
        # nova a cada frame para descartar uma coluna a cada ~90 (R27.3).
        index = 0
        while index < len(self.pipes):
            if self.pipes[index].off_screen():
                del self.pipes[index]
            else:
                index += 1

    def sync_rects(self) -> None:
        """Reposiciona os retangulos de todas as colunas (R23.6).

        Chamado no redimensionamento, que muda a linha do chao sob colunas que nao se
        moveram."""
        for pipe in self.pipes:
            pipe.sync_rects()

    def draw(self, renderer: render.Renderer, textures: dict[str, pygame.Surface]) -> None:
        """Desenha so as colunas que caem dentro do canvas (R27.7)."""
        for pipe in self.pipes:
            if pipe.visible():
                pipe.draw(renderer, textures)
