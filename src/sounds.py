"""Sintese de sons 8-bit via stdlib (sem numpy, R9.2) e controle de mudo (R8)."""

import array
import math
import random
from typing import TypedDict

import pygame

from src.storage import is_android

SAMPLE_RATE = 44100
ANDROID_MIXER_BUFFER = 1024


class MixerParams(TypedDict, total=False):
    """Argumentos nomeados de `pygame.mixer.init`/`pre_init` que o jogo define.

    Tipado, e nao um `dict[str, int]`, para que o desempacotamento nas duas chamadas
    seja conferido pelo `ty` contra a assinatura real do pygame — que tem tambem
    parametros de outros tipos (`devicename`)."""

    frequency: int
    size: int
    channels: int
    buffer: int


def mixer_params() -> MixerParams:
    """Parametros do mixer: 44.1 kHz, 16 bits com sinal, mono.

    O buffer maior so no Android, onde o padrao do pygame e pequeno demais para o
    caminho de audio do aparelho e o som sai crepitando (R8.4, R14.6, design secao 11).
    No desktop a chave nem e passada, para continuar valendo o padrao do pygame."""
    params: MixerParams = {"frequency": SAMPLE_RATE, "size": -16, "channels": 1}
    if is_android():
        params["buffer"] = ANDROID_MIXER_BUFFER
    return params


def pre_init() -> None:
    """Fixa os parametros do mixer ANTES de `pygame.init()` (R27.6, design secao 40).

    A v2 inicializava o mixer duas vezes: `pygame.init()` o subia com os parametros
    padrao e, logo em seguida, `SoundManager.__init__` o derrubava e o subia de novo
    com os parametros certos. Abrir um dispositivo de audio e caro — no Android, dezenas
    de milissegundos —, e fazer isso duas vezes na abertura era tempo de inicializacao
    jogado fora, alem de expor uma janela em que o dispositivo esta aberto com o buffer
    errado.

    `pre_init` nao abre nada: so guarda o que o `init` seguinte vai usar. Por isso e
    inofensiva quando o audio nao existe — a falha continua acontecendo no `init`, onde
    ja e tratada."""
    pygame.mixer.pre_init(**mixer_params())


def _new_buffer(n: int) -> array.array:
    return array.array("h", bytes(2 * n))


def _square_sweep(freq_start: float, freq_end: float, duration_ms: int, volume: float = 0.4) -> array.array:
    """Onda quadrada com sweep de frequencia e decaimento linear (flap, portal)."""
    n = int(SAMPLE_RATE * duration_ms / 1000)
    samples = _new_buffer(n)
    for i in range(n):
        progress = i / n
        freq = freq_start + (freq_end - freq_start) * progress
        phase = 2 * math.pi * freq * (i / SAMPLE_RATE)
        square = 1.0 if math.sin(phase) >= 0 else -1.0
        envelope = 1.0 - progress
        samples[i] = int(square * envelope * volume * 32767)
    return samples


def _double_ping(freq1: float, freq2: float, duration_ms: int, volume: float = 0.4) -> array.array:
    """Dois pings de onda quadrada em sequencia, estilo XP orb (score)."""
    n = int(SAMPLE_RATE * duration_ms / 1000)
    half = n // 2
    samples = _new_buffer(n)
    for i in range(n):
        if i < half:
            freq, progress = freq1, i / half
        else:
            freq, progress = freq2, (i - half) / max(n - half, 1)
        phase = 2 * math.pi * freq * (i / SAMPLE_RATE)
        square = 1.0 if math.sin(phase) >= 0 else -1.0
        envelope = 1.0 - progress
        samples[i] = int(square * envelope * volume * 32767)
    return samples


def _white_noise(duration_ms: int, volume: float = 0.5) -> array.array:
    """Ruido branco com decaimento (hit / bloco quebrando)."""
    n = int(SAMPLE_RATE * duration_ms / 1000)
    samples = _new_buffer(n)
    for i in range(n):
        envelope = 1.0 - i / n
        samples[i] = int(random.uniform(-1, 1) * envelope * volume * 32767)
    return samples


class SoundManager:
    def __init__(self) -> None:
        """Assume o mixer que `pre_init` + `pygame.init()` ja deixaram pronto.

        So inicializa por conta propria se ele nao estiver de pe — o que acontece quando
        alguem constroi o `SoundManager` fora do jogo (um teste, um script) e quando o
        `pygame.init()` nao conseguiu abrir o dispositivo. No segundo caso a tentativa
        aqui tambem falha, e o jogo segue mudo, como desde a v1 (R8.4)."""
        self.muted = False
        self.audio_ok = False
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(**mixer_params())
            self.audio_ok = True
        except pygame.error:
            self.audio_ok = False

        self._sounds: dict[str, pygame.mixer.Sound] = {}
        if self.audio_ok:
            self._sounds = {
                "flap": pygame.mixer.Sound(buffer=_square_sweep(300, 500, 80)),
                "score": pygame.mixer.Sound(buffer=_double_ping(800, 1200, 120)),
                "hit": pygame.mixer.Sound(buffer=_white_noise(200)),
                "portal": pygame.mixer.Sound(buffer=_square_sweep(900, 200, 400)),
            }

    def play(self, name: str) -> None:
        """Toca o som se o audio estiver disponivel e nao estiver mudo (R8.3, R8.4)."""
        if self.audio_ok and not self.muted:
            self._sounds[name].play()

    def toggle_mute(self) -> None:
        self.muted = not self.muted
