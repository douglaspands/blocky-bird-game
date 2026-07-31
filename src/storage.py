"""Resolve o diretorio gravavel do highscore por plataforma (R4.5).

No Android o diretorio de trabalho nao e gravavel; a v1 gravava highscore.json
via caminho relativo (resolvido contra o cwd), o que falharia silenciosamente
la (a escrita ja engole OSError). Este modulo resolve um diretorio correto por
plataforma para score.py usar como default.
"""

import os
import sys
from pathlib import Path


def is_android() -> bool:
    """ANDROID_ARGUMENT e definido pelo python-for-android em tempo de execucao."""
    return "ANDROID_ARGUMENT" in os.environ


def is_frozen() -> bool:
    """PyInstaller define sys.frozen no executavel empacotado (BlockyBee.spec).

    No modo onefile, __file__ aponta para o diretorio temporario de extracao
    (sys._MEIPASS), apagado ao fechar o app — usar esse caminho como base faz
    o highscore.json nunca sobreviver entre execucoes do .exe/binario.
    """
    return getattr(sys, "frozen", False)


def save_dir() -> Path:
    if is_android():
        try:
            # fornecido pelo p4a em runtime; indisponivel no venv de dev
            from android.storage import app_storage_path  # ty: ignore[unresolved-import]

            return Path(app_storage_path())
        except ImportError:
            return Path(os.environ.get("ANDROID_PRIVATE", "."))
    if is_frozen():
        return Path(sys.executable).resolve().parent  # pasta do .exe/binario empacotado
    return Path(__file__).resolve().parent.parent  # raiz do projeto, rodando de fonte
