"""Persistencia do recorde em highscore.json (R4.3, R4.4, R4.5, R39.2-R39.5)."""

from src import storage

FILENAME = "highscore.json"


def load_highscore() -> int:
    """Le o recorde salvo, ou 0 se o dado faltar ou estiver corrompido."""
    try:
        data = storage.read_json(FILENAME)
        return int(data["highscore"]) if data is not None else 0
    except (ValueError, KeyError, TypeError):
        return 0


def save_highscore(highscore: int) -> None:
    """Grava o recorde. Falha de escrita e ignorada em silencio (tratada em storage)."""
    storage.write_json(FILENAME, {"highscore": highscore})
