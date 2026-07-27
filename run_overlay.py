"""Standalone entry point used to build the packaged executable.

`python -m cycling_overlay` is the normal way to run this from source; this
top-level script exists so PyInstaller has a script to point at that isn't
itself inside the package (a script run directly can't use the package's
relative imports).
"""

from __future__ import annotations

from cycling_overlay.__main__ import main

if __name__ == "__main__":
    main()
