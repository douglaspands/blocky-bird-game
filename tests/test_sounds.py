import pygame

from src.sounds import ANDROID_MIXER_BUFFER, SAMPLE_RATE, SoundManager


def test_mixer_init_uses_larger_buffer_on_android(monkeypatch):
    """Buffer pequeno demais no Android estoura/crepita (R8.4, R14.6, design secao 11)."""
    calls = []

    def fake_init(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr("src.sounds.is_android", lambda: True)
    monkeypatch.setattr(pygame.mixer, "init", fake_init)

    SoundManager()

    assert calls == [{"frequency": SAMPLE_RATE, "size": -16, "channels": 1, "buffer": ANDROID_MIXER_BUFFER}]


def test_mixer_init_uses_default_buffer_off_android(monkeypatch):
    calls = []

    def fake_init(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr("src.sounds.is_android", lambda: False)
    monkeypatch.setattr(pygame.mixer, "init", fake_init)

    SoundManager()

    assert calls == [{"frequency": SAMPLE_RATE, "size": -16, "channels": 1}]
