#!/usr/bin/env bash
#
# Enable Volume Booster to start automatically at login (XDG autostart).
set -euo pipefail

# Resolve the installed binary to an absolute path — safest at login time,
# when ~/.local/bin may not yet be on PATH.
BIN="$(command -v volume-booster 2>/dev/null || true)"
if [ -z "$BIN" ]; then
    BIN="$HOME/.local/bin/volume-booster"
fi
if [ ! -x "$BIN" ]; then
    echo "error: volume-booster not found (run ./install.sh first)" >&2
    exit 1
fi

AUTOSTART="${XDG_CONFIG_HOME:-$HOME/.config}/autostart"
mkdir -p "$AUTOSTART"

cat > "$AUTOSTART/volume-booster.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Volume Booster
Comment=Boost system audio above 100% for quiet videos
Exec=$BIN
Icon=volume-booster
Terminal=false
Categories=AudioVideo;Audio;Utility;
X-GNOME-Autostart-enabled=true
EOF

echo "✔ Volume Booster will start automatically at login"
echo "  wrote: $AUTOSTART/volume-booster.desktop"
