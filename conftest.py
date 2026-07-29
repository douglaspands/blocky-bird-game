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
