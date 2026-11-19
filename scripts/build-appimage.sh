#!/usr/bin/env bash
#
# Build an AppImage for Volume Booster.
#
# A portable PyQt6 app is non-trivial to bundle (Python + full Qt stack), so we
# build on top of `python-appimage` to get a relocatable Python, install PyQt6
# into it, then wrap the result with appimagetool.
#
# Requirements: docker OR a local python-appimage build; appimagetool.
# This is best run in CI (see .github/workflows/release.yml).
#
# Output: build/appimage/Volume_Booster-x86_64.AppImage
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP="Volume Booster"
PKG="volume-booster"
OUT="$ROOT/build/appimage"
APPDIR="$OUT/AppDir"

ARCH=$(uname -m)
APPIMAGETOOL_URL="https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-${ARCH}.AppImage"

mkdir -p "$APPDIR"

# --- python-appimage (relocatable CPython) -----------------------------------
PYAPPIMAGE="python3.12.3-cp312-cp312-manylinux2014_${ARCH}.AppImage"
if [ ! -x "$OUT/$PYAPPIMAGE" ]; then
    curl -fsSL "https://github.com/niess/python-appimage/releases/download/python3.12/$PYAPPIMAGE" \
        -o "$OUT/$PYAPPIMAGE"
    chmod +x "$OUT/$PYAPPIMAGE"
    (cd "$OUT" && ./"$PYAPPIMAGE" --appimage-extract >/dev/null)
fi

# Install PyQt6 into the extracted python (this is the slow, size-heavy step).
"$OUT/squashfs-root/AppRun" -m pip install --quiet PyQt6

# --- assemble AppDir ---------------------------------------------------------
cp -a "$OUT/squashfs-root/." "$APPDIR/"
install -Dm755 "$ROOT/volume_booster.py" "$APPDIR/usr/bin/$PKG"

cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
export PATH="$HERE/usr/bin:$PATH"
# python-appimage keeps its payload under usr/; run the script with it.
exec "$HERE/usr/bin/python3.12" "$HERE/usr/bin/volume-booster" "$@"
EOF
chmod +x "$APPDIR/AppRun"

install -Dm644 "$ROOT/packaging/volume-booster.desktop" "$APPDIR/$APP.desktop"
install -Dm644 "$ROOT/packaging/icons/hicolor/256x256/apps/volume-booster.png" \
    "$APPDIR/volume-booster.png"

# --- appimagetool ------------------------------------------------------------
if [ ! -x "$OUT/appimagetool" ]; then
    curl -fsSL "$APPIMAGETOOL_URL" -o "$OUT/appimagetool"
    chmod +x "$OUT/appimagetool"
fi

"$OUT/appimagetool" "$APPDIR" "$OUT/$PKG-${ARCH}.AppImage"

echo "✔ AppImage built: $OUT/$PKG-${ARCH}.AppImage"
