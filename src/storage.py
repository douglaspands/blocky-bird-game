"""Resolve o diretorio gravavel do highscore por plataforma (R4.5).

No Android o diretorio de trabalho nao e gravavel; a v1 gravava highscore.json
via caminho relativo (resolvido contra o cwd), o que falharia silenciosamente
la (a escrita ja engole OSError). Este modulo resolve um diretorio correto por
plataforma para score.py usar como default.
"""

import json
import os
import sys
from pathlib import Path


def is_android() -> bool:
    """ANDROID_ARGUMENT e definido pelo python-for-android em tempo de execucao."""
    return "ANDROID_ARGUMENT" in os.environ


def is_web() -> bool:
    """sys.platform == "emscripten" e o runtime WebAssembly do pygbag (R39.1)."""
    return sys.platform == "emscripten"


def _web_storage():
    """`window.localStorage` do navegador, seam isolado para teste (R39.5).

    `platform.window` e como o proprio `pygbag` expõe o `window` do JavaScript
    (confirmado em `pygbag/support/pyodide.py` do pacote instalado: `sys.modules["js"]
    = platform.window.globalThis`). Import lazy porque o modulo `platform` do pygbag
    substitui o `platform` da stdlib e so existe de fato sob Emscripten.
    """
    import platform

    return platform.window.localStorage  # ty: ignore[unresolved-attribute] injetado pelo pygbag em runtime


def read_json(filename: str) -> dict | None:
    """Le um JSON por nome: `localStorage` na web, arquivo em `save_dir()` fora dela.

    `None` quando o dado nao existe ou a leitura falha (arquivo ausente/sem permissao —
    R39.3); um JSON corrompido propaga `json.JSONDecodeError`, deixado para quem chama
    validar o formato esperado (R39.2, R39.5).
    """
    if is_web():
        raw = _web_storage().getItem(filename)
        return json.loads(raw) if raw is not None else None
    try:
        with open(save_dir() / filename, encoding="utf-8") as f:
            return json.load(f)
    except OSError:
        return None


def write_json(filename: str, data: dict) -> None:
    """Grava um JSON por nome: `localStorage` na web, arquivo em `save_dir()` fora dela.

    Falha de escrita em arquivo e ignorada em silencio, como ja era antes desta funcao
    existir (R39.2).
    """
    if is_web():
        _web_storage().setItem(filename, json.dumps(data))
        return
    try:
        with open(save_dir() / filename, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except OSError:
        pass


def is_frozen() -> bool:
    """PyInstaller define sys.frozen no executavel empacotado (BlockyBee.spec).

    No modo onefile, __file__ aponta para o diretorio temporario de extracao
    (sys._MEIPASS), apagado ao fechar o app — usar esse caminho como base faz
    o highscore.json nunca sobreviver entre execucoes do .exe/binario.
    """
    return getattr(sys, "frozen", False)


def save_dir() -> Path:
    """Diretorio gravavel para dados persistentes (recorde, qualidade), por plataforma."""
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
