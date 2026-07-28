"""Persisted user settings (window position, units, thresholds, opacity).

Stored as JSON so the packaged .exe — which has no command line a normal user
would ever type into — remembers whatever was last configured through the
in-app Settings dialog or dragged into place.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from .paths import app_data_dir

logger = logging.getLogger(__name__)

SETTINGS_FILE = app_data_dir() / "settings.json"

# Only these keys are ever read from or written to the file; anything else
# present is ignored rather than propagated, so a corrupted/foreign file can't
# inject unexpected config.
VALID_KEYS = (
    "min_cadence", "min_power", "imperial", "hide_units",
    "window_duration", "opacity", "window_x", "window_y",
)


def load_settings() -> dict[str, Any]:
    if not SETTINGS_FILE.exists():
        return {}

    try:
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        logger.warning("Could not read settings file, ignoring: %s", SETTINGS_FILE)
        return {}

    if not isinstance(data, dict):
        return {}

    return {key: data[key] for key in VALID_KEYS if key in data}


def save_settings(values: dict[str, Any]) -> None:
    """Merge `values` into the persisted settings and write them back out."""
    current = load_settings()
    current.update({key: value for key, value in values.items() if key in VALID_KEYS})

    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2)
    except OSError:
        logger.warning("Could not write settings file: %s", SETTINGS_FILE)
