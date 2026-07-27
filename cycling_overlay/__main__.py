"""Entry point: `python -m cycling_overlay [options]`."""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import parse_args
from .ui import CyclingOverlay


def _log_dir() -> Path:
    """A stable, user-writable directory for log output.

    Deliberately independent of `__file__`/`sys.executable` location: under a
    PyInstaller onefile build the app runs from a temp extraction directory,
    and the install directory itself may not be writable.
    """
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    else:
        base = Path.home() / ".local" / "share"
    return base / "CyclingOverlay"


LOG_FILE = _log_dir() / "cycling_overlay.log"


def setup_logging() -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    # watchdog's inotify buffer is extremely chatty at DEBUG/INFO
    logging.getLogger("watchdog.observers.inotify_buffer").setLevel(logging.WARNING)


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting cycling overlay")

    config = parse_args()
    logger.info(
        "Config: focus_file=%s min_cadence=%s min_power=%s imperial=%s window_duration=%s",
        config.focus_file, config.min_cadence, config.min_power, config.imperial, config.window_duration,
    )

    try:
        overlay = CyclingOverlay(config)
        overlay.run()
    except Exception:
        logger.exception("Fatal error")
        raise
    finally:
        logger.info("Application terminated")


if __name__ == "__main__":
    main()
