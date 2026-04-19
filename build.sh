#!/bin/bash
# Build VDitto from WSL. Launches Windows build.bat via cmd.exe.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WIN_BAT="$(wslpath -w "$SCRIPT_DIR/build.bat")"
echo "Launching Windows build..."
cmd.exe /c "$WIN_BAT"
