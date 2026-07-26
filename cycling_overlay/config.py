"""CLI argument parsing, runtime configuration, and overlay layout definitions."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_FOCUS_FILE = Path.home() / "Documents" / "TPVirtual" / "Broadcast" / "focus.json"
DEFAULT_WINDOW_DURATION = 300  # seconds of history kept for the graphs


@dataclass(frozen=True)
class OverlayConfig:
    focus_file: Path = DEFAULT_FOCUS_FILE
    min_cadence: int | None = None
    min_power: int | None = None
    imperial: bool = False
    hide_units: bool = False
    window_duration: int = DEFAULT_WINDOW_DURATION


def parse_args(argv: list[str] | None = None) -> OverlayConfig:
    parser = argparse.ArgumentParser(description="Cycling Stats Overlay")
    parser.add_argument(
        "--focus-file",
        type=Path,
        default=DEFAULT_FOCUS_FILE,
        help=f"Path to TPVirtual's focus.json (default: {DEFAULT_FOCUS_FILE})",
    )
    parser.add_argument("--min-cadence", type=int, help="Minimum cadence threshold (shows red if below)")
    parser.add_argument("--min-power", type=int, help="Minimum power threshold (shows red if below)")
    parser.add_argument(
        "--imperial",
        action="store_true",
        help="Use imperial units (mph, miles) instead of metric (km/h, km)",
    )
    parser.add_argument("--hide-units", action="store_true", help="Hide unit labels from display values")
    parser.add_argument(
        "--window-duration",
        type=int,
        default=DEFAULT_WINDOW_DURATION,
        help=f"Sliding window duration in seconds for the graphs (default: {DEFAULT_WINDOW_DURATION})",
    )
    args = parser.parse_args(argv)

    return OverlayConfig(
        focus_file=args.focus_file,
        min_cadence=args.min_cadence,
        min_power=args.min_power,
        imperial=args.imperial,
        hide_units=args.hide_units,
        window_duration=args.window_duration,
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
]

UNITS: dict[str, str] = {
    "power": "W",
    "heartrate": "BPM",
    "cadence": "RPM",
    "time": "",
    "tss": "TSS",
    "calories": "CAL",
}
