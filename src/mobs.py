"""Mobs decorativos das faixas (R25.3, R25.4).

Nove mobs voxel — creeper, bruxa e aldeao no Overworld; enderman, aranha e esqueleto
na Cave; ghast, blaze e piglin no Nether — habitam **exclusivamente** as faixas
decorativas: a de ceu, acima da area jogavel, e as laterais, o corte transversal do
subsolo. Nunca a area jogavel. Isso nao e disciplina de quem desenha: cada mob e
recortado contra o retangulo da faixa antes de ir para a tela, e as faixas sao
disjuntas de `viewport.play` por construcao (`viewport.py`), entao um pixel de mob
dentro do campo de jogo nao tem por onde acontecer.

O recorte tambem e o que faz a lateral parecer um poco de mineracao de verdade: o mob
some devagar atras da parede de terra em vez de piscar ao cruzar a borda.

**R25.4 e a restricao que importa, e este cabecalho de imports e a prova dela.**
`mobs.py` nao importa `game`, `bird`, `pipes`, `score` nem `biome` — recebe o id do
bioma, um deslocamento e o `Viewport` ativo, e mais nada. Nao ha caminho pelo qual um
mob colida, pontue ou mude velocidade, porque nao ha caminho pelo qual ele *alcance*
qualquer uma dessas coisas. E uma dependencia de mao unica, e e o que torna o
requisito verificavel por teste em vez de por inspecao.

Ver specs/v3/design.md secao 35.
"""

import random
from typing import NamedTuple

import pygame

from src import config, render, textures

MOB_FACTOR = 0.15
"""Deriva propria dos mobs, como fracao da velocidade do bioma.

Metade da camada distante do parallax (`decor.FAR_FACTOR`, 0.3) — quanto mais lento,
mais longe. E o que os coloca claramente atras do cenario e o que impede que algo no
fundo compita com a coluna pela atencao do jogador."""

MOB_SIZE = 32
"""Lado do sprite desenhado, em pixels de canvas.

O dobro exato dos 16x16 de origem: escala inteira, sem pixel de largura desigual, o
mesmo criterio com que `textures.scale_pixel_perfect` amplia os blocos. Menor que os
48 da abelha de proposito — o mob e cenario, e nao pode ser confundido com o jogador.
"""

IDLE_FRAMES = (0, 1)
IDLE_FRAME_INTERVAL = 6
"""Frames entre os dois quadros de idle: a mesma cadencia da asa da abelha
(`bird.WING_FRAME_INTERVAL`).

Repetida aqui em vez de importada, e a repeticao e o ponto: `mobs.py` nao depende de
nenhum modulo de jogo (R25.4), e uma constante de seis linhas nao vale abrir a
primeira excecao a isso."""

SKY_PERIOD = 190
SIDE_PERIOD = 160
"""Distancia horizontal entre dois mobs vizinhos do mesmo campo.

Sao os unicos numeros de espacamento: o desvio sorteado dentro de cada periodo nunca
passa de `period - MOB_SIZE`, entao dois vizinhos ficam sempre a pelo menos um sprite
de distancia e nenhum par se sobrepoe — nem na emenda do ciclo."""

FIELD_SPANS = 3
"""Quantas larguras de canvas um campo cobre antes de se repetir, no minimo.

Mesmo acordo entre memoria e repeticao das faixas de parallax (`decor.STRIP_SPANS`),
so que aqui o custo e ainda menor: um campo e uma tupla de posicoes, nao pixels."""

MIN_SLOTS = 6
"""Piso de posicoes por campo, para que as tres variedades do bioma (R25.3) aparecam
mesmo num canvas estreito, onde a conta de `FIELD_SPANS` daria menos que isso."""

BIOME_MOBS: dict[str, tuple[str, str, str]] = {
    "overworld": ("creeper", "witch", "villager"),
    "cave": ("enderman", "spider", "skeleton"),
    "nether": ("ghast", "blaze", "piglin"),
}
"""Tres variedades por bioma (R25.3), chaveadas pelo id do bioma — o mesmo padrao de
`bands.DEEP_BLOCK` e de `decor._LAYERS`, para que a decoracao nao vire campo de
`Biome`."""


class _Slot(NamedTuple):
    """Uma posicao do campo: qual mob, onde, e em que fase do idle."""

    kind: str
    x: int
    """Coordenada no campo, nao na tela: o desenho subtrai o deslocamento e da a volta."""
    y: int
    phase: int
    """0 ou 1. Sem ela os mobs da tela piscariam em unissono, que e o jeito mais rapido
    de um cenario parecer mecanico."""


_FIELDS: dict[object, tuple[_Slot, ...]] = {}
"""Campos ja sorteados, memoizados pela chave.

Vale como cache de modulo pela mesma razao de `decor._STRIP_TOPS`: e uma funcao pura
da chave e o valor sao numeros, nunca pixels. Duas telas de mesmo tamanho no mesmo
bioma tem o mesmo campo, tenham sido desenhadas por qual `MobField` for."""


def _sprite(renderer: render.Renderer, kind: str, frame: int) -> render.Image:
    """Sprite de um (mob, frame de idle), construido uma vez (R27.2)."""
    return renderer.image(
        ("mob", kind, frame),
        lambda: textures.scale_pixel_perfect(textures.MOB_MAKERS[kind](frame), MOB_SIZE),
    )


def precompute(renderer: render.Renderer) -> None:
    """Constroi os 18 sprites de uma vez, fora do frame.

    Chamada na inicializacao e de novo apos um redimensionamento, que descarta o cache
    de imagens do renderizador — mesma disciplina de `bird.precompute_sprites`. Os
    sprites nao dependem do canvas, mas `forget_images` nao sabe distinguir isso.
    """
    for kind in textures.MOB_MAKERS:
        for frame in IDLE_FRAMES:
            _sprite(renderer, kind, frame)


def _build_field(
    biome_id: str, band: str, period: int, top: int, height: int, canvas_w: int
) -> tuple[_Slot, ...]:
    """Sorteia as posicoes de um campo, uma unica vez por chave.

    O sorteio percorre as variedades em rodizio (`index % 3`) em vez de escolher ao
    acaso: e o que garante que as tres do bioma estejam presentes em qualquer campo,
    em vez de deixar isso por conta da sorte de um canvas estreito.
    """
    kinds = BIOME_MOBS[biome_id]
    rng = random.Random(f"{biome_id}:{band}")
    count = max(MIN_SLOTS, -(-FIELD_SPANS * canvas_w // period))
    slots = []
    for index in range(count):
        x = index * period + rng.randrange(period - MOB_SIZE)
        y = top + rng.randrange(height - MOB_SIZE + 1)
        slots.append(_Slot(kinds[index % len(kinds)], x, y, rng.randrange(len(IDLE_FRAMES))))
    return tuple(slots)


def _field(biome_id: str, band: str, period: int, top: int, height: int, canvas_w: int) -> tuple[_Slot, ...]:
    """Campo memoizado. A chave e tudo de que o sorteio depende."""
    key = (biome_id, band, period, top, height, canvas_w)
    field = _FIELDS.get(key)
    if field is None:
        field = _build_field(biome_id, band, period, top, height, canvas_w)
        _FIELDS[key] = field
    return field


class MobField:
    """Os mobs em cena: deriva propria, idle proprio, e nenhuma outra informacao.

    Uma instancia por partida, como `DecorManager`. O estado inteiro sao dois numeros —
    o quanto o campo ja derivou e em que quadro de idle ele esta.
    """

    def __init__(self) -> None:
        """Inicia sem deriva, no primeiro quadro de idle."""
        self.scrolled = 0.0
        self.frame = 0
        self._frame_timer = 0

    def update(self, speed: float) -> None:
        """Avanca a deriva e a animacao de idle.

        `speed` zero congela a deriva e deixa o idle correndo, que e o que a tela
        PRONTO pede: o cenario respira antes de a partida comecar, sem sair do lugar.
        """
        self.scrolled += speed * MOB_FACTOR
        self._frame_timer += 1
        if self._frame_timer >= IDLE_FRAME_INTERVAL:
            self._frame_timer = 0
            self.frame = 1 - self.frame

    def draw_sky(self, renderer: render.Renderer, biome_id: str) -> None:
        """Mobs da faixa de ceu. Desenhados antes das colunas (design secao 32.6)."""
        band = config.viewport().sky_band
        self._draw(renderer, biome_id, "sky", SKY_PERIOD, band.top, band.height, (band,))

    def draw_sides(self, renderer: render.Renderer, biome_id: str) -> None:
        """Mobs das faixas laterais. Desenhados **depois** das faixas, que sao opacas.

        Um unico campo alimenta os dois lados, e nao um por lado: assim o mob que sai
        pela esquerda da faixa direita e o mesmo que, muito depois, entra pela direita
        da esquerda — como se tivesse atravessado a terra por tras do poco.
        """
        vp = config.viewport()
        self._draw(renderer, biome_id, "side", SIDE_PERIOD, 0, vp.height, (vp.left_band, vp.right_band))

    def _draw(
        self,
        renderer: render.Renderer,
        biome_id: str,
        band: str,
        period: int,
        top: int,
        height: int,
        clips: tuple[pygame.Rect, ...],
    ) -> None:
        """Desenha o campo recortado contra as faixas `clips`.

        A faixa que nao existe tem largura ou altura zero (tela 2:3) e cai fora aqui —
        nada e sorteado e nada e desenhado. A faixa mais baixa que um sprite tambem: um
        mob cortado ao meio na horizontal, contra o ceu, leria como defeito, ao
        contrario do corte vertical da lateral, que le como estar atras da terra.
        """
        visible_clips = [clip for clip in clips if clip.width > 0 and clip.height > 0]
        if not visible_clips or height < MOB_SIZE:
            return

        canvas_w = renderer.size[0]
        field = _field(biome_id, band, period, top, height, canvas_w)
        span = len(field) * period
        offset = round(self.scrolled) % span

        for slot in field:
            x = (slot.x - offset) % span
            if x >= canvas_w:
                # alem da borda direita do canvas so pode aparecer pelo outro lado: e o
                # mob que ja deu a volta e esta entrando com parte do corpo de fora.
                x -= span
            rect = pygame.Rect(x, slot.y, MOB_SIZE, MOB_SIZE)
            image: render.Image | None = None
            for clip in visible_clips:
                shown = rect.clip(clip)
                if not shown.width or not shown.height:
                    continue
                if image is None:  # so paga a consulta quando ha mesmo o que desenhar
                    image = _sprite(renderer, slot.kind, (self.frame + slot.phase) % len(IDLE_FRAMES))
                area = pygame.Rect(shown.x - rect.x, shown.y - rect.y, shown.width, shown.height)
                renderer.draw(image, shown.topleft, area)
