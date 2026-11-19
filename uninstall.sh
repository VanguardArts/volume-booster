#!/usr/bin/env bash
#
# Uninstall Volume Booster (portable install only — matches install.sh).
set -euo pipefail

PREFIX="${PREFIX:-$HOME/.local}"

rm -f \
  "$PREFIX/bin/volume-booster" \
  "$PREFIX/share/applications/volume-booster.desktop" \
  "$PREFIX/share/icons/hicolor/scalable/apps/volume-booster.svg"

command -v update-desktop-database >/dev/null 2>&1 \
  && update-desktop-database "$PREFIX/share/applications" 2>/dev/null || true

echo "✔ Volume Booster uninstalled from $PREFIX"
