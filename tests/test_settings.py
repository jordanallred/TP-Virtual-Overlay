import json

import cycling_overlay.settings as settings_module
from cycling_overlay.settings import load_settings, save_settings


def test_missing_file_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_module, "SETTINGS_FILE", tmp_path / "nope.json")
    assert load_settings() == {}


def test_corrupted_json_returns_empty(tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text("{not valid json", encoding="utf-8")
    monkeypatch.setattr(settings_module, "SETTINGS_FILE", settings_file)
    assert load_settings() == {}


def test_non_dict_json_returns_empty(tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text("[1, 2, 3]", encoding="utf-8")
    monkeypatch.setattr(settings_module, "SETTINGS_FILE", settings_file)
    assert load_settings() == {}


def test_unknown_keys_are_dropped(tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(json.dumps({"min_power": 5, "totally_unknown": "x"}), encoding="utf-8")
    monkeypatch.setattr(settings_module, "SETTINGS_FILE", settings_file)
    assert load_settings() == {"min_power": 5}


def test_save_then_load_round_trips(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_module, "SETTINGS_FILE", tmp_path / "settings.json")

    save_settings({"min_power": 200, "imperial": True})
    assert load_settings() == {"min_power": 200, "imperial": True}


def test_save_merges_rather_than_replaces(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_module, "SETTINGS_FILE", tmp_path / "settings.json")

    save_settings({"min_power": 200, "imperial": True})
    save_settings({"opacity": 0.4})

    assert load_settings() == {"min_power": 200, "imperial": True, "opacity": 0.4}


def test_save_creates_parent_directory(tmp_path, monkeypatch):
    settings_file = tmp_path / "nested" / "dir" / "settings.json"
    monkeypatch.setattr(settings_module, "SETTINGS_FILE", settings_file)

    save_settings({"opacity": 0.5})
    assert settings_file.exists()
    assert load_settings() == {"opacity": 0.5}
