"""Faixas laterais: corte transversal do subsolo do bioma (R25.2, R24.4).

Quando a tela e mais larga que a area jogavel, cada lateral recebe um corte
transversal do terreno, opaco e ocupando a altura inteira do canvas. A area jogavel
passa a ser lida como um poco vertical cortado na terra, a unica parte por onde se
enxerga o ceu — a estetica de mineshaft do Minecraft.

A opacidade nao e enfeite, e o mecanismo de R24.4: as faixas sao desenhadas DEPOIS
das colunas, entao uma coluna que ainda nao entrou na area jogavel fica escondida
atras da terra. Combinado com o spawn em `play.right` (R24.3), o jogador enxerga o
obstaculo no mesmo instante em que enxergaria numa tela 2:3 — a oclusao e o que
impede uma tela mais larga de virar vantagem.

Ver specs/v3/design.md secao 32.5.
"""

import pygame

from src import config, decor, render
from src.biome import Biome

DEEP_BLOCK = {"overworld": "stone", "cave": "cobblestone", "nether": "obsidian"}
"""Camada profunda de cada bioma: Overworld grama -> terra -> pedra, Cave pedra ->
pedregulho, Nether netherrack -> obsidiana. Chaveado pelo id do bioma, no mesmo
padrao de `decor._LAYERS`, para que a decoracao nao vire campo de `Biome`."""

TOPSOIL_ROWS = 3
"""Fileiras do bloco principal entre a linha do chao e a camada profunda."""

ORE_VEIN_PERIOD = 90
"""Distancia horizontal entre veios de minerio dentro da faixa."""


class SideBands:
    """Desenha as duas faixas laterais, cada uma como uma unica imagem por bioma.

    O conteudo so muda quando o canvas ou o bioma mudam, entao cada parede e
    construida uma vez e guardada com o renderizador, que a chaveia por bioma, lado e
    tamanho — a mesma disciplina dos gradientes de ceu.
    """

    def draw(self, renderer: render.Renderer, textures: dict[str, pygame.Surface], biome: Biome) -> None:
        """Cobre as laterais do canvas. Sem sobra horizontal (tela 2:3), nao faz nada."""
        vp = config.viewport()
        left_rect, right_rect = vp.left_band, vp.right_band
        if left_rect.width == 0 and right_rect.width == 0:
            return

        # semente diferente por lado: duas paredes identicas em espelho entregariam a
        # simetria de graca e denunciariam a repeticao.
        for rect, seed in ((left_rect, 0), (right_rect, 1000)):
            if not rect.width:
                continue
            image = self._band(renderer, textures, biome, seed)
            renderer.draw(image, rect.topleft, pygame.Rect(0, 0, rect.width, rect.height))

    def _band(
        self, renderer: render.Renderer, textures: dict[str, pygame.Surface], biome: Biome, seed: int
    ) -> render.Image:
        vp = config.viewport()
        ground_y = config.ground_y()
        width = max(vp.left_band.width, vp.right_band.width)
        return renderer.image(
            ("band", biome.id, seed, width, vp.height, ground_y),
            lambda: _build(width, vp.height, ground_y, biome, textures, seed),
        )


def _build(
    width: int,
    height: int,
    ground_y: int,
    biome: Biome,
    textures: dict[str, pygame.Surface],
    seed: int,
) -> pygame.Surface:
    """Monta uma parede de terra opaca com as camadas empilhadas do bioma.

    Duas ancoras, e ambas importam. A crosta (borda + solo) fica no topo do canvas,
    marcando a superficie la em cima; o miolo e a camada profunda, que e onde os
    veios de minerio aparecem. E na linha do chao da area jogavel — a mesma que
    `Ground.draw` usa — vai outra fileira de borda, para a terra parecer continua de
    uma borda a outra, com solo logo abaixo dela.

    As duas ancoras nao compartilham grade: `ground_y` depende da faixa de ceu e
    quase nunca e multiplo do bloco. Por isso a faixa e preenchida com a camada
    profunda primeiro, e as fileiras de cada ancora sao desenhadas por cima.
    """
    band = pygame.Surface((width, height))  # sem SRCALPHA: opacidade e requisito (R24.4)
    main = textures[biome.block_main]
    edge = textures[biome.block_edge]
    deep = textures[DEEP_BLOCK[biome.id]]
    block = main.get_width()

    for y in range(0, height, block):
        _tile_row(band, deep, y, width, block)

    _tile_row(band, edge, 0, width, block)
    for row in range(TOPSOIL_ROWS):
        _tile_row(band, main, (row + 1) * block, width, block)

    y = ground_y + block
    while y < height and (y - ground_y) <= TOPSOIL_ROWS * block:
        _tile_row(band, main, y, width, block)
        y += block
    _tile_row(band, edge, ground_y, width, block)

    x = ORE_VEIN_PERIOD // 2
    idx = seed
    while x < width:
        for color, rect in decor.ore_vein_shapes(x, idx, height):
            pygame.draw.rect(band, color, rect)
        x += ORE_VEIN_PERIOD
        idx += 1
    return band


def _tile_row(band: pygame.Surface, texture: pygame.Surface, y: int, width: int, block: int) -> None:
    x = 0
    while x < width:
        band.blit(texture, (x, y))
        x += block
