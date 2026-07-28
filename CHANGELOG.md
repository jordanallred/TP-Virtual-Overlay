# Changelog

## 0.4.0

### Added
- In-app Settings dialog (⚙ icon): cadence/power thresholds, hide-units, graph
  window duration, and opacity, with no command line required.
- Settings and window position now persist across restarts (`settings.json`).
- LIVE / NO DATA header indicator that flips if TPVirtual stops sending data.
- System tray icon with Show/Hide, Reset Position, and Quit, so the window can
  always be recovered even if dragged off-screen or hidden.
- Per-monitor DPI awareness, so the overlay renders sharp instead of blurry on
  scaled displays.
- Windows installer (`TPVirtualOverlaySetup.exe`) alongside the existing
  portable exe — per-user install, optional desktop shortcut, optional launch
  at Windows startup, clean uninstall.
- Automated test suite (pytest), run in CI on every push.
- MIT license.

### Fixed
- The file watcher would silently never attach if the overlay was started
  before TPVirtual had ever created its `Broadcast` folder. It now retries
  until the folder appears.
- Metric values now use a tabular/monospace font so digits don't jitter
  horizontally as values change.

## 0.3.0

- Standalone Windows executable (PyInstaller) and automated release pipeline
  (GitHub Actions builds and publishes the exe on a version tag push).
- Custom app icon.
- Log location moved to `%LOCALAPPDATA%\CyclingOverlay\`, independent of the
  install location (required for the packaged exe to log reliably).

## 0.2.0

- Redesigned overlay UI (rounded cards, rolling power/heart-rate graphs).

## 0.1.0

- Initial release: draggable always-on-top overlay reading TPVirtual's
  `focus.json`.
