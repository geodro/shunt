"""`shunt uninstall` - scoate instalarea per-utilizator făcută de install.sh.

Regulile și preferințele rămân, dacă nu ceri --purge: dezinstalarea nu e același
lucru cu renunțarea, iar o reinstalare peste o săptămână ar porni de la zero.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from .rules import config_path
from .settings import APP_DESKTOP, is_default

APP_ID = "co.dumitres.Shunt"
KWIN_ID = "shunt"


def _data_home() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))


def _targets() -> list[Path]:
    data = _data_home()
    return [
        Path.home() / ".local/bin/shunt",
        data / "applications" / f"{APP_ID}.desktop",
        data / "icons/hicolor/scalable/apps" / f"{APP_ID}.svg",
        data / "icons/hicolor/scalable/apps" / f"{APP_ID}-symbolic.svg",
        data / "dbus-1/services" / f"{APP_ID}.service",
        Path.home() / ".config/systemd/user/shunt.service",
        data / "kwin/scripts" / KWIN_ID,
    ]


def _quiet(*command: str) -> None:
    subprocess.run(command, capture_output=True)


def run(purge: bool = False) -> int:
    if is_default():
        print(f"Warning: {APP_DESKTOP} is still the default browser.")
        print("  Pick another one, for example:")
        print("  xdg-settings set default-web-browser org.mozilla.firefox.desktop")

    _quiet("systemctl", "--user", "disable", "--now", "shunt.service")

    removed = 0
    for target in _targets():
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        elif target.exists() or target.is_symlink():
            target.unlink()
        else:
            continue
        removed += 1
        print(f"removed {target}")

    _quiet("systemctl", "--user", "daemon-reload")
    _quiet(
        "kwriteconfig6", "--file", "kwinrc", "--group", "Plugins",
        "--key", f"{KWIN_ID}Enabled", "false",
    )
    _quiet("update-desktop-database", str(_data_home() / "applications"))
    _quiet("qdbus6", "org.kde.KWin", "/Scripting",
           "org.kde.kwin.Scripting.unloadScript", KWIN_ID)
    _quiet("qdbus6", "org.kde.KWin", "/KWin", "reconfigure")

    settings_dir = config_path().parent
    if purge and settings_dir.is_dir():
        shutil.rmtree(settings_dir)
        print(f"removed {settings_dir}")
    elif settings_dir.is_dir():
        print(f"Rules and preferences kept in {settings_dir} (shunt uninstall --purge)")

    if removed == 0:
        print("Nothing installed for this user.")
        print("If Shunt came from a package, remove it with your package manager.")
        return 0

    print("Uninstalled.")
    return 0
