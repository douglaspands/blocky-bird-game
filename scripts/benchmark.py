"""Benchmark headless do laco de jogo (R30.3, R30.4).

Roda N frames de cada cenario sem display real (`SDL_VIDEODRIVER=dummy`) e reporta
ms/frame p50 e p95, contagem de draw calls e alocacao de memoria. O objetivo e que
cada task de otimizacao da v3 seja comprovada contra o baseline registrado na secao
30 de `specs/v3/design.md`, em vez de suposta.

Por que p50 e p95, e nao media: num jogo o que estraga a experiencia e a cauda. Um
p95 ruim e um engasgo visivel a cada 20 frames, e a media o esconde. As alocacoes
entram na medicao porque sao a causa mais provavel dessa cauda — medi-las e medir o
mecanismo, nao so o sintoma.

Uso:
    uv run python scripts/benchmark.py
    uv run python scripts/benchmark.py --frames 600
"""

from __future__ import annotations

import argparse
import gc
import os
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame

from src import config
from src.biome import BIOMES
from src.game import Game, GameState

DEFAULT_FRAMES = 300
WARMUP_FRAMES = 60
"""Frames descartados antes de medir: enchem a tela de colunas e aquecem os caches."""

CHURN_FRAMES = 60
"""Frames da passada de memoria: `tracemalloc` e caro, entao a amostra e menor."""

_DRAW_CALLS = 0
_COUNTED_OPS = ("draw", "fill", "clear")
"""Operacoes do renderizador que contam como draw call — as que chegam ao SDL."""


def percentile(samples: list[float], fraction: float) -> float:
    """Percentil por interpolacao linear entre as amostras vizinhas.

    `fraction` vai de 0.0 a 1.0 (0.5 = mediana). Uma lista vazia devolve 0.0, para
    que o benchmark nunca falhe por um cenario que nao produziu amostras.
    """
    if not samples:
        return 0.0
    ordered = sorted(samples)
    if len(ordered) == 1:
        return ordered[0]
    position = fraction * (len(ordered) - 1)
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    weight = position - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


@dataclass(frozen=True)
class Result:
    """Numeros medidos de um cenario."""

    scenario: str
    p50_ms: float
    p95_ms: float
    draw_calls: float
    churn_kb: float

    def as_row(self) -> str:
        """Formata o resultado como linha de tabela markdown, pronta para o design.md."""
        return (
            f"| {self.scenario} | {self.p50_ms:.2f} | {self.p95_ms:.2f} "
            f"| {self.draw_calls:.0f} | {self.churn_kb:.1f} |"
        )


def _measure_churn_kb(game: Game, tick: Callable[[Game], None], frames: int) -> float:
    """Mede a memoria transitoria alocada por frame, em KB.

    Passada separada e proposital: `tracemalloc` deixa o processo varias vezes mais
    lento, entao misturar essa medicao com a de tempo estragaria as duas.

    A tecnica e o pico por frame: `reset_peak()` no inicio do frame e o pico
    reportado no fim dao a marca d'agua da memoria transitoria daquele frame — ou
    seja, o que foi alocado e descartado dentro dele. As alternativas obvias medem a
    coisa errada: `sys.getallocatedblocks()` reporta o saldo liquido (um frame que
    aloca e libera 40 objetos aparece como zero, entao detecta vazamento, nao
    pressao), e a contagem de coletas do `gc` so sobe quando ha excedente liquido de
    objetos-contentores, que um laco equilibrado nunca produz.
    """
    import tracemalloc

    tracemalloc.start()
    try:
        total_kb = 0.0
        for _ in range(frames):
            tick(game)
            baseline, _ = tracemalloc.get_traced_memory()
            tracemalloc.reset_peak()
            game.update()
            game.draw()
            _, peak = tracemalloc.get_traced_memory()
            total_kb += max(peak - baseline, 0) / 1024.0
        return total_kb / frames
    finally:
        tracemalloc.stop()


def _fresh_display() -> None:
    """Reinicia o subsistema de video entre cenarios.

    Sem este reinicio, cada `Game()` novo deixa uma janela e um renderizador para
    tras, e os cenarios medidos depois ficam progressivamente mais lentos — um
    artefato de medicao que nao existe no jogo real.
    """
    pygame.display.quit()
    pygame.display.init()


def _count_draw_calls(game: Game) -> None:
    """Envolve as operacoes de desenho do renderizador do `game` para conta-las.

    Desde a task 50 todo desenho passa pelo renderizador, entao contar aqui e contar
    exatamente o que chega ao SDL — mais fiel que a contagem da v2, que envolvia
    `Surface.blit` e as funcoes de `pygame.draw` e nao enxergava mais nada.
    """

    def wrap(original: Callable[..., object]) -> Callable[..., object]:
        def counted(*args: object, **kwargs: object) -> object:
            global _DRAW_CALLS
            _DRAW_CALLS += 1
            return original(*args, **kwargs)

        return counted

    for name in _COUNTED_OPS:
        setattr(game.renderer, name, wrap(getattr(game.renderer, name)))


def _stop_counting(game: Game) -> None:
    """Desfaz o envolvimento, devolvendo os metodos da classe.

    Nao e higiene opcional: o envolvimento cria um ciclo (renderizador -> atributo ->
    closure -> metodo ligado -> renderizador), entao o renderizador so seria liberado
    numa passada do coletor ciclico. Ela viria depois do `display.quit()` do cenario
    seguinte, e a` destruicao tardia atropelaria a janela nova — o SDL reaproveita os
    ponteiros. Sintoma medido: o segundo cenario morria com
    `error: Parameter 'texture' is invalid`. Quebrando o ciclo aqui, o renderizador e
    liberado por contagem de referencia ainda com o video vivo.
    """
    for name in _COUNTED_OPS:
        game.renderer.__dict__.pop(name, None)


class _NoCollisionGame(Game):
    """Game que nunca colide.

    Sem isso, o cenario terminaria no meio da medicao e passaria a medir a tela de
    GAME_OVER em vez da partida. Uma subclasse, e nao um monkeypatch do metodo, para
    que a checagem de tipos continue valendo sobre a assinatura.
    """

    def _collision_texture(self) -> str | None:
        """Nunca reporta colisao."""
        return None


def _make_game() -> Game:
    """Cria um Game com colisao desativada, para o cenario nao terminar no meio da medicao."""
    return _NoCollisionGame()


def _keep_flying(game: Game) -> None:
    """Mantem a abelha no ar, para que a cena medida seja a de uma partida em curso."""
    if game.bird.pos.y > config.screen_h() * 0.6:
        game.bird.flap()


def _setup_pronto() -> tuple[Game, Callable[[Game], None]]:
    """Cenario: tela inicial, com a abelha flutuando."""
    game = _make_game()
    game.state = GameState.PRONTO
    return game, lambda _: None


def _setup_jogando(biome_index: int) -> Callable[[], tuple[Game, Callable[[Game], None]]]:
    """Cenario: partida em curso num bioma especifico, com colunas na tela."""

    def setup() -> tuple[Game, Callable[[Game], None]]:
        game = _make_game()
        game.state = GameState.JOGANDO
        game.score = BIOMES[biome_index].threshold
        game.biome.update(game.score)
        return game, _keep_flying

    return setup


def _setup_game_over() -> tuple[Game, Callable[[Game], None]]:
    """Cenario: tela de fim com particulas ativas — o pior caso de objetos em cena."""
    game = _make_game()
    game.state = GameState.JOGANDO
    for _ in range(WARMUP_FRAMES):
        game.update()
    game.state = GameState.GAME_OVER
    texture = game.textures[game.biome.current.block_main]

    def refill(g: Game) -> None:
        if not g.particles.particles:
            g.particles.burst(g.bird.rect.center, texture)

    refill(game)
    return game, refill


SCENARIOS: dict[str, Callable[[], tuple[Game, Callable[[Game], None]]]] = {
    "PRONTO": _setup_pronto,
    "JOGANDO overworld": _setup_jogando(0),
    "JOGANDO cave": _setup_jogando(1),
    "JOGANDO nether": _setup_jogando(2),
    "GAME_OVER": _setup_game_over,
}


def run_scenario(name: str, frames: int) -> Result:
    """Mede um cenario por `frames` frames, apos um aquecimento descartado."""
    global _DRAW_CALLS

    _fresh_display()
    game, tick = SCENARIOS[name]()
    _count_draw_calls(game)
    try:
        for _ in range(WARMUP_FRAMES):
            tick(game)
            game.update()
            game.draw()

        gc.collect()
        samples: list[float] = []
        _DRAW_CALLS = 0

        for _ in range(frames):
            tick(game)
            start = time.perf_counter()
            game.update()
            game.draw()
            samples.append((time.perf_counter() - start) * 1000.0)

        draw_calls = _DRAW_CALLS / frames
        churn_kb = _measure_churn_kb(game, tick, min(frames, CHURN_FRAMES))
    finally:
        _stop_counting(game)

    return Result(name, percentile(samples, 0.5), percentile(samples, 0.95), draw_calls, churn_kb)


def main() -> None:
    """Roda todos os cenarios e imprime a tabela markdown do design.md."""
    parser = argparse.ArgumentParser(description="Benchmark headless do Blocky Bee")
    parser.add_argument("--frames", type=int, default=DEFAULT_FRAMES, help="frames medidos por cenario")
    args = parser.parse_args()

    results = [run_scenario(name, args.frames) for name in SCENARIOS]

    print(f"\nBenchmark — {args.frames} frames por cenario, apos {WARMUP_FRAMES} de aquecimento\n")
    print("| Cenario | p50 (ms) | p95 (ms) | draw calls/frame | KB transitorios/frame |")
    print("|---|---|---|---|---|")
    for result in results:
        print(result.as_row())
    print()


if __name__ == "__main__":
    main()
