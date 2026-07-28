import time

from cycling_overlay.watcher import FocusFileWatcher, _DebouncedFileHandler


class _FakeEvent:
    def __init__(self, path: str) -> None:
        self.src_path = path


def _wait_until(predicate, timeout=2.0, interval=0.02):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()


def test_debounce_suppresses_rapid_repeats():
    calls = []
    handler = _DebouncedFileHandler("focus.json", lambda: calls.append(1), debounce_seconds=0.3)

    handler.on_modified(_FakeEvent("C:/x/focus.json"))
    handler.on_modified(_FakeEvent("C:/x/focus.json"))
    assert calls == [1]

    time.sleep(0.35)
    handler.on_modified(_FakeEvent("C:/x/focus.json"))
    assert calls == [1, 1]


def test_debounce_ignores_unrelated_files():
    calls = []
    handler = _DebouncedFileHandler("focus.json", lambda: calls.append(1))

    handler.on_modified(_FakeEvent("C:/x/nearest.json"))

    assert calls == []


def test_watcher_attaches_immediately_when_directory_exists(tmp_path):
    focus_file = tmp_path / "focus.json"
    watcher = FocusFileWatcher(focus_file, lambda: None, retry_seconds=0.05)

    watcher.start()
    try:
        assert watcher._observer is not None
    finally:
        watcher.stop()


def test_watcher_retries_until_directory_appears(tmp_path):
    target_dir = tmp_path / "Broadcast"
    focus_file = target_dir / "focus.json"
    watcher = FocusFileWatcher(focus_file, lambda: None, retry_seconds=0.05)

    watcher.start()
    try:
        assert watcher._observer is None, "should not attach before the directory exists"

        target_dir.mkdir()

        assert _wait_until(lambda: watcher._observer is not None), (
            "watcher never attached after the directory was created"
        )
    finally:
        watcher.stop()

    assert watcher._observer is None
    assert watcher._retry_timer is None


def test_stop_before_directory_exists_cancels_pending_retry(tmp_path):
    focus_file = tmp_path / "never-created" / "focus.json"
    watcher = FocusFileWatcher(focus_file, lambda: None, retry_seconds=5.0)

    watcher.start()
    assert watcher._retry_timer is not None

    watcher.stop()

    assert watcher._retry_timer is None
    assert watcher._observer is None

    # Directory appearing after stop() must not resurrect the watcher.
    focus_file.parent.mkdir()
    time.sleep(0.1)
    assert watcher._observer is None
