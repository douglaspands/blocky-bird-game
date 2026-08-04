"""Chao rolante de blocos, sincronizado a velocidade das colunas (R7.3)."""

import pygame

from src import config, render
from src.config import BLOCK, GROUND_H


class Ground:
    """Chao rolante: deslocamento visual e faixa de colisao fixa na base do canvas."""

    def __init__(self) -> None:
        """Inicia sem deslocamento, com a faixa de colisao na linha do chao atual."""
        self.offset = 0.0
        self.rect = pygame.Rect(0, config.ground_y(), config.screen_w(), GROUND_H)
        """Faixa de colisao do chao, construida uma vez e movida no lugar (R27.3)."""

    def update(self, speed: float) -> None:
        """Avanca o deslocamento visual do chao pela velocidade atual."""
        self.offset = (self.offset - speed) % BLOCK

    def sync_rect(self) -> None:
        """Reancora a faixa de colisao na linha do chao e na largura do canvas atuais.

        Nao e chamada no passo de simulacao, ao contrario das irmas em `Bird` e
        `PipePair`: a geometria do chao nao depende de nada que role durante a partida,
        so do canvas. Quem chama e `Game.apply_resize`. Um `sync_rect()` dentro de
        `update` seria codigo que nenhum teste consegue justificar — foi escrito,
        sobreviveu a rodada de mutacao por ser inerte, e saiu.
        """
        self.rect.y = config.ground_y()
        self.rect.width = config.screen_w()

    def draw(
        self,
        renderer: render.Renderer,
        textures: dict[str, pygame.Surface],
        block_main: str,
        block_edge: str,
    ) -> None:
        """Uma faixa pre-renderizada, um desenho por frame (R27.2).

        A v2 refazia a mesma parede de blocos a cada frame — 22 blits num canvas de
        480 de largura, e mais quanto maior a tela — para um resultado que so difere
        entre frames por alguns pixels de deslocamento horizontal. Aqui a parede e
        construida uma vez por par de blocos e o rolamento vira o retangulo de
        origem andando dentro dela.

        Continua usando as texturas do bioma atual, sem congelamento (R7.3): o par de
        blocos entra na chave da faixa, entao trocar de bioma pede outra faixa em vez
        de reaproveitar a anterior.
        """
        top_y = config.ground_y()
        canvas_w = config.screen_w()
        height = config.screen_h() - top_y
        strip = renderer.image(
            ("ground", block_main, block_edge, canvas_w, height),
            lambda: _make_strip(textures[block_main], textures[block_edge], canvas_w, height),
        )
        # a faixa e periodica em BLOCK, entao deslocar a origem de 0 a BLOCK cobre o
        # ciclo inteiro de rolamento; `offset` ja vem reduzido modulo BLOCK.
        renderer.draw(strip, (0, top_y), pygame.Rect(BLOCK - round(self.offset), 0, canvas_w, height))


def _make_strip(main: pygame.Surface, edge: pygame.Surface, canvas_w: int, height: int) -> pygame.Surface:
    """Parede de chao de `canvas_w + BLOCK` por `height`.

    A fileira de borda fica no topo, as de preenchimento abaixo ate a base do
    canvas. O bloco a mais de largura e o que da lugar ao rolamento — com ele a faixa cobre o
    canvas inteiro em qualquer posicao do ciclo, e o desenho nunca precisa de uma
    segunda passada para tapar a sobra.

    Opaca de proposito: o chao cobre tudo que estiver atras dele, e uma faixa com
    alfa mandaria o desenho para o caminho de mistura a troco de nada (R27.4).
    """
    strip = pygame.Surface((canvas_w + BLOCK, height))
    for x in range(0, canvas_w + BLOCK, BLOCK):
        strip.blit(edge, (x, 0))
        for y in range(BLOCK, height, BLOCK):
            strip.blit(main, (x, y))
    return strip
