import pygame

from src import sounds
from src.sounds import (
    ANDROID_MIXER_BUFFER,
    SAMPLE_RATE,
    WEB_MIXER_BUFFER,
    SoundManager,
    mixer_params,
    pre_init,
)

ANDROID_PARAMS = {"frequency": SAMPLE_RATE, "size": -16, "channels": 1, "buffer": ANDROID_MIXER_BUFFER}
WEB_PARAMS = {"frequency": SAMPLE_RATE, "size": -16, "channels": 1, "buffer": WEB_MIXER_BUFFER}
DESKTOP_PARAMS = {"frequency": SAMPLE_RATE, "size": -16, "channels": 1}


def test_mixer_params_use_a_larger_buffer_on_android(monkeypatch):
    """Buffer pequeno demais no Android estoura/crepita (R8.4, R14.6, design secao 11)."""
    monkeypatch.setattr("src.sounds.is_android", lambda: True)
    monkeypatch.setattr("src.sounds.is_web", lambda: False)
    assert mixer_params() == ANDROID_PARAMS


def test_mixer_params_use_a_larger_buffer_on_web(monkeypatch):
    """Placeholder a calibrar (R37.6, design secao 47) — mesma logica do Android."""
    monkeypatch.setattr("src.sounds.is_android", lambda: False)
    monkeypatch.setattr("src.sounds.is_web", lambda: True)
    assert mixer_params() == WEB_PARAMS


def test_mixer_params_use_the_default_buffer_off_android_and_web(monkeypatch):
    monkeypatch.setattr("src.sounds.is_android", lambda: False)
    monkeypatch.setattr("src.sounds.is_web", lambda: False)
    assert mixer_params() == DESKTOP_PARAMS


# --- inicializacao unica do mixer (task 61, R27.6) ---------------------------------


def _spy(monkeypatch, name) -> list[dict]:
    """Registra os kwargs de cada chamada a `pygame.mixer.<name>`, sem executa-la."""
    calls: list[dict] = []
    monkeypatch.setattr(pygame.mixer, name, lambda **kwargs: calls.append(kwargs))
    return calls


def test_pre_init_carries_the_same_parameters_the_mixer_would_be_initialized_with(monkeypatch):
    """`pre_init` so guarda o que o `init` seguinte vai usar — se ela guardasse outra
    coisa, o mixer nasceria com os parametros errados e ninguem reclamaria."""
    monkeypatch.setattr("src.sounds.is_android", lambda: True)
    calls = _spy(monkeypatch, "pre_init")

    pre_init()

    assert calls == [ANDROID_PARAMS]


def test_a_mixer_already_up_is_not_initialized_a_second_time(monkeypatch):
    """O ponto da task: a v2 abria o dispositivo de audio duas vezes na abertura —
    uma pelo `pygame.init()`, com os parametros padrao, e outra aqui. Com `pre_init`
    ele ja nasce certo, e a segunda abertura deixa de existir."""
    calls = _spy(monkeypatch, "init")
    monkeypatch.setattr(pygame.mixer, "get_init", lambda: (SAMPLE_RATE, -16, 1))

    manager = SoundManager()

    assert calls == []
    assert manager.audio_ok is True


def test_a_mixer_that_is_not_up_is_initialized_with_the_right_parameters(monkeypatch):
    """Fora do jogo (um teste, um script) ninguem chamou `pre_init`, e o `SoundManager`
    continua sabendo subir o mixer sozinho — com os mesmos parametros."""
    monkeypatch.setattr("src.sounds.is_android", lambda: False)
    calls = _spy(monkeypatch, "init")
    monkeypatch.setattr(pygame.mixer, "get_init", lambda: None)

    SoundManager()

    assert calls == [DESKTOP_PARAMS]


def test_audio_that_cannot_be_opened_leaves_the_game_playable(monkeypatch):
    """Degradacao graciosa desde a v1: sem dispositivo de audio o jogo segue mudo, e
    `play` nao levanta nada (R8.4)."""

    def fail(**kwargs):
        raise pygame.error("sem dispositivo de audio (simulado)")

    monkeypatch.setattr(pygame.mixer, "get_init", lambda: None)
    monkeypatch.setattr(pygame.mixer, "init", fail)

    manager = SoundManager()

    assert manager.audio_ok is False
    manager.play("flap")


def test_the_game_pre_initializes_the_mixer_before_pygame_init(monkeypatch):
    """A ordem e tudo: `pre_init` depois do `pygame.init()` nao teria efeito nenhum
    sobre o mixer que ja subiu."""
    order: list[str] = []
    monkeypatch.setattr(sounds, "pre_init", lambda: order.append("pre_init"))
    real_init = pygame.init
    monkeypatch.setattr(pygame, "init", lambda: (order.append("init"), real_init())[1])

    from src.game import Game

    Game()

    assert order[:2] == ["pre_init", "init"]
