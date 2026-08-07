import json
import sys
import types
from pathlib import Path

from src import storage
from tests.fakes import FakeLocalStorage


def test_is_android_false_without_env_var(monkeypatch):
    monkeypatch.delenv("ANDROID_ARGUMENT", raising=False)
    assert storage.is_android() is False


def test_is_android_true_with_env_var(monkeypatch):
    monkeypatch.setenv("ANDROID_ARGUMENT", "qualquer-coisa")
    assert storage.is_android() is True


def test_is_web_false_off_emscripten(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux", raising=False)
    assert storage.is_web() is False


def test_is_web_true_under_emscripten(monkeypatch):
    monkeypatch.setattr(sys, "platform", "emscripten", raising=False)
    assert storage.is_web() is True


def test_save_dir_desktop_is_project_root(monkeypatch):
    # o conftest.py isola storage.save_dir() para nao gravar na raiz real do
    # projeto durante os testes; aqui queremos testar a implementacao de
    # verdade, entao desfazemos essa protecao so para este teste.
    monkeypatch.undo()
    monkeypatch.delenv("ANDROID_ARGUMENT", raising=False)

    root = storage.save_dir()
    assert (root / "pyproject.toml").is_file()


def test_save_dir_frozen_desktop_uses_executable_dir(monkeypatch, tmp_path):
    """Executavel empacotado pelo PyInstaller (BlockyBee.spec): __file__ aponta
    para o _MEIPASS temporario, entao o diretorio correto vem de sys.executable."""
    monkeypatch.undo()
    monkeypatch.delenv("ANDROID_ARGUMENT", raising=False)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    fake_exe = tmp_path / "BlockyBee.exe"
    monkeypatch.setattr(sys, "executable", str(fake_exe))

    assert storage.save_dir() == tmp_path


def test_save_dir_android_uses_app_storage_path(monkeypatch):
    """Simula o modulo `android.storage` que o p4a injeta em tempo de execucao."""
    monkeypatch.undo()
    monkeypatch.setenv("ANDROID_ARGUMENT", "1")

    fake_android = types.ModuleType("android")
    fake_storage = types.ModuleType("android.storage")
    fake_storage.app_storage_path = lambda: "/data/data/org.blockybee/files"  # ty: ignore[unresolved-attribute]
    fake_android.storage = fake_storage  # ty: ignore[unresolved-attribute] ModuleType aceita atributo dinamico em runtime
    monkeypatch.setitem(sys.modules, "android", fake_android)
    monkeypatch.setitem(sys.modules, "android.storage", fake_storage)

    assert storage.save_dir() == Path("/data/data/org.blockybee/files")


def test_save_dir_android_falls_back_when_module_missing(monkeypatch):
    """Sem o modulo android (ex.: testando fora do p4a), cai no fallback de env var."""
    monkeypatch.undo()
    monkeypatch.setenv("ANDROID_ARGUMENT", "1")
    monkeypatch.setenv("ANDROID_PRIVATE", "/data/data/org.blockybee/files_fallback")
    monkeypatch.delitem(sys.modules, "android", raising=False)
    monkeypatch.delitem(sys.modules, "android.storage", raising=False)

    assert storage.save_dir() == Path("/data/data/org.blockybee/files_fallback")


def test_save_dir_android_fallback_defaults_to_dot(monkeypatch):
    monkeypatch.undo()
    monkeypatch.setenv("ANDROID_ARGUMENT", "1")
    monkeypatch.delenv("ANDROID_PRIVATE", raising=False)
    monkeypatch.delitem(sys.modules, "android", raising=False)
    monkeypatch.delitem(sys.modules, "android.storage", raising=False)

    assert storage.save_dir() == Path(".")


# --- read_json / write_json: arquivo (R39.2, R39.3) --------------------------------


def test_read_json_missing_file_returns_none():
    assert storage.read_json("nao-existe.json") is None


def test_write_json_and_read_json_roundtrip_on_file():
    storage.write_json("dados.json", {"a": 1})

    assert storage.read_json("dados.json") == {"a": 1}


def test_write_json_ignores_write_errors(tmp_path, monkeypatch):
    """Diretorio inexistente: engolido em silencio, como ja era no recorde."""
    monkeypatch.setattr(storage, "save_dir", lambda: tmp_path / "sem" / "essa" / "pasta")

    storage.write_json("dados.json", {"a": 1})  # nao deve lancar


# --- read_json / write_json: localStorage (R39.2, R39.5) ---------------------------


def test_read_json_missing_key_in_web_storage_returns_none(monkeypatch):
    monkeypatch.setattr(storage, "is_web", lambda: True)
    monkeypatch.setattr(storage, "_web_storage", lambda: FakeLocalStorage())

    assert storage.read_json("dados.json") is None


def test_write_json_and_read_json_roundtrip_on_web_storage(monkeypatch):
    fake = FakeLocalStorage()
    monkeypatch.setattr(storage, "is_web", lambda: True)
    monkeypatch.setattr(storage, "_web_storage", lambda: fake)

    storage.write_json("dados.json", {"a": 1})

    assert fake.getItem("dados.json") == json.dumps({"a": 1})
    assert storage.read_json("dados.json") == {"a": 1}
