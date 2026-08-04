"""Persistencia do recorde em highscore.json (R4.3, R4.4, R4.5)."""

import json
from pathlib import Path

from src import storage


def _default_path() -> Path:
    """Resolve o caminho padrao do arquivo de recorde.

    Resolvido a cada chamada (nao como default de parametro) para que
    storage.save_dir() possa ser monkeypatched em testes e reagir a mudanca
    de plataforma em runtime, em vez de ficar congelado no import (R4.5).
    """
    return storage.save_dir() / "highscore.json"


def load_highscore(path: Path | None = None) -> int:
    """Le o recorde salvo, ou 0 se o arquivo faltar ou estiver corrompido."""
    path = path if path is not None else _default_path()
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return int(data["highscore"])
    except (OSError, ValueError, KeyError, TypeError):
        return 0


def save_highscore(highscore: int, path: Path | None = None) -> None:
    """Grava o recorde em disco, ignorando falha de escrita em silencio."""
    path = path if path is not None else _default_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"highscore": highscore}, f)
    except OSError:
        pass
