import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest


@pytest.fixture(scope="session", autouse=True)
def _pygame_session():
    pygame.init()
    yield
    pygame.quit()


@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    """Evita que testes leiam/gravem highscore.json na raiz real do projeto.

    storage.save_dir() no desktop resolve para a raiz do projeto via __file__
    (nao mais o cwd), entao so o chdir nao basta desde a v2 — monkeypatcha
    save_dir() direto para o tmp_path do teste."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("src.storage.save_dir", lambda: tmp_path)


@pytest.fixture(autouse=True)
def _reset_viewport():
    """Game define o viewport ativo globalmente ao criar o display (960x720 no
    desktop). Sem este reset, o canvas de um teste vazaria para o proximo — os
    testes de unidade assumem o canvas 2:3, identico a area jogavel."""
    from src import config, viewport

    config.set_viewport(viewport.compute(viewport.PLAY_W, viewport.PLAY_H))


@pytest.fixture(autouse=True)
def _reset_display():
    """pygame.SCALED exige um renderer SDL, e o driver dummy so permite um por
    processo — sem isso, o 2o+ set_mode(SCALED) do processo falha com
    'failed to create renderer' (varios testes criam Game() cada um; ver
    design.md secao 20.2)."""
    pygame.display.quit()
    pygame.display.init()
