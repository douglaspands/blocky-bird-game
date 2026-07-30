"""Resolve o diretorio gravavel do highscore por plataforma (R4.5).

No Android o diretorio de trabalho nao e gravavel; a v1 gravava highscore.json
via caminho relativo (resolvido contra o cwd), o que falharia silenciosamente
la (a escrita ja engole OSError). Este modulo resolve um diretorio correto por
plataforma para score.py usar como default.
"""

import os
from pathlib import Path


def is_android() -> bool:
    """ANDROID_ARGUMENT e definido pelo python-for-android em tempo de execucao."""
    return "ANDROID_ARGUMENT" in os.environ


def save_dir() -> Path:
    if is_android():
        try:
            from android.storage import app_storage_path  # fornecido pelo p4a

            return Path(app_storage_path())
        except ImportError:
            return Path(os.environ.get("ANDROID_PRIVATE", "."))
    return Path(__file__).resolve().parent.parent  # raiz do projeto, no desktop
