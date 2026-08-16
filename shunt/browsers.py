"""Descoperirea browserelor instalate și lansarea lor."""

from __future__ import annotations

import os
import shlex
import subprocess
from configparser import ConfigParser, Error as ConfigError
from dataclasses import dataclass
from pathlib import Path

APP_ID = "co.dumitres.Shunt"

# Alte selectoare de browser: dacă apar în listă, un click ne trimite înapoi la noi.
EXCLUDED = {"co.dumitres.Shunt", "re.sonny.Junction", "org.gnome.Zenity"}

WANTED_SCHEME = "x-scheme-handler/https"


@dataclass(frozen=True)
class Browser:
    desktop_id: str  # "com.brave.Browser.desktop"
    name: str
    icon: str
    path: Path

    @property
    def app_id(self) -> str:
        return self.desktop_id.removesuffix(".desktop")


def _data_dirs() -> list[Path]:
    home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    system = os.environ.get(
        "XDG_DATA_DIRS", "/usr/local/share:/usr/share"
    ).split(":")
    dirs = [home] + [Path(d) for d in system if d]
    # Flatpak-urile instalate system-wide nu apar mereu în XDG_DATA_DIRS.
    dirs += [
        Path("/var/lib/flatpak/exports/share"),
        home / "flatpak/exports/share",
    ]
    seen, out = set(), []
    for d in dirs:
        apps = d / "applications"
        if apps.is_dir() and apps not in seen:
            seen.add(apps)
            out.append(apps)
    return out


def _parse(path: Path) -> Browser | None:
    parser = ConfigParser(interpolation=None, strict=False)
    try:
        parser.read(path, encoding="utf-8")
        entry = parser["Desktop Entry"]
    except (ConfigError, KeyError, OSError, UnicodeDecodeError):
        return None

    if entry.get("Type") != "Application":
        return None
    if entry.getboolean("NoDisplay", fallback=False):
        return None
    if entry.getboolean("Hidden", fallback=False):
        return None
    if WANTED_SCHEME not in entry.get("MimeType", ""):
        return None

    return Browser(
        desktop_id=path.name,
        name=entry.get("Name", path.stem),
        icon=entry.get("Icon", "web-browser"),
        path=path,
    )


def discover() -> list[Browser]:
    """Browserele instalate, deduplicate după desktop-id (prima apariție câștigă)."""
    found: dict[str, Browser] = {}
    for directory in _data_dirs():
        for path in sorted(directory.glob("*.desktop")):
            if path.stem in EXCLUDED or path.name in found:
                continue
            browser = _parse(path)
            if browser:
                found[browser.desktop_id] = browser
    return sorted(found.values(), key=lambda b: b.name.lower())


def installed_apps() -> list[tuple[str, str]]:
    """(nume, app-id) pentru aplicațiile vizibile — sursele posibile ale unui link."""
    found: dict[str, str] = {}
    for directory in _data_dirs():
        for path in sorted(directory.glob("*.desktop")):
            app_id = path.stem
            if app_id in found or app_id in EXCLUDED:
                continue
            parser = ConfigParser(interpolation=None, strict=False)
            try:
                parser.read(path, encoding="utf-8")
                entry = parser["Desktop Entry"]
            except (ConfigError, KeyError, OSError, UnicodeDecodeError):
                continue
            if entry.get("Type") != "Application":
                continue
            if entry.getboolean("NoDisplay", fallback=False):
                continue
            if entry.getboolean("Hidden", fallback=False):
                continue
            found[app_id] = entry.get("Name", app_id)
    return sorted(
        ((name, app_id) for app_id, name in found.items()),
        key=lambda pair: pair[0].lower(),
    )


def app_name(resource_class: str) -> str:
    """Numele afișabil al aplicației-sursă; pe Wayland resourceClass e chiar app-id-ul."""
    if not resource_class:
        return ""
    for directory in _data_dirs():
        for candidate in (f"{resource_class}.desktop", f"{resource_class.lower()}.desktop"):
            path = directory / candidate
            if not path.exists():
                continue
            parser = ConfigParser(interpolation=None, strict=False)
            try:
                parser.read(path, encoding="utf-8")
                return parser["Desktop Entry"].get("Name", resource_class)
            except (ConfigError, KeyError, OSError, UnicodeDecodeError):
                return resource_class
    return resource_class.rsplit(".", 1)[-1]


def launch(browser: Browser, url: str) -> None:
    """`gio launch` se ocupă de %u, de Flatpak și de DBusActivatable în locul nostru."""
    subprocess.Popen(
        ["gio", "launch", str(browser.path), url],
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


if __name__ == "__main__":  # pragma: no cover - ajutor de debug
    for b in discover():
        print(f"{b.desktop_id:40} {b.name:25} {b.icon}")
    print(shlex.join(["gio", "launch", "<desktop>", "<url>"]))
