"""Entry point: `python -m cycling_overlay [options]`."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from .config import parse_args
from .paths import app_data_dir
from .ui import CyclingOverlay

LOG_FILE = app_data_dir() / "cycling_overlay.log"


def _set_dpi_awareness() -> None:
    """Opt the process into per-monitor DPI awareness.

    Must run before the Tk root window is created. Without this, Windows
    bitmap-stretches the (DPI-unaware) window to the right physical size on
    scaled displays, which is what makes text and shapes look blurry on any
    monitor running above 100% scaling.
    """
    if sys.platform != "win32":
        return

    import ctypes

    try:
        # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 (Windows 10 1703+).
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        return
    except (AttributeError, OSError):
        pass

    try:
        # PROCESS_PER_MONITOR_DPI_AWARE (Windows 8.1+).
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except (AttributeError, OSError):
        pass

    try:
        # System DPI aware (Vista+); better than nothing on very old Windows.
        ctypes.windll.user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        logging.getLogger(__name__).warning("Could not set process DPI awareness")


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

    _set_dpi_awareness()

    config = parse_args()
    logger.info(
        "Config: focus_file=%s min_cadence=%s min_power=%s imperial=%s",
        config.focus_file, config.min_cadence, config.min_power, config.imperial,
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
