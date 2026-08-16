#!/usr/bin/env bash
# Așază arborele de instalare în $1. Folosit și de .deb, și de .rpm, ca layout-ul
# să existe într-un singur loc.
set -euo pipefail

DEST="${1:?usage: stage.sh <destdir>}"
SRC="$(cd "$(dirname "$0")/.." && pwd)"
BIN="/usr/bin/shunt"

install -Dm755 "$SRC/bin/shunt" "$DEST/usr/bin/shunt"

install -d "$DEST/usr/lib/shunt/shunt"
install -Dm644 "$SRC"/shunt/*.py -t "$DEST/usr/lib/shunt/shunt"

install -d "$DEST/usr/share/applications"
sed "s|@BIN@|$BIN|g" "$SRC/data/co.dumitres.Shunt.desktop" \
    > "$DEST/usr/share/applications/co.dumitres.Shunt.desktop"

install -d "$DEST/usr/share/dbus-1/services"
sed "s|@BIN@|$BIN|g" "$SRC/data/co.dumitres.Shunt.service" \
    > "$DEST/usr/share/dbus-1/services/co.dumitres.Shunt.service"

install -d "$DEST/usr/lib/systemd/user"
sed "s|@BIN@|$BIN|g" "$SRC/data/shunt.service" \
    > "$DEST/usr/lib/systemd/user/shunt.service"

# Pachetul nu poate rula `systemctl --user enable` pentru fiecare utilizator;
# symlink-ul în .wants pornește serviciul la login pentru toți.
install -d "$DEST/usr/lib/systemd/user/graphical-session.target.wants"
ln -sf ../shunt.service \
    "$DEST/usr/lib/systemd/user/graphical-session.target.wants/shunt.service"

install -Dm644 "$SRC/kwin/metadata.json" "$DEST/usr/share/kwin/scripts/shunt/metadata.json"
install -Dm644 "$SRC/kwin/contents/code/main.js" \
    "$DEST/usr/share/kwin/scripts/shunt/contents/code/main.js"

install -Dm644 "$SRC/data/icons/co.dumitres.Shunt.svg" \
    "$DEST/usr/share/icons/hicolor/scalable/apps/co.dumitres.Shunt.svg"
install -Dm644 "$SRC/data/icons/co.dumitres.Shunt-symbolic.svg" \
    "$DEST/usr/share/icons/hicolor/scalable/apps/co.dumitres.Shunt-symbolic.svg"

install -Dm644 "$SRC/README.md" "$DEST/usr/share/doc/shunt/README.md"
