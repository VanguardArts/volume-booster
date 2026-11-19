#!/usr/bin/env bash
#
# Disable Volume Booster autostart-at-login.
set -euo pipefail

AUTOSTART="${XDG_CONFIG_HOME:-$HOME/.config}/autostart"
rm -f "$AUTOSTART/volume-booster.desktop"
echo "✔ Autostart disabled"
