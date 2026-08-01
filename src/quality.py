"""Qualidade adaptativa: o jogo mede o proprio desempenho e se ajusta (R29).

Nem todo aparelho vai sustentar 60 FPS depois de tudo que a v3 fez. A alternativa a
este modulo nao e "rodar liso em todo lugar" — e engasgar num aparelho modesto e deixar
o jogador com a impressao de que o jogo e ruim. Aqui o jogo desliga decoracao ate
caber.

**A regra que nao se negocia (R29.3).** Nenhum nivel toca em velocidade de coluna,
tamanho de abertura, hitbox ou pontuacao. O que se desliga e sempre decorativo, em
ordem crescente de importancia visual: primeiro os mobs e a camada distante do
parallax, depois o parallax inteiro. Isso e o que preserva a comparabilidade dos
recordes que R24 garante — dois jogadores em aparelhos diferentes continuam jogando o
mesmo jogo, um deles com menos enfeite.

**Nivel BAIXO reduz o desenho, nao a simulacao.** `render_fps` cai para 30, e os
passos logicos continuam sendo 60 por segundo (o acumulador da secao 37 cuida disso).
Menos quadros, mesma velocidade de jogo — que e precisamente a distincao que R28
existe para fazer.

Ver specs/v3/design.md secao 38.
"""

import json
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

from src import storage

FILENAME = "quality.json"
"""Ao lado do `highscore.json`, no diretorio gravavel por plataforma (R29.5)."""


class Level(IntEnum):
    """Os tres niveis, ordenados: `BAIXO < MEDIO < ALTO`.

    `IntEnum` porque a ordem e usada — subir e descer de nivel sao comparacoes, e
    "esta abaixo do maximo" e um `<`."""

    BAIXO = 0
    MEDIO = 1
    ALTO = 2


@dataclass(frozen=True)
class Settings:
    """O que cada nivel liga e desliga. Tudo aqui e decorativo, por construcao (R29.3)."""

    mobs: bool
    """Mobs decorativos das faixas (`mobs.py`, R25.3)."""

    far_parallax: bool
    """Camada distante do parallax — nuvens, estalactites, poças de lava."""

    near_parallax: bool
    """Camada proxima — colinas, veios de minerio, pilares."""

    particles: int
    """Particulas por explosao de colisao (`particles.burst`, R3.2)."""

    render_fps: int
    """Quadros desenhados por segundo. A simulacao continua a 60 passos logicos."""


SETTINGS: dict[Level, Settings] = {
    Level.ALTO: Settings(mobs=True, far_parallax=True, near_parallax=True, particles=16, render_fps=60),
    Level.MEDIO: Settings(mobs=False, far_parallax=False, near_parallax=True, particles=8, render_fps=60),
    Level.BAIXO: Settings(mobs=False, far_parallax=False, near_parallax=False, particles=4, render_fps=30),
}

WINDOW_FRAMES = 120
"""Janela de medicao para descer de nivel: ~2 s a 60 FPS (R29.1).

Curta o bastante para que os primeiros segundos ruins nao se arrastem, longa o
bastante para que um engasgo isolado nao decida nada — um travamento de 300 ms no meio
de 120 quadros derruba a media de 60 para ~52 FPS, bem acima do limiar de queda."""

RISE_WINDOW_FRAMES = 300
"""Janela para subir: ~5 s, mais que o dobro da de descida (R29.4).

Assimetrica de proposito. Descer e barato e reversivel; subir cedo demais devolve o
engasgo que motivou a descida, e o jogador ve o cenario piscando entre dois niveis."""

DROP_FPS = 50.0
"""Media abaixo disto na janela inteira derruba um nivel (R29.2)."""

RISE_FPS = 58.0
"""Media acima disto sobe um nivel. A folga de 8 FPS para o limiar de queda e a
histerese propriamente dita (R29.4): entre 50 e 58 nada acontece, e e essa faixa morta
que impede um aparelho no limite de alternar para sempre."""


def load_level(path: Path | None = None) -> Level:
    """Le o nivel gravado, ou ALTO se nao houver um utilizavel (R29.5, R29.6).

    Mesma disciplina de `score.load_highscore`: arquivo ausente, ilegivel, com JSON
    quebrado ou com um nivel que nao existe resulta em ALTO e redeteccao. Um arquivo
    de preferencia corrompido nunca pode impedir o jogo de abrir — e comecar no maximo
    e a escolha certa por ser a unica que se corrige sozinha em dois segundos, ao
    contrario de comecar no minimo."""
    path = path if path is not None else _default_path()
    try:
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
        return Level[str(data["level"])]
    except (OSError, ValueError, KeyError, TypeError):
        return Level.ALTO


def save_level(level: Level, path: Path | None = None) -> None:
    """Grava o nivel detectado (R29.5). Falha de escrita e ignorada, como no recorde."""
    path = path if path is not None else _default_path()
    try:
        with open(path, "w", encoding="utf-8") as file:
            json.dump({"level": level.name}, file)
    except OSError:
        pass


def _default_path() -> Path:
    """Resolvido a cada chamada, e nao como default de parametro, para acompanhar uma
    troca de plataforma em tempo de execucao — igual a `score._default_path`."""
    return storage.save_dir() / FILENAME


class Quality:
    """Mede a taxa de quadros em JOGANDO e ajusta o nivel (R29.1, R29.2, R29.4).

    O estado sao tres numeros: quantos quadros ja entraram na janela, quanto tempo eles
    somaram, e o nivel atual. Sem lista, sem alocacao por quadro — esta medicao roda no
    caminho quente do laco e nao pode ser ela mesma o custo (secao 36 do design).
    """

    __slots__ = ("_count", "_total_ms", "dirty", "level")

    def __init__(self, level: Level = Level.ALTO) -> None:
        """Comeca no nivel dado — o gravado da sessao anterior, no jogo (R29.5)."""
        self.level = level
        self.dirty = False
        """Nivel mudou e ainda nao foi gravado. Ver `Game._flush_quality`: gravar aqui
        seria escrita em disco dentro do frame de JOGANDO, que R27.5 proibe."""
        self._count = 0
        self._total_ms = 0.0

    @property
    def settings(self) -> Settings:
        """O que esta ligado no nivel atual."""
        return SETTINGS[self.level]

    @property
    def render_fps(self) -> int:
        """Limite de quadros por segundo para o relogio do laco principal."""
        return self.settings.render_fps

    def frame(self, frame_ms: float, playing: bool) -> None:
        """Registra um quadro e, ao fechar a janela, decide se troca de nivel.

        `playing` e falso fora de JOGANDO, e ai a janela e **descartada**, nao apenas
        pausada (R29.1): a tela PRONTO desenha menos e o GAME_OVER congela o cenario,
        entao as duas medem outra coisa. Pior, uma janela que atravessasse a pausa
        mediria o tempo parado como quadros lentissimos e derrubaria o nivel de um
        aparelho que estava indo bem.
        """
        if not playing:
            self._reset_window()
            return

        self._count += 1
        self._total_ms += frame_ms
        if self._count < WINDOW_FRAMES:
            return

        # a janela curta so pode descer; a longa, que a contem, tambem pode subir. E a
        # assimetria de R29.4 escrita como duas janelas em vez de dois limiares.
        fps = self._fps()
        long_window = self._count >= RISE_WINDOW_FRAMES
        if fps < DROP_FPS and self.level > Level.BAIXO:
            self._change(Level(self.level - 1))
        elif long_window and fps > RISE_FPS and self.level < Level.ALTO:
            self._change(Level(self.level + 1))
        elif not long_window:
            return  # janela curta sem queda: segue medindo, sem reiniciar a contagem
        self._reset_window()

    def _change(self, level: Level) -> None:
        """Troca o nivel e marca para gravacao."""
        self.level = level
        self.dirty = True

    def _fps(self) -> float:
        """Taxa media da janela, ou 0 se nada foi medido."""
        return 1000.0 * self._count / self._total_ms if self._total_ms > 0 else 0.0

    def _reset_window(self) -> None:
        """Recomeca a medicao do zero."""
        self._count = 0
        self._total_ms = 0.0
