"""Sintese de sons 8-bit via stdlib (sem numpy, R9.2) e controle de mudo (R8)."""

import array
import math
import random

import pygame

SAMPLE_RATE = 44100


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
        self.muted = False
        self.audio_ok = False
        try:
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1)
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
