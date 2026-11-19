#!/usr/bin/env bash
#
# Build a Debian/Ubuntu .deb package for Volume Booster using dpkg-deb.
#
# Output: build/deb/volume-booster_<version>_all.deb
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="1.1.2"
PKG="volume-booster"
STAGE="$ROOT/build/deb/${PKG}_${VERSION}_all"
DEBIAN="$STAGE/DEBIAN"

command -v dpkg-deb >/dev/null 2>&1 || {
    echo "error: dpkg-deb not found (install 'dpkg' / 'dpkg-dev')" >&2
    exit 1
}

rm -rf "$STAGE"
mkdir -p \
    "$STAGE/usr/bin" \
    "$STAGE/usr/share/applications" \
    "$STAGE/usr/share/icons/hicolor/scalable/apps" \
    "$STAGE/usr/share/doc/$PKG" \
    "$DEBIAN"

install -m 0755 "$ROOT/volume_booster.py"  "$STAGE/usr/bin/volume-booster"
install -m 0644 "$ROOT/packaging/volume-booster.desktop" "$STAGE/usr/share/applications/volume-booster.desktop"
install -m 0644 "$ROOT/packaging/volume-booster.svg"     "$STAGE/usr/share/icons/hicolor/scalable/apps/volume-booster.svg"
for sz in 16 24 32 48 64 96 128 256 512; do
    install -Dm 0644 "$ROOT/packaging/icons/hicolor/${sz}x${sz}/apps/volume-booster.png" \
        "$STAGE/usr/share/icons/hicolor/${sz}x${sz}/apps/volume-booster.png"
done

# Package metadata (render version placeholder, if any).
sed "s/__VERSION__/$VERSION/g" "$ROOT/packaging/debian/control" > "$DEBIAN/control"
install -m 0755 "$ROOT/packaging/debian/postinst" "$DEBIAN/postinst"

# Minimal copyright file.
cat > "$STAGE/usr/share/doc/$PKG/copyright" <<EOF
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: volume-booster
Source: https://github.com/VanguardArts/volume-booster

Files: *
Copyright: 2026 Vanguard Arts SRL
License: MIT
 See /usr/share/doc/$PKG/ for the full MIT license text.
EOF

# gzip the changelog-friendly doc entry (not strictly required).
cat > "$STAGE/usr/share/doc/$PKG/changelog.gz.tmp" <<EOF
$PKG ($VERSION) unstable; urgency=medium

  * Initial release.

 -- Vanguard Arts SRL <support@vanguardarts.com>  $(date -R)
EOF
gzip -c "$STAGE/usr/share/doc/$PKG/changelog.gz.tmp" > "$STAGE/usr/share/doc/$PKG/changelog.gz"
rm -f "$STAGE/usr/share/doc/$PKG/changelog.gz.tmp"

mkdir -p "$ROOT/build/deb"
DEB_FILE="$ROOT/build/deb/${PKG}_${VERSION}_all.deb"
dpkg-deb --build --root-owner-group "$STAGE" "$DEB_FILE" >/dev/null

echo "✔ Built $DEB_FILE"
ls -l "$DEB_FILE"
