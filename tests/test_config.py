import json

import cycling_overlay.settings as settings_module
from cycling_overlay.config import DEFAULT_FOCUS_FILE, DEFAULT_OPACITY, DEFAULT_WINDOW_DURATION, parse_args


def test_defaults_with_no_saved_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_module, "SETTINGS_FILE", tmp_path / "settings.json")

    cfg = parse_args([])

    assert cfg.focus_file == DEFAULT_FOCUS_FILE
    assert cfg.min_cadence is None
    assert cfg.min_power is None
    assert cfg.imperial is False
    assert cfg.hide_units is False
    assert cfg.window_duration == DEFAULT_WINDOW_DURATION
    assert cfg.opacity == DEFAULT_OPACITY
    assert cfg.window_x is None
    assert cfg.window_y is None


def test_cli_flags_override_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_module, "SETTINGS_FILE", tmp_path / "settings.json")

    cfg = parse_args(["--min-cadence", "70", "--min-power", "150", "--imperial", "--hide-units"])

    assert cfg.min_cadence == 70
    assert cfg.min_power == 150
    assert cfg.imperial is True
    assert cfg.hide_units is True


def test_saved_settings_used_when_no_cli_override(tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(
        json.dumps({"min_cadence": 65, "imperial": True, "window_duration": 120, "opacity": 0.5}),
        encoding="utf-8",
    )
    monkeypatch.setattr(settings_module, "SETTINGS_FILE", settings_file)

    cfg = parse_args([])

    assert cfg.min_cadence == 65
    assert cfg.imperial is True
    assert cfg.window_duration == 120
    assert cfg.opacity == 0.5


def test_cli_flag_takes_precedence_over_saved_settings(tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(json.dumps({"min_power": 100, "window_duration": 200}), encoding="utf-8")
    monkeypatch.setattr(settings_module, "SETTINGS_FILE", settings_file)

    cfg = parse_args(["--min-power", "250"])

    assert cfg.min_power == 250  # CLI wins
    assert cfg.window_duration == 200  # untouched saved value still applies


def test_saved_window_position_is_loaded(tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(json.dumps({"window_x": 321, "window_y": 654}), encoding="utf-8")
    monkeypatch.setattr(settings_module, "SETTINGS_FILE", settings_file)

    cfg = parse_args([])

    assert cfg.window_x == 321
    assert cfg.window_y == 654
