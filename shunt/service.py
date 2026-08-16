"""Interfețele D-Bus. Numele și calea derivă din id-ul .desktop, cum cere spec-ul."""

from __future__ import annotations

from PySide6.QtCore import ClassInfo, QObject, Slot
from PySide6.QtDBus import QDBusAbstractAdaptor, QDBusConnection

BUS_NAME = "co.dumitres.Shunt"
OBJECT_PATH = "/co/dumitres/Shunt"


@ClassInfo({"D-Bus Interface": "org.freedesktop.Application"})
class ApplicationAdaptor(QDBusAbstractAdaptor):
    """https://specifications.freedesktop.org/desktop-entry-spec (DBusActivatable)."""

    def __init__(self, controller: QObject):
        super().__init__(controller)
        self._controller = controller

    @Slot("QVariantMap")
    def Activate(self, platform_data):  # noqa: N802 - nume impus de D-Bus
        self._controller.activated()

    @Slot("QStringList", "QVariantMap")
    def Open(self, uris, platform_data):  # noqa: N802
        for uri in uris:
            self._controller.open_url(uri)

    @Slot(str, "QVariantList", "QVariantMap")
    def ActivateAction(self, action_name, parameters, platform_data):  # noqa: N802
        self._controller.activated()


@ClassInfo({"D-Bus Interface": "co.dumitres.Shunt.Kwin"})
class KwinAdaptor(QDBusAbstractAdaptor):
    """Alimentată de scriptul KWin (kwin/contents/code/main.js)."""

    def __init__(self, controller: QObject):
        super().__init__(controller)
        self._controller = controller

    @Slot(str, str, str)
    def ActiveWindowChanged(self, caption, resource_class, resource_name):  # noqa: N802
        self._controller.set_source(resource_class, caption)


def register(controller: QObject) -> bool:
    """False dacă numele e deja luat (rulează altă instanță)."""
    bus = QDBusConnection.sessionBus()
    if not bus.isConnected():
        raise RuntimeError("shunt: nu există bus de sesiune")

    ApplicationAdaptor(controller)
    KwinAdaptor(controller)
    if not bus.registerObject(
        OBJECT_PATH, controller, QDBusConnection.RegisterOption.ExportAdaptors
    ):
        raise RuntimeError(f"shunt: nu pot înregistra obiectul {OBJECT_PATH}")

    return bus.registerService(BUS_NAME)
