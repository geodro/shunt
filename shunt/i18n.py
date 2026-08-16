"""Traduceri.

Șirurile din cod sunt în engleză și sunt și cheile tabelului — dacă lipsește o
traducere, textul rămâne în engleză în loc să apară o cheie goală în interfață.
Fără .ts/.qm: proiectul n-are pas de compilare și n-ar merita unul pentru atât.
"""

from __future__ import annotations

import os

RO = {
    # chooser
    "Remember for {app}": "Ține minte pentru {app}",
    "Remember": "Ține minte",
    "Could not identify the source application.": "N-am putut identifica aplicația-sursă.",
    "{name}  ({key})": "{name}  ({key})",
    # notificare
    "Opened in {browser}": "Deschis în {browser}",
    "Choose another": "Alege altul",
    # tray
    "Settings…": "Setări…",
    "Quit": "Ieși",
    "Shunt: {count} rule": "Shunt: {count} regulă",
    "Shunt: {count} rules": "Shunt: {count} reguli",
    # setări
    "Shunt handles http and https links.": "Shunt preia link-urile http și https.",
    "Another program handles links.": "Alt program preia link-urile.",
    "Make it the default browser": "Fă-l browser implicit",
    "Tray icon": "Iconiță în tray",
    "Notifications": "Notificări",
    "After a rule opens a browser, offer a way to pick another one.":
        "După ce o regulă deschide un browser, oferă și varianta de a alege altul.",
    "The daemon runs either way. Without it, Shunt cannot tell where you came from.":
        "Daemonul rulează oricum. Fără el, Shunt nu poate ști din ce aplicație vii.",
    "New rule": "Regulă nouă",
    "When I click from:": "Când dau click din:",
    "And the address is:": "Iar adresa e:",
    "Open in:": "Deschide în:",
    "Add": "Adaugă",
    "Update selected row": "Actualizează rândul selectat",
    "The first matching rule wins, so the order matters.":
        "Prima regulă care se potrivește câștigă, deci ordinea contează.",
    "Add exception": "Adaugă excepție",
    "Start a narrower rule for the same application, for one address only.":
        "Începe o regulă mai îngustă pentru aceeași aplicație, doar pentru o adresă.",
    "From application": "Din aplicația",
    "For address": "Pentru adresa",
    "Opens in": "Se deschide în",
    "Move up": "Mută sus",
    "Move down": "Mută jos",
    "Delete": "Șterge",
    "Open rules.json": "Deschide rules.json",
    "any application": "oricare aplicație",
    "any address": "orice adresă",
    "{browser} (missing)": "{browser} (lipsește)",
    "the application name or its app-id": "numele aplicației sau app-id-ul ei",
    "* for any site, or for example *.zoom.us": "* pentru orice site, sau de exemplu *.zoom.us",
    "Pick a browser.": "Alege un browser.",
    "It failed.": "A eșuat.",
}

TRANSLATIONS = {"ro": RO}


def _language() -> str:
    for variable in ("LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(variable)
        if value and value not in ("C", "POSIX"):
            return value.split(".")[0].split("_")[0].lower()
    return "en"


_TABLE = TRANSLATIONS.get(_language(), {})


def _(text: str) -> str:
    return _TABLE.get(text, text)
