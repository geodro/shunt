"""shunt — selector de browser pentru Plasma. Proces rezident, activat prin D-Bus."""

from __future__ import annotations

import os
import sys

from PySide6.QtCore import QObject, QTimer
from PySide6.QtDBus import QDBusConnection, QDBusInterface
from PySide6.QtWidgets import QApplication

from . import __version__, browsers, config, rules, service, uninstall, update
from .chooser import Chooser
from .notify import Notifier
from .settings import Settings, app_icon
from .tray import Tray

APP_ID = "co.dumitres.Shunt"
DEBUG = bool(os.environ.get("SHUNT_DEBUG"))


class Controller(QObject):
    def __init__(self):
        super().__init__()
        self._window: Chooser | None = None
        self._source_class = ""
        self._notifier = Notifier(self)
        self._settings: Settings | None = None
        self._tray: Tray | None = None

    def start(self) -> None:
        """Abia după ce am luat numele de pe bus — altfel a doua instanță clipește în tray."""
        self._apply_tray(config.load()["tray_icon"])

    def _apply_tray(self, enabled: bool) -> None:
        if enabled and self._tray is None:
            self._tray = Tray(self.show_settings, self)
        elif not enabled and self._tray is not None:
            self._tray.deleteLater()
            self._tray = None

    # --- apelate din D-Bus -------------------------------------------------

    def activated(self) -> None:
        """Click pe Shunt în lansator: nu avem ce link deschide, deci arătăm setările."""
        self.show_settings()

    def set_source(self, resource_class: str, caption: str) -> None:
        self._source_class = resource_class
        if DEBUG:
            print(f"shunt: source = {resource_class!r}", flush=True)

    def open_url(self, url: str) -> None:
        if not url.startswith(("http://", "https://")):
            print(f"shunt: ignoring {url!r} (unsupported scheme)")
            return

        source = self._source_class
        target = rules.match(rules.load(), source, url)
        if target:
            match = next(
                (b for b in browsers.discover() if b.desktop_id == target), None
            )
            if match:
                browsers.launch(match, url)
                if config.load()["notifications"]:
                    self._notifier.opened_in(
                        match.name, match.icon, lambda: self.show_chooser(url, source)
                    )
                return
            print(f"shunt: rule points at {target}, which no longer exists")

        self.show_chooser(url, source)

    # --- logică ------------------------------------------------------------

    def show_settings(self) -> None:
        if self._settings is None:
            self._settings = Settings()
            self._settings.tray_toggled.connect(self._apply_tray)
            self._settings.changed.connect(self._on_rules_changed)
        self._settings.show()
        self._settings.raise_()
        self._settings.activateWindow()

    def show_chooser(self, url: str, source_class: str = "") -> None:
        available = browsers.discover()
        if not available:
            print("shunt: no browser installed")
            return

        # O singură fereastră; un al doilea link o înlocuiește.
        if self._window:
            self._window.close()

        window = Chooser(available, url, browsers.app_name(source_class))
        window.chosen.connect(
            lambda browser, remember: self._launch(browser, url, source_class, remember)
        )
        window.destroyed.connect(self._forget_window)
        window.show()
        window.raise_()
        window.activateWindow()
        self._window = window

    def _forget_window(self, *_args) -> None:
        self._window = None

    def _on_rules_changed(self) -> None:
        if self._tray:
            self._tray.refresh()

    def _launch(self, browser, url: str, source_class: str, remember: bool) -> None:
        if remember and source_class:
            rules.remember(source_class, browser.desktop_id)
            self._on_rules_changed()
            if self._settings and self._settings.isVisible():
                self._settings.refresh()
        browsers.launch(browser, url)


def _forward_to_running(urls: list[str]) -> bool:
    """Instanța deja pornită preia treaba; noi ieșim."""
    iface = QDBusInterface(
        service.BUS_NAME,
        service.OBJECT_PATH,
        "org.freedesktop.Application",
        QDBusConnection.sessionBus(),
    )
    if not iface.isValid():
        return False
    if urls:
        iface.call("Open", urls, {})
    else:
        iface.call("Activate", {})
    return True


USAGE = """shunt — browser chooser for Plasma

  shunt                 start the daemon, or show the settings window
  shunt open <url>...   open the given links through Shunt
  shunt <url>...        same, shorthand
  shunt update          update this installation
  shunt uninstall       remove it for this user (--purge drops rules too)
  shunt --version       print the version
"""


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    args = argv[1:]

    if args and args[0] in ("-h", "--help"):
        print(USAGE)
        return 0
    if args and args[0] == "--version":
        print(f"shunt {__version__}")
        return 0
    if args and args[0] == "update":
        return update.run()
    if args and args[0] == "uninstall":
        return uninstall.run(purge="--purge" in args)
    if args and args[0] == "open":
        args = args[1:]

    urls = [a for a in args if not a.startswith("-")]

    app = QApplication(argv)
    app.setApplicationName("shunt")
    # Fără setApplicationDisplayName: Qt ar lipi „ — Shunt" la titluri, iar scriptul
    # KWin recunoaște selectorul exact după titlu.
    app.setDesktopFileName(APP_ID)  # din el iese resourceClass, de care depinde KWin
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(app_icon())

    controller = Controller()
    if not service.register(controller):
        if _forward_to_running(urls):
            return 0
        print("shunt: already running")
        return 0

    controller.start()

    for url in urls:
        QTimer.singleShot(0, lambda u=url: controller.open_url(u))

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
