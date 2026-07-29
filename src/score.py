"""Persistencia do recorde em highscore.json (R4.3, R4.4)."""

import json
from pathlib import Path

HIGHSCORE_PATH = Path("highscore.json")


def load_highscore(path: Path = HIGHSCORE_PATH) -> int:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return int(data["highscore"])
    except (OSError, ValueError, KeyError, TypeError):
        return 0


def save_highscore(highscore: int, path: Path = HIGHSCORE_PATH) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"highscore": highscore}, f)
    except OSError:
        pass
