#!/usr/bin/env bash
#
# Portable installer for Volume Booster.
#
# Default installs to ~/.local (no root needed). Override with:
#   PREFIX=/usr/local ./install.sh        (or use sudo PREFIX=/usr ./install.sh)
set -euo pipefail

PREFIX="${PREFIX:-$HOME/.local}"
BIN="$PREFIX/bin"
APPS="$PREFIX/share/applications"
ICONS="$PREFIX/share/icons/hicolor/scalable/apps"

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$BIN" "$APPS" "$ICONS"

install -m 0755 "$SRC_DIR/volume_booster.py"  "$BIN/volume-booster"
install -m 0644 "$SRC_DIR/packaging/volume-booster.desktop" "$APPS/volume-booster.desktop"
install -m 0644 "$SRC_DIR/packaging/volume-booster.svg"     "$ICONS/volume-booster.svg"

# Refresh desktop/icon caches when the tools exist.
command -v update-desktop-database >/dev/null 2>&1 \
  && update-desktop-database "$PREFIX/share/applications" 2>/dev/null || true
command -v gtk-update-icon-cache >/dev/null 2>&1 \
  && gtk-update-icon-cache -f -t "$PREFIX/share/icons/hicolor" 2>/dev/null || true

echo "✔ Volume Booster installed to $PREFIX"
echo "  Launch with:  volume-booster"
echo "  ...or find 'Volume Booster' in your application menu."
