"""`shunt update` — actualizează instalarea curentă, oricare ar fi ea.

Nu descarcă și nu instalează nimic singur: dintr-un clone sare pe cel mai recent
tag și rulează install.sh, iar dintr-un pachet de sistem trimite la managerul de
pachete. Un auto-updater care scrie în /usr ar fi și inutil, și greu de auditat.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from . import __version__

PACKAGE_MANAGERS = [
    ("pacman", "sudo pacman -Syu shunt"),
    ("dnf", "sudo dnf upgrade shunt"),
    ("apt", "sudo apt update && sudo apt install --only-upgrade shunt"),
    ("zypper", "sudo zypper update shunt"),
]


def _checkout_root() -> Path | None:
    """Rădăcina sursei din care rulăm, dacă nu rulăm dintr-un pachet."""
    root = Path(__file__).resolve().parent.parent
    return root if (root / "install.sh").is_file() else None


def _package_hint() -> str:
    for binary, command in PACKAGE_MANAGERS:
        if shutil.which(binary):
            return command
    return "your package manager"


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True
    )


def _latest_tag(root: Path) -> str:
    listing = _git(root, "tag", "--list", "v*", "--sort=-v:refname")
    tags = [line.strip() for line in listing.stdout.splitlines() if line.strip()]
    return tags[0] if tags else ""


def _reload_kwin_script() -> None:
    """install.sh repornește daemonul, dar scriptul rulează în KWin, nu în noi."""
    for args in (
        ["/Scripting", "org.kde.kwin.Scripting.unloadScript", "shunt"],
        ["/KWin", "reconfigure"],
    ):
        subprocess.run(["qdbus6", "org.kde.KWin", *args], capture_output=True)


def run() -> int:
    print(f"shunt {__version__}")

    root = _checkout_root()
    if root is None:
        print("Installed as a system package. Update it with:")
        print(f"  {_package_hint()}")
        return 0

    if not (root / ".git").exists():
        print(f"{root} is not a git checkout, reinstalling the sources as they are.")
        return _install(root)

    fetch = _git(root, "fetch", "--tags", "--force")
    if fetch.returncode != 0:
        print(fetch.stderr.strip() or "git fetch failed.")
        return fetch.returncode

    tag = _latest_tag(root)
    if not tag:
        print("No release tag yet, reinstalling the current checkout.")
        return _install(root)

    head = _git(root, "rev-parse", "HEAD").stdout.strip()
    tagged = _git(root, "rev-parse", f"{tag}^{{commit}}").stdout.strip()
    if head == tagged:
        print(f"Already on {tag}.")
        return _install(root)

    print(f"Moving to {tag}")
    # Detached: releases sunt tag-uri, nu ramuri. Eșuează zgomotos dacă ai
    # modificări locale — mai bine decât să ți le arunce.
    checkout = _git(root, "checkout", "--detach", tag)
    if checkout.returncode != 0:
        print(checkout.stderr.strip() or "git checkout failed.")
        return checkout.returncode

    return _install(root)


def _install(root: Path) -> int:
    result = subprocess.run(["bash", str(root / "install.sh")])
    if result.returncode != 0:
        return result.returncode
    _reload_kwin_script()
    print("Done.")
    return 0
