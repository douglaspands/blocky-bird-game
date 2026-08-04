"""Resolve o caminho de um asset bundlado, somente-leitura (R21.2).

Diferente de storage.save_dir() (que resolve onde GRAVAR e evita sys._MEIPASS
de proposito, ja que esse diretorio e apagado ao fechar o processo), aqui o
caso e o oposto: o PyInstaller onefile EXTRAI os dados empacotados (via
`datas=` no .spec) para sys._MEIPASS a cada execucao — e exatamente onde um
asset builtin deve ser lido no executavel empacotado.
"""

import sys
from pathlib import Path

from src import storage


def asset_path(filename: str) -> Path:
    """Resolve o caminho absoluto de um asset em `assets/filename`."""
    if storage.is_frozen():
        base = Path(getattr(sys, "_MEIPASS", "."))
    else:
        base = Path(__file__).resolve().parent.parent  # raiz do projeto (fonte ou apk do p4a)
    return base / "assets" / filename
