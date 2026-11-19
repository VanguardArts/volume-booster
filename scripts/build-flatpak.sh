#!/usr/bin/env bash
#
# Build the Flatpak for Volume Booster. Requires flatpak + flatpak-builder and
# the org.kde.Platform / org.kde.Sdk runtimes (6.x).
#
# Output: build/flatpak/volume-booster.flatpak
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="$ROOT/packaging/flatpak/com.vanguardarts.VolumeBooster.yml"
OUT="$ROOT/build/flatpak"

command -v flatpak-builder >/dev/null 2>&1 || {
    echo "error: flatpak-builder not found (install 'flatpak-builder')" >&2
    exit 1
}

flatpak remote-add --if-not-exists --user flathub https://flathub.org/repo/flathub.flatpakrepo

mkdir -p "$OUT"
flatpak-builder --force-clean --user --install-deps-from=flathub \
    "$OUT/build-dir" "$MANIFEST"

flatpak build-export "$OUT/repo" "$OUT/build-dir"
flatpak build-bundle "$OUT/repo" "$OUT/volume-booster.flatpak" \
    com.vanguardarts.VolumeBooster

echo "✔ Flatpak built: $OUT/volume-booster.flatpak"
