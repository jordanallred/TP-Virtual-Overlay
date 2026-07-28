"""Shared, frozen-safe location for this app's user data (logs, settings).

Deliberately independent of `__file__`/`sys.executable`: under a PyInstaller
onefile build the app runs from a temp extraction directory, and the install
directory itself may not be writable.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def app_data_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    else:
        base = Path.home() / ".local" / "share"
    return base / "CyclingOverlay"
