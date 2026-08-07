from src import storage
from src.score import FILENAME, load_highscore, save_highscore
from tests.fakes import FakeLocalStorage


def test_missing_file_falls_back_to_zero():
    assert load_highscore() == 0


def test_save_and_load_roundtrip():
    save_highscore(42)
    assert load_highscore() == 42


def test_corrupted_json_falls_back_to_zero(tmp_path):
    (tmp_path / FILENAME).write_text("{not valid json", encoding="utf-8")
    assert load_highscore() == 0


def test_missing_key_falls_back_to_zero(tmp_path):
    (tmp_path / FILENAME).write_text('{"outra_chave": 1}', encoding="utf-8")
    assert load_highscore() == 0


def test_wrong_type_falls_back_to_zero(tmp_path):
    (tmp_path / FILENAME).write_text('{"highscore": "nao-e-numero"}', encoding="utf-8")
    assert load_highscore() == 0


def test_save_overwrites_previous_value():
    save_highscore(5)
    save_highscore(10)
    assert load_highscore() == 10


def test_roundtrip_uses_web_storage_when_is_web(monkeypatch):
    """R39.2, R39.5: mesma API publica, sem navegador real."""
    fake = FakeLocalStorage()
    monkeypatch.setattr(storage, "is_web", lambda: True)
    monkeypatch.setattr(storage, "_web_storage", lambda: fake)

    save_highscore(7)

    assert load_highscore() == 7
