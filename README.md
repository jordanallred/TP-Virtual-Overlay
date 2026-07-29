# Cycling Overlay

A draggable, always-on-top desktop overlay that displays live ride data — power,
heart rate, cadence, speed, distance, TSS, calories, grade, and draft — read
from [TrainingPeaks Virtual (TPVirtual)](https://www.trainingpeaks.com/virtual/#download)'s
`focus.json` broadcast file. Useful for streaming or recording indoor rides with
your stats visible on top of any window.

![Cycling overlay screenshot](screenshot.png)

## Features

- Live-updating metric cards (power, heart rate, cadence, speed, distance, time,
  TSS, calories, slope/grade, draft)
- In-app Settings dialog (⚙ icon) for units, thresholds, and opacity —
  no command line needed
- Optional minimum cadence/power thresholds that flash red when you fall below them
- A LIVE / NO DATA indicator so you can tell at a glance if TPVirtual has stopped sending data
- Semi-transparent, borderless, draggable window that stays on top of other apps,
  remembers where you left it, and renders sharp on scaled/high-DPI displays
- System tray icon to recover the window (Show/Hide, Reset Position) if it's ever lost,
  plus Quit
- Automatically refreshes as soon as TPVirtual writes new data (no polling)

## Requirements

Windows only (uses Tkinter; TPVirtual itself is Windows-only).

## Download (no Python required)

Grab the latest release from the
[Releases page](https://github.com/jordanallred/TP-Virtual-Overlay/releases/latest).
There are two options — pick whichever you prefer:

- **`TPVirtualOverlaySetup.exe`** — a normal installer: Start Menu shortcut, optional
  desktop shortcut, optional "launch at Windows startup", and a clean uninstaller.
  No admin rights required (installs to your user profile).
- **`TPVirtualOverlay.exe`** — the same app as a single portable file. Just copy it
  wherever you like and double-click; no install, nothing else written to your system.

Windows SmartScreen may warn you about either one since they aren't code-signed;
that's expected for a small open-source tool. Click **More info → Run anyway** if
you trust the source (or better yet, [read the code](cycling_overlay) and build it
yourself — see below).

1. Download and run either file above.
2. Start TPVirtual so it's writing to its `Broadcast/focus.json` file.
3. The overlay appears automatically once TPVirtual starts broadcasting.

The window is draggable from anywhere and can be closed with the ✕ button in the
header. Click the ⚙ icon to configure units, cadence/power thresholds, and
opacity — no command line needed; your choices are remembered for next time.
If the window is ever lost (dragged off-screen, hidden), use the system tray
icon's right-click menu to show it again or reset its position.

## For developers

### Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for dependency management

### Installation

```
uv sync
```

### Usage

Start TPVirtual so it's writing to its `Broadcast/focus.json` file, then run:

```
uv run python -m cycling_overlay
```

### Options

Everything here is also reachable from the in-app ⚙ Settings dialog, which is
the only way to change these when running the packaged exe/installer (there's
no CLI when double-clicking an exe). CLI flags are for developers running from
source and always override whatever's saved; anything you don't pass falls
back to the last value saved from the Settings dialog (see [Settings](#settings)).

| Flag | Description |
| --- | --- |
| `--focus-file PATH` | Path to TPVirtual's `focus.json` (default: `~/Documents/TPVirtual/Broadcast/focus.json`) |
| `--min-cadence N` | Cadence turns red when pedaling below `N` rpm |
| `--min-power N` | Power turns red when below `N` watts |
| `--imperial` | Use mph/miles instead of km/h/km |
| `--hide-units` | Hide unit labels next to values |
| `--opacity N` | Window opacity from 0.1 to 1.0 (default: 0.7) |

Example:

```
uv run python -m cycling_overlay --min-cadence 70 --min-power 150 --opacity 0.85
```

## Settings

Click the ⚙ icon in the header to open the Settings dialog: cadence/power
thresholds, hide-units, and opacity. Saving writes them to `settings.json`
alongside the log file (see [Logs](#logs)) so they persist across restarts —
this is what makes the packaged exe configurable without a command line.
Window position is saved automatically whenever you drag the overlay, no
dialog needed.

## System tray

The overlay lives in the system tray (you may need to click the little "^"
arrow in the taskbar to see hidden icons). Right-click it for:

- **Show/Hide** — toggle the overlay window (also the default double-click action)
- **Reset Position** — snap the window back to the top-left of your primary
  monitor; use this if it's ever been dragged off-screen or a monitor was
  unplugged
- **Quit** — fully exit the app (same as the ✕ button)

## Testing without TPVirtual

`cycling_overlay.testdata` generates a stream of random ride data and writes it to
a `focus.json` file at the configured interval, so you can develop or demo the
overlay without TPVirtual running:

```
uv run python -m cycling_overlay.testdata
```

It defaults to the same path as the overlay; pass `--output` to point it elsewhere
and `--interval` to change how often it writes (default: 1 second).

## Running the test suite

```
uv run pytest
```

Also runs automatically in CI (see [`.github/workflows/ci.yml`](.github/workflows/ci.yml))
alongside `ruff check`.

## Building the executable and installer yourself

Both release artifacts are built by
[`.github/workflows/release.yml`](.github/workflows/release.yml) whenever a
`vX.Y.Z` tag is pushed. To build the same things locally:

```
uv sync --all-groups
uv run pyinstaller TPVirtualOverlay.spec --noconfirm --clean
```

The resulting `dist/TPVirtualOverlay.exe` is a onefile, windowed (no console)
build with the app icon embedded. Regenerate `assets/icon.ico` with
`uv run python scripts/make_icon.py` if you want to change it.

To also build the installer, install [Inno Setup](https://jrsoftware.org/isinfo.php)
(`winget install JRSoftware.InnoSetup`), then:

```
iscc installer\TPVirtualOverlay.iss
```

This produces `installer_dist\TPVirtualOverlaySetup.exe`. It installs per-user
(no admin rights needed) with an optional desktop shortcut and an optional
"launch at Windows startup" task; see [`installer/TPVirtualOverlay.iss`](installer/TPVirtualOverlay.iss).

## How it works

TPVirtual continuously overwrites a `focus.json` file with the current rider's
stats while broadcasting. This app watches that file for changes (via
[watchdog](https://pypi.org/project/watchdog/)) and re-renders the overlay each
time it's updated, rather than polling on a timer.

## Project layout

```
cycling_overlay/
├── __main__.py            # Logging setup, DPI awareness, main() entry point
├── config.py              # CLI args + saved-settings merge, layout/unit definitions
├── metrics.py             # Parses a focus.json rider entry and handles unit conversions
├── watcher.py             # Debounced filesystem watcher for focus.json (retries until it exists)
├── settings.py            # Persisted settings.json (position, thresholds, units, opacity)
├── paths.py               # Shared app-data directory (logs + settings), frozen-safe
├── tray.py                # System tray icon (pystray)
├── ui.py                  # Tkinter overlay window + Settings dialog
└── testdata.py            # Synthetic focus.json generator for testing
tests/                      # pytest suite (metrics, config, settings, watcher, testdata, ui helpers)
run_overlay.py               # Entry script PyInstaller builds (imports cycling_overlay.__main__)
TPVirtualOverlay.spec        # PyInstaller build spec
installer/TPVirtualOverlay.iss  # Inno Setup installer script
assets/icon.ico               # App/window icon
scripts/make_icon.py          # Regenerates assets/icon.ico and assets/icon.png
.github/workflows/             # CI (lint + tests) and release (build exe + installer, publish on tag push)
```

## Logs

Runtime logs are written to `cycling_overlay.log` under
`%LOCALAPPDATA%\CyclingOverlay\` (rotated automatically at 5MB, keeping 3
backups), alongside the `settings.json` described in [Settings](#settings).
Check the log first if the overlay isn't behaving as expected.

## License

[MIT](LICENSE)
