#!/usr/bin/env bash
#
# Build an RPM for Volume Booster (works on Fedora, RHEL, Rocky/Alma, openSUSE).
#
# Output: build/rpm/RPMS/noarch/volume-booster-<version>-<release>.noarch.rpm
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="1.1.4"
NAME="volume-booster"
OUT="$ROOT/build/rpm"
TARBALL="$NAME-$VERSION.tar.gz"

command -v rpmbuild >/dev/null 2>&1 || {
    echo "error: rpmbuild not found (install 'rpm-build' / 'rpm')" >&2
    exit 1
}
command -v tar >/dev/null 2>&1 || { echo "error: tar not found" >&2; exit 1; }

rm -rf "$OUT"
mkdir -p "$OUT"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}

# Stage a clean source tree under the versioned directory expected by %setup.
STAGE="$(mktemp -d)/$NAME-$VERSION"
mkdir -p "$STAGE"
cp -a "$ROOT/volume_booster.py" "$ROOT/packaging" "$ROOT/LICENSE" "$ROOT/README.md" "$STAGE/"
tar -C "$(dirname "$STAGE")" -czf "$OUT/SOURCES/$TARBALL" "$NAME-$VERSION"
rm -rf "$(dirname "$STAGE")"

rpmbuild -bb --define "_topdir $OUT" "$ROOT/packaging/rpm/volume-booster.spec"

echo "✔ RPM built:"
find "$OUT/RPMS" -name '*.rpm' -exec ls -l {} \;
