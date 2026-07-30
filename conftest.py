import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest


@pytest.fixture(scope="session", autouse=True)
def _pygame_session():
    pygame.init()
    yield
    pygame.quit()


@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    """Evita que testes leiam/gravem highscore.json na raiz real do projeto."""
    monkeypatch.chdir(tmp_path)


@pytest.fixture(autouse=True)
def _reset_display():
    """pygame.SCALED exige um renderer SDL, e o driver dummy so permite um por
    processo — sem isso, o 2o+ set_mode(SCALED) do processo falha com
    'failed to create renderer' (varios testes criam Game() cada um)."""
    pygame.display.quit()
    pygame.display.init()
