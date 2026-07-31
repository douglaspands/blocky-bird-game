import sys
from pathlib import Path

from src import assets


def test_asset_path_source_run_resolves_project_root(monkeypatch):
    monkeypatch.setattr("src.storage.is_frozen", lambda: False)

    path = assets.asset_path("app_icon_512.png")

    assert path == Path(__file__).resolve().parent.parent / "assets" / "app_icon_512.png"


def test_asset_path_frozen_resolves_meipass(monkeypatch, tmp_path):
    monkeypatch.setattr("src.storage.is_frozen", lambda: True)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

    path = assets.asset_path("app_icon_512.png")

    assert path == tmp_path / "assets" / "app_icon_512.png"
