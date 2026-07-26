"""Debounced filesystem watcher that triggers a callback when focus.json changes."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


class _DebouncedFileHandler(FileSystemEventHandler):
    def __init__(self, target_name: str, callback: Callable[[], None], debounce_seconds: float = 0.5) -> None:
        self._target_name = target_name
        self._callback = callback
        self._debounce_seconds = debounce_seconds
        self._last_update = 0.0

    def on_modified(self, event: FileSystemEvent) -> None:
        if Path(event.src_path).name != self._target_name:
            return

        now = time.time()
        if now - self._last_update < self._debounce_seconds:
            return

        self._last_update = now
        logger.debug("Detected change to %s", event.src_path)
        self._callback()


class FocusFileWatcher:
    """Watches the directory containing the focus file and invokes a callback on change."""

    def __init__(self, focus_file: Path, callback: Callable[[], None]) -> None:
        self._focus_file = focus_file
        self._callback = callback
        self._observer: Observer | None = None

    def start(self) -> None:
        directory = self._focus_file.parent
        if not directory.exists():
            logger.warning("Focus file directory does not exist, file monitoring disabled: %s", directory)
            return

        handler = _DebouncedFileHandler(self._focus_file.name, self._callback)
        self._observer = Observer()
        self._observer.schedule(handler, str(directory), recursive=False)
        self._observer.start()
        logger.info("Watching %s for changes", self._focus_file)

    def stop(self) -> None:
        if self._observer is not None:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            logger.info("File watcher stopped")
