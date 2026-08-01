"""Instrumentacao de desempenho: medicao por frame e sobreposicao de diagnostico (R30).

Desligada por padrao. So e ligada quando a variavel de ambiente `BLOCKY_PERF` esta
definida com um valor diferente de vazio e de "0" — assim o custo em producao e uma
comparacao contra `None` por frame, e nenhuma medicao entra no caminho quente (R30.2).

O ponto de medir e nao otimizar no escuro: os numeros produzidos aqui (no aparelho) e
por `scripts/benchmark.py` (no CI) sao o que prova que cada task de otimizacao da v3
funcionou, em vez de supor. Ver specs/v3/design.md secao 39.
"""

import gc
import os
import time

from src import pixelfont, render

ENV_VAR = "BLOCKY_PERF"
WINDOW_FRAMES = 60
"""Tamanho da janela da media movel: ~1 segundo a 60 FPS."""

GC_THRESHOLD = (50_000, 50, 50)
"""Limiares do coletor ciclico depois de `tune_gc()`, contra os (700, 10, 10) padrao.

Setenta vezes mais alocacoes liquidas de contentor entre varreduras da geracao 0. Com
a disciplina de alocacao da task 58 no lugar, o laco em regime permanente produz um
saldo liquido proximo de zero, entao o limiar alto adia a varredura para muito alem da
duracao de uma partida."""

_OVERLAY_MARGIN = 6
_OVERLAY_SCALE = 2
_OVERLAY_COLOR = (255, 240, 120)
_OVERLAY_SHADOW = (20, 16, 10)
_LINE_SPACING = 2


def enabled() -> bool:
    """Indica se a instrumentacao foi ligada por variavel de ambiente (R30.2)."""
    return os.environ.get(ENV_VAR, "") not in ("", "0")


def tune_gc() -> None:
    """Tira o coletor ciclico do caminho do frame (R27.3). Chamar ao fim da inicializacao.

    Sao tres passos, nessa ordem:

    1. `gc.collect()` — recolhe o lixo da propria inicializacao antes de congelar, para
       nao congelar justamente o que deveria ser jogado fora.
    2. `gc.freeze()` — move tudo que sobrou para a geracao permanente, que o coletor nao
       percorre. Quase todo o jogo e construido aqui e vive ate o fim (texturas, atlas,
       glifos, definicoes de bioma), entao isso remove de uma vez a maior parte do
       trabalho de qualquer varredura futura.
    3. `gc.set_threshold(*GC_THRESHOLD)` — o que ainda for varrido, sera muito mais raro.

    `gc.disable()` foi descartado de proposito: acabaria com as pausas, mas qualquer
    ciclo criado em tempo de execucao vazaria pelo resto da sessao. Elevar o limiar
    mantem a rede de seguranca e adia a varredura para alem de uma partida inteira
    (design secao 36).

    Efeito colateral que importa em teste: o congelamento e permanente e global. Quem
    chama isto fora do jogo (a suite, por criar `Game` centenas de vezes) precisa
    desfaze-lo com `gc.unfreeze()` e devolver os limiares."""
    gc.collect()
    gc.freeze()
    gc.set_threshold(*GC_THRESHOLD)


class _MovingAverage:
    """Media movel de janela fixa, sem alocar nada por amostra.

    Usa um buffer circular pre-alocado e uma soma corrente: adicionar uma amostra e
    uma escrita, duas somas e um incremento de indice. Uma implementacao ingenua
    (lista que cresce e `sum()` a cada leitura) alocaria por frame, que e exatamente
    o que a v3 esta tentando eliminar (design secao 36).
    """

    __slots__ = ("_buffer", "_count", "_index", "_total")

    def __init__(self, size: int) -> None:
        """Cria a janela com `size` amostras, todas zeradas."""
        self._buffer = [0.0] * max(size, 1)
        self._index = 0
        self._count = 0
        self._total = 0.0

    def add(self, value: float) -> None:
        """Registra uma amostra, descartando a mais antiga quando a janela esta cheia."""
        self._total += value - self._buffer[self._index]
        self._buffer[self._index] = value
        self._index = (self._index + 1) % len(self._buffer)
        self._count = min(self._count + 1, len(self._buffer))

    @property
    def average(self) -> float:
        """Media das amostras da janela, ou 0.0 enquanto nenhuma foi registrada."""
        return self._total / self._count if self._count else 0.0


class FrameProfiler:
    """Acumula tempo de atualizacao, tempo de desenho e duracao do frame (R30.1).

    O uso previsto por frame e: `frame(ms)` com o retorno de `Clock.tick()`, depois
    `begin()` antes de `update()`, `end_update()` logo apos, e `end_draw()` apos o
    desenho. Cada `end_*` mede desde a ultima marcacao e reinicia o cronometro, entao
    nao ha necessidade de chamar `begin()` de novo entre as duas etapas.
    """

    __slots__ = ("_draw_ms", "_frame_ms", "_mark", "_update_ms", "backend")

    def __init__(self, window: int = WINDOW_FRAMES) -> None:
        """Cria o profiler com janelas de media movel de `window` frames."""
        self._update_ms = _MovingAverage(window)
        self._draw_ms = _MovingAverage(window)
        self._frame_ms = _MovingAverage(window)
        self._mark = 0.0
        self.backend = "surface"
        """Caminho de renderizacao em uso, preenchido pela camada de render (R26.5)."""

    def frame(self, frame_ms: float) -> None:
        """Registra a duracao real do frame, tal como reportada pelo relogio do pygame."""
        self._frame_ms.add(frame_ms)

    def begin(self) -> None:
        """Inicia a cronometragem de uma etapa do frame."""
        self._mark = time.perf_counter()

    def end_update(self) -> None:
        """Fecha a medicao da atualizacao e reinicia o cronometro para o desenho."""
        self._update_ms.add(self._split_ms())

    def end_draw(self) -> None:
        """Fecha a medicao do desenho."""
        self._draw_ms.add(self._split_ms())

    def _split_ms(self) -> float:
        """Devolve os milissegundos desde a ultima marcacao e remarca o cronometro."""
        now = time.perf_counter()
        elapsed = (now - self._mark) * 1000.0
        self._mark = now
        return elapsed

    @property
    def update_ms(self) -> float:
        """Tempo medio de `update()` na janela, em milissegundos."""
        return self._update_ms.average

    @property
    def draw_ms(self) -> float:
        """Tempo medio de desenho na janela, em milissegundos."""
        return self._draw_ms.average

    @property
    def fps(self) -> float:
        """Taxa de quadros media derivada da duracao real dos frames."""
        average = self._frame_ms.average
        return 1000.0 / average if average > 0 else 0.0

    def lines(self) -> list[str]:
        """Monta as linhas da sobreposicao, em maiusculas (a fonte bitmap nao tem minusculas)."""
        return [
            f"FPS {self.fps:.0f}",
            f"UPD {self.update_ms:.1f}MS",
            f"DRW {self.draw_ms:.1f}MS",
            self.backend.upper(),
        ]


def draw_overlay(renderer: render.Renderer, profiler: FrameProfiler) -> None:
    """Desenha a sobreposicao de diagnostico no canto superior esquerdo (R30.1).

    Usa a fonte bitmap propria (`pixelfont`), guardada como imagem por (texto, escala,
    cor) — entao so o primeiro frame de cada valor distinto paga a renderizacao dos
    glifos, e o custo da sobreposicao nao mascara o que ela esta medindo.
    """
    y = _OVERLAY_MARGIN
    for line in profiler.lines():
        shadow = _glyphs(renderer, line, _OVERLAY_SHADOW)
        main = _glyphs(renderer, line, _OVERLAY_COLOR)
        renderer.draw(shadow, (_OVERLAY_MARGIN + 1, y + 1))
        renderer.draw(main, (_OVERLAY_MARGIN, y))
        y += pixelfont.GLYPH_H * _OVERLAY_SCALE + _LINE_SPACING


def _glyphs(renderer: render.Renderer, line: str, color: tuple[int, int, int]) -> render.Image:
    """Imagem de uma linha da sobreposicao, guardada com o renderizador."""
    return renderer.image(("perf", line, color), lambda: pixelfont.render(line, _OVERLAY_SCALE, color))
