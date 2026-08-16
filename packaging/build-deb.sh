#!/usr/bin/env bash
# Construiește shunt_<versiune>_all.deb în dist/. Cere doar dpkg-deb.
set -euo pipefail

SRC="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="$(sed -n 's/^__version__ = "\(.*\)"$/\1/p' "$SRC/shunt/__init__.py")"
[ -n "$VERSION" ] || { echo "nu găsesc versiunea în shunt/__init__.py" >&2; exit 1; }

BUILD="$(mktemp -d)"
trap 'rm -rf "$BUILD"' EXIT

"$SRC/packaging/stage.sh" "$BUILD"

install -d "$BUILD/DEBIAN"
cat > "$BUILD/DEBIAN/control" <<EOF
Package: shunt
Version: $VERSION
Section: net
Priority: optional
Architecture: all
Maintainer: George Dumitrescu <george@dumitres.co>
Depends: python3 (>= 3.10), python3-pyside6.qtwidgets, python3-pyside6.qtdbus, libglib2.0-bin, kwin-wayland | kwin-x11
Recommends: libnotify-bin
Description: Browser chooser for KDE Plasma 6
 Asks which browser should open a link, remembers the answer per source
 application, and shows up under the mouse pointer. Needs a KWin script for
 the two things Wayland does not give a plain client: which window was active
 and where the cursor is. Plasma 6 only; the Plasma 5 scripting API differs.
EOF

cat > "$BUILD/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
if [ "$1" = "configure" ]; then
    update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
    gtk-update-icon-cache -qtf /usr/share/icons/hicolor >/dev/null 2>&1 || true
    systemctl --global daemon-reload >/dev/null 2>&1 || true
fi
EOF
chmod 755 "$BUILD/DEBIAN/postinst"

mkdir -p "$SRC/dist"
dpkg-deb --root-owner-group --build "$BUILD" "$SRC/dist/shunt_${VERSION}_all.deb"
echo "→ dist/shunt_${VERSION}_all.deb"
