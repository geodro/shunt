"""Notificarea de după deschiderea automată — singura cale de a te răzgândi.

Un proces nou nu poate citi pe Wayland ce taste ții apăsate, deci varianta
„ține Ctrl ca să vezi selectorul" nu e posibilă. Notificarea o înlocuiește.

Prin notify-send, nu direct pe D-Bus: `replaces_id` din org.freedesktop.
Notifications e uint32, iar PySide6 trimite orice int Python ca int32, deci
apelul direct e respins de serverul de notificări.
"""

from __future__ import annotations

import shutil
from typing import Callable

from PySide6.QtCore import QObject, QProcess

from .i18n import _

TIMEOUT_MS = 5000
_ACTION = "choose"


class Notifier(QObject):
    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._available = shutil.which("notify-send") is not None
        if not self._available:
            print("shunt: notify-send not found, no notifications")

    def opened_in(
        self, browser_name: str, icon: str, on_choose: Callable[[], None]
    ) -> None:
        if not self._available:
            return

        process = QProcess(self)
        process.finished.connect(
            lambda _code, _status, p=process: self._on_finished(p, on_choose)
        )
        process.start(
            "notify-send",
            [
                "--app-name=Shunt",
                f"--icon={icon}",
                f"--expire-time={TIMEOUT_MS}",
                "--hint=string:desktop-entry:co.dumitres.Shunt",
                f"--action={_ACTION}={_('Choose another')}",
                _("Opened in {browser}").format(browser=browser_name),
            ],
        )

    def _on_finished(self, process: QProcess, on_choose: Callable[[], None]) -> None:
        # --action face notify-send să aștepte și să scrie pe stdout ce s-a apăsat.
        chosen = bytes(process.readAllStandardOutput()).decode(errors="replace").strip()
        process.deleteLater()
        if chosen == _ACTION:
            on_choose()
