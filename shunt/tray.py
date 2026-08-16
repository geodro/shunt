"""Iconița din tray — semnul că daemonul e sus și scurtătura către setări."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QObject
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from . import rules
from .i18n import _
from .settings import tray_icon


class Tray(QObject):
    def __init__(self, on_settings: Callable[[], None], parent: QObject | None = None):
        super().__init__(parent)
        self._icon = QSystemTrayIcon(tray_icon(), self)

        menu = QMenu()
        settings_action = QAction(_("Settings…"), menu)
        settings_action.triggered.connect(lambda: on_settings())
        quit_action = QAction(_("Quit"), menu)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(settings_action)
        menu.addSeparator()
        menu.addAction(quit_action)

        self._menu = menu  # QMenu fără părinte: ținem noi referința
        self._icon.setContextMenu(menu)
        self._icon.activated.connect(
            lambda reason: on_settings()
            if reason == QSystemTrayIcon.ActivationReason.Trigger
            else None
        )
        self.refresh()
        self._icon.show()

    def refresh(self) -> None:
        count = len(rules.load())
        template = "Shunt: {count} rule" if count == 1 else "Shunt: {count} rules"
        self._icon.setToolTip(_(template).format(count=count))
