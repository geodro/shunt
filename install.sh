#!/usr/bin/env bash
# Install Shunt for the current user (Plasma 6).
#   ./install.sh            install, leaving the default browser alone
#   ./install.sh --default  and make it the handler for http/https
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
BIN="$HOME/.local/bin/shunt"
APP_ID="co.dumitres.Shunt"
KWIN_ID="shunt"

# --- preflight ---------------------------------------------------------------
# Shunt is a Plasma 6 application, not a portable one: without the KWin script it
# cannot tell where a link came from, which is the whole point. Fail here rather
# than after everything is in place. SHUNT_SKIP_CHECKS=1 to install anyway.

fail() {
    echo "✗ $1" >&2
    echo "  Set SHUNT_SKIP_CHECKS=1 to install anyway." >&2
    exit 1
}

warn() { echo "⚠  $1" >&2; }

if [ -z "${SHUNT_SKIP_CHECKS:-}" ]; then
    for tool in python3 gio kwriteconfig6 qdbus6; do
        command -v "$tool" >/dev/null 2>&1 || fail "$tool not found."
    done

    python3 - <<'PY' || fail "Python 3.10+ with PySide6 (QtWidgets, QtDBus) is required."
import sys
assert sys.version_info >= (3, 10), sys.version
import PySide6.QtWidgets, PySide6.QtDBus  # noqa: F401
PY

    # `|| true`: cu pipefail, un plasmashell lipsă ar omorî scriptul aici, prin
    # set -e, înainte să apucăm să dăm mesajul care explică de ce.
    plasma="$(plasmashell --version 2>/dev/null | awk '{print $2}')" || true
    case "$plasma" in
        6.*) ;;
        "")  fail "Plasma not found. Shunt needs KDE Plasma 6." ;;
        *)   fail "Plasma $plasma found. Shunt needs 6.x; the KWin scripting API differs." ;;
    esac

    command -v notify-send >/dev/null 2>&1 ||
        warn "notify-send not found, so there is no 'Choose another' notification."

    qdbus6 org.kde.KWin /KWin org.freedesktop.DBus.Peer.Ping >/dev/null 2>&1 ||
        warn "KWin is not answering on D-Bus. Log into a Plasma session before using Shunt."
fi

echo "→ Command: $BIN"
mkdir -p "$(dirname "$BIN")"
chmod +x "$SRC/bin/shunt"
ln -sfn "$SRC/bin/shunt" "$BIN"

echo "→ Desktop entry"
mkdir -p "$DATA/applications"
sed "s|@BIN@|$BIN|g" "$SRC/data/$APP_ID.desktop" > "$DATA/applications/$APP_ID.desktop"

echo "→ Icon"
ICONS="$DATA/icons/hicolor/scalable/apps"
mkdir -p "$ICONS"
cp "$SRC/data/icons/$APP_ID.svg"          "$ICONS/$APP_ID.svg"
cp "$SRC/data/icons/$APP_ID-symbolic.svg" "$ICONS/$APP_ID-symbolic.svg"

echo "→ D-Bus activation"
mkdir -p "$DATA/dbus-1/services"
sed "s|@BIN@|$BIN|g" "$SRC/data/$APP_ID.service" > "$DATA/dbus-1/services/$APP_ID.service"

echo "→ systemd service (starts at login)"
mkdir -p "$HOME/.config/systemd/user"
sed "s|@BIN@|$BIN|g" "$SRC/data/shunt.service" > "$HOME/.config/systemd/user/shunt.service"
systemctl --user daemon-reload
systemctl --user enable shunt.service
systemctl --user restart shunt.service  # reinstalling must pick up the new code

echo "→ KWin script"
KWIN_DEST="$DATA/kwin/scripts/$KWIN_ID"
mkdir -p "$KWIN_DEST/contents/code"
cp "$SRC/kwin/metadata.json"         "$KWIN_DEST/metadata.json"
cp "$SRC/kwin/contents/code/main.js" "$KWIN_DEST/contents/code/main.js"
kwriteconfig6 --file kwinrc --group Plugins --key "${KWIN_ID}Enabled" true

echo "→ Reloading"
update-desktop-database "$DATA/applications" >/dev/null 2>&1 || true
gtk-update-icon-cache -qtf "$DATA/icons/hicolor" >/dev/null 2>&1 || true
qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.unloadScript "$KWIN_ID" >/dev/null 2>&1 || true
qdbus6 org.kde.KWin /KWin reconfigure >/dev/null 2>&1 || true

if [ "${1:-}" = "--default" ]; then
    echo "→ Set as the default browser"
    xdg-settings set default-web-browser "$APP_ID.desktop"
fi

echo
echo "✅ Done."
if [ "${1:-}" != "--default" ]; then
    echo "   To take over links:  xdg-settings set default-web-browser $APP_ID.desktop"
fi
echo "   Try it:              gio open https://example.com"
echo "   Rules:               ${XDG_CONFIG_HOME:-$HOME/.config}/shunt/rules.json"
