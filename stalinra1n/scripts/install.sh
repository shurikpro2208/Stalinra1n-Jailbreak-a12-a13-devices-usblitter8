#!/usr/bin/env bash
set -euo pipefail

echo "usbliter8 Payload Injector Installer"
echo "===================================="
echo ""

# Check Python
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON="$cmd"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "Error: Python 3 not found"
    exit 1
fi

echo "Using: $($PYTHON --version)"
echo ""

# Install
cd "$(dirname "$0")/.."
$PYTHON -m pip install --upgrade pip
$PYTHON -m pip install -e .
$PYTHON -m pip install customtkinter rich pyusb

echo ""
echo "Installation complete!"
echo ""
echo "Run: stalinra1n tui"
echo "Or:  stalinra1n-gui"
