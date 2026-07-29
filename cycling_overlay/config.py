"""CLI argument parsing, runtime configuration, and overlay layout definitions."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .settings import load_settings

DEFAULT_FOCUS_FILE = Path.home() / "Documents" / "TPVirtual" / "Broadcast" / "focus.json"
DEFAULT_OPACITY = 0.7


@dataclass(frozen=True)
class OverlayConfig:
    focus_file: Path = DEFAULT_FOCUS_FILE
    min_cadence: int | None = None
    min_power: int | None = None
    imperial: bool = False
    hide_units: bool = False
    opacity: float = DEFAULT_OPACITY
    window_x: int | None = None
    window_y: int | None = None


def parse_args(argv: list[str] | None = None) -> OverlayConfig:
    """Build the runtime config from persisted settings, overridden by any CLI flags given.

    Precedence: explicit CLI flag > value saved from a previous run (settings.json,
    written by the in-app Settings dialog / window drag) > built-in default. The
    packaged .exe is normally launched with no arguments at all, so it relies
    entirely on the saved settings; CLI flags exist for developers running from
    source.
    """
    parser = argparse.ArgumentParser(description="Cycling Stats Overlay")
    parser.add_argument(
        "--focus-file",
        type=Path,
        default=None,
        help=f"Path to TPVirtual's focus.json (default: {DEFAULT_FOCUS_FILE})",
    )
    parser.add_argument("--min-cadence", type=int, default=None,
                         help="Minimum cadence threshold (shows red if below)")
    parser.add_argument("--min-power", type=int, default=None,
                         help="Minimum power threshold (shows red if below)")
    parser.add_argument(
        "--imperial",
        action="store_true",
        help="Use imperial units (mph, miles) instead of metric (km/h, km)",
    )
    parser.add_argument("--hide-units", action="store_true", help="Hide unit labels from display values")
    parser.add_argument(
        "--opacity",
        type=float,
        default=None,
        help=f"Window opacity from 0.1 (near-invisible) to 1.0 (opaque) (default: {DEFAULT_OPACITY})",
    )
    args = parser.parse_args(argv)
    saved = load_settings()

    return OverlayConfig(
        focus_file=args.focus_file or DEFAULT_FOCUS_FILE,
        min_cadence=args.min_cadence if args.min_cadence is not None else saved.get("min_cadence"),
        min_power=args.min_power if args.min_power is not None else saved.get("min_power"),
        imperial=args.imperial or bool(saved.get("imperial", False)),
        hide_units=args.hide_units or bool(saved.get("hide_units", False)),
        opacity=args.opacity if args.opacity is not None else saved.get("opacity", DEFAULT_OPACITY),
        window_x=saved.get("window_x"),
        window_y=saved.get("window_y"),
    )


# Layout of the metric cards grid: each row holds a list of metric definitions.
# "color" is the card's accent (value text, top edge, and border tint); "icon" is purely decorative.
LAYOUT: list[dict[str, Any]] = [
    {
        "row": 0,
        "metrics": [
            {"type": "power", "title": "POWER", "default_value": "-- W", "color": "#ffb020", "icon": "⚡",
             "show_average": True, "avg_label": "NP"},
            {"type": "heartrate", "title": "HEART RATE", "default_value": "-- BPM", "color": "#ff4d6d",
             "icon": "♥", "show_average": True},
        ],
    },
    {
        "row": 1,
        "metrics": [
            {"type": "cadence", "title": "CADENCE", "default_value": "-- RPM", "color": "#2ee6a8",
             "icon": "\U0001f504", "show_average": True},
            {"type": "speed", "title": "SPEED", "default_value": "-- KM/H", "color": "#4cc9f0",
             "icon": "\U0001f4a8", "show_average": True},
        ],
    },
    {
        "row": 2,
        "metrics": [
            {"type": "time", "title": "TIME", "default_value": "--:--", "color": "#c9c9d9",
             "icon": "⏱", "show_average": False},
            {"type": "distance", "title": "DISTANCE", "default_value": "-- KM", "color": "#7c9eff",
             "icon": "\U0001f4cd", "show_average": False},
        ],
    },
    {
        "row": 3,
        "metrics": [
            {"type": "tss", "title": "TSS", "default_value": "-- TSS", "color": "#c77dff",
             "icon": "\U0001f4ca", "show_average": False},
            {"type": "calories", "title": "CALORIES", "default_value": "-- CAL", "color": "#ffd166",
             "icon": "\U0001f525", "show_average": False},
        ],
    },
    {
        "row": 4,
        "metrics": [
            {"type": "slope", "title": "SLOPE", "default_value": "-- %", "color": "#ff6b35",
             "icon": "⛰", "show_average": False},
            {"type": "draft", "title": "DRAFT", "default_value": "-- %", "color": "#3a86ff",
             "icon": "\U0001f6b4", "show_average": False},
        ],
    },
]

UNITS: dict[str, str] = {
    "power": "W",
    "heartrate": "BPM",
    "cadence": "RPM",
    "time": "",
    "tss": "TSS",
    "calories": "CAL",
    "slope": "%",
    "draft": "%",
}
