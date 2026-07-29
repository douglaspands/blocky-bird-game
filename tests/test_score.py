from src.score import load_highscore, save_highscore


def test_missing_file_falls_back_to_zero(tmp_path):
    path = tmp_path / "highscore.json"
    assert load_highscore(path) == 0


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "highscore.json"
    save_highscore(42, path)
    assert load_highscore(path) == 42


def test_corrupted_json_falls_back_to_zero(tmp_path):
    path = tmp_path / "highscore.json"
    path.write_text("{not valid json", encoding="utf-8")
    assert load_highscore(path) == 0


def test_missing_key_falls_back_to_zero(tmp_path):
    path = tmp_path / "highscore.json"
    path.write_text('{"outra_chave": 1}', encoding="utf-8")
    assert load_highscore(path) == 0


def test_wrong_type_falls_back_to_zero(tmp_path):
    path = tmp_path / "highscore.json"
    path.write_text('{"highscore": "nao-e-numero"}', encoding="utf-8")
    assert load_highscore(path) == 0


def test_save_overwrites_previous_value(tmp_path):
    path = tmp_path / "highscore.json"
    save_highscore(5, path)
    save_highscore(10, path)
    assert load_highscore(path) == 10
