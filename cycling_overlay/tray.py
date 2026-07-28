"""System tray icon.

The overlay window is borderless and always-on-top with no taskbar entry, so
if it's ever dragged off-screen, hidden behind something, or a monitor gets
unplugged, there'd otherwise be no way to get it back short of killing the
process. The tray icon exists as recovery: Show/Hide, Reset Position, and Quit.

pystray runs its own message loop on a background thread; its callbacks fire
on that thread; callers are responsible for marshaling back onto the Tk main
thread (e.g. via `root.after(0, ...)`) before touching any Tk widget.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from pathlib import Path

import pystray
from PIL import Image

logger = logging.getLogger(__name__)

TrayCallback = Callable[[pystray.Icon, pystray.MenuItem], None]


class TrayIcon:
    def __init__(
        self,
        icon_path: Path,
        on_show_hide: TrayCallback,
        on_reset_position: TrayCallback,
        on_quit: TrayCallback,
    ) -> None:
        image = Image.open(icon_path)
        menu = pystray.Menu(
            pystray.MenuItem("Show/Hide", on_show_hide, default=True),
            pystray.MenuItem("Reset Position", on_reset_position),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", on_quit),
        )
        self._icon = pystray.Icon("TPVirtualOverlay", image, "TP Virtual Overlay", menu)
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True, name="tray-icon")
        self._thread.start()

    def _run(self) -> None:
        try:
            self._icon.run()
        except Exception:
            logger.exception("Tray icon thread crashed")

    def stop(self) -> None:
        try:
            self._icon.stop()
        except Exception:
            logger.exception("Error stopping tray icon")
