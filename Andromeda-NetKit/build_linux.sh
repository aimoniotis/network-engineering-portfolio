#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
python3 -c "import tkinter" || {
    echo "Tkinter is missing. Install it with your distribution's python3-tk package." >&2
    exit 1
}
python3 -m venv .venv
.venv/bin/python -m pip install --quiet --disable-pip-version-check -r requirements-build.txt
.venv/bin/python -m PyInstaller --clean --noconfirm --log-level WARN AndromedaNetKit.spec

echo "Build complete: $(pwd)/dist/AndromedaNetKit"
echo "Run it with: ./dist/AndromedaNetKit"
