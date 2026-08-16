"""Fereastra de setări: adaugă, ordonează și șterge regulile."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from PySide6.QtCore import QByteArray, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from . import browsers, config, rules
from .i18n import _

APP_DESKTOP = "co.dumitres.Shunt.desktop"
ANY_SOURCE = "any application"


def is_default() -> bool:
    try:
        out = subprocess.run(
            ["xdg-settings", "get", "default-web-browser"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return out.stdout.strip() == APP_DESKTOP


class Settings(QWidget):
    changed = Signal()
    tray_toggled = Signal(bool)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shunt")
        self.setWindowIcon(app_icon())
        self.resize(720, 520)

        layout = QVBoxLayout(self)
        layout.addLayout(self._build_status())
        layout.addWidget(self._build_form())
        hint = QLabel(_("The first matching rule wins, so the order matters."))
        hint.setWordWrap(True)
        layout.addWidget(hint)
        layout.addWidget(self._build_table(), 1)
        layout.addLayout(self._build_actions())

    # --- construcție -------------------------------------------------------

    def _build_status(self) -> QHBoxLayout:
        self._status = QLabel()
        self._make_default = QPushButton(_("Make it the default browser"))
        self._make_default.clicked.connect(self._set_default)

        self._tray = QCheckBox(_("Tray icon"))
        self._tray.setToolTip(
            _("The daemon runs either way. Without it, Shunt cannot tell where you came from.")
        )
        self._tray.toggled.connect(self._toggle_tray)

        self._notifications = QCheckBox(_("Notifications"))
        self._notifications.setToolTip(
            _("After a rule opens a browser, offer a way to pick another one.")
        )
        self._notifications.toggled.connect(
            lambda enabled: config.set_value("notifications", enabled)
        )

        row = QHBoxLayout()
        row.addWidget(self._status, 1)
        row.addWidget(self._notifications)
        row.addWidget(self._tray)
        row.addWidget(self._make_default)
        return row

    def _build_form(self) -> QGroupBox:
        self._source = QComboBox()
        self._source.setEditable(True)
        self._source.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._source.lineEdit().setPlaceholderText(_("the application name or its app-id"))

        self._host = QLineEdit()
        self._host.setPlaceholderText(_("* for any site, or for example *.zoom.us"))

        self._browser = QComboBox()

        add = QPushButton(_("Add"))
        add.clicked.connect(self._add)
        self._update = QPushButton(_("Update selected row"))
        self._update.setEnabled(False)
        self._update.clicked.connect(self._update_selected)

        buttons = QHBoxLayout()
        buttons.addWidget(add)
        buttons.addWidget(self._update)
        buttons.addStretch(1)

        form = QFormLayout()
        form.addRow(_("When I click from:"), self._source)
        form.addRow(_("And the address is:"), self._host)
        form.addRow(_("Open in:"), self._browser)
        form.addRow("", buttons)

        box = QGroupBox(_("New rule"))
        box.setLayout(form)
        return box

    def _build_table(self) -> QTableWidget:
        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(
            [_("From application"), _("For address"), _("Opens in")]
        )
        self._table.verticalHeader().hide()
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._table.itemSelectionChanged.connect(self._on_selection)
        return self._table

    def _build_actions(self) -> QHBoxLayout:
        self._exception = QPushButton(_("Add exception"))
        self._exception.setEnabled(False)
        self._exception.setToolTip(
            _("Start a narrower rule for the same application, for one address only.")
        )
        self._exception.clicked.connect(self._start_exception)

        up = QPushButton(_("Move up"))
        up.clicked.connect(lambda: self._move(-1))
        down = QPushButton(_("Move down"))
        down.clicked.connect(lambda: self._move(1))
        remove = QPushButton(_("Delete"))
        remove.clicked.connect(self._remove_selected)
        open_file = QPushButton(_("Open rules.json"))
        open_file.clicked.connect(self._open_rules_file)

        row = QHBoxLayout()
        for button in (self._exception, up, down, remove):
            row.addWidget(button)
        row.addStretch(1)
        row.addWidget(open_file)
        return row

    # --- date --------------------------------------------------------------

    def showEvent(self, event):  # noqa: N802
        self.refresh()
        super().showEvent(event)

    def refresh(self) -> None:
        default = is_default()
        self._status.setText(
            "✅ " + _("Shunt handles http and https links.")
            if default
            else "⚠️ " + _("Another program handles links.")
        )
        self._make_default.setVisible(not default)

        stored = config.load()
        for checkbox, key in (
            (self._tray, "tray_icon"),
            (self._notifications, "notifications"),
        ):
            checkbox.blockSignals(True)
            checkbox.setChecked(stored[key])
            checkbox.blockSignals(False)

        self._fill_sources()
        self._fill_browsers()
        self._fill_table()

    def _fill_sources(self) -> None:
        current = self._source.currentText()
        self._source.clear()
        self._source.addItem(_(ANY_SOURCE), "*")
        for name, app_id in browsers.installed_apps():
            self._source.addItem(name, app_id)
        self._source.setCurrentText(current or _(ANY_SOURCE))

    def _fill_browsers(self) -> None:
        current = self._browser.currentData()
        self._browser.clear()
        for browser in browsers.discover():
            self._browser.addItem(
                QIcon.fromTheme(browser.icon), browser.name, browser.desktop_id
            )
        index = self._browser.findData(current)
        if index >= 0:
            self._browser.setCurrentIndex(index)

    def _fill_table(self) -> None:
        names = {b.desktop_id: b.name for b in browsers.discover()}
        current = rules.load()
        self._table.setRowCount(len(current))
        for row, rule in enumerate(current):
            cells = [
                _(ANY_SOURCE) if rule.source == "*" else browsers.app_name(rule.source),
                _("any address") if rule.host == "*" else rule.host,
                names.get(rule.browser, _("{browser} (missing)").format(browser=rule.browser)),
            ]
            for column, text in enumerate(cells):
                self._table.setItem(row, column, QTableWidgetItem(text))

    # --- acțiuni -----------------------------------------------------------

    def _selected_row(self) -> int:
        rows = {index.row() for index in self._table.selectedIndexes()}
        return rows.pop() if len(rows) == 1 else -1

    def _on_selection(self) -> None:
        row = self._selected_row()
        self._update.setEnabled(row >= 0)
        self._exception.setEnabled(row >= 0)
        if row < 0:
            return
        rule = rules.load()[row]
        self._source.setCurrentText(
            _(ANY_SOURCE) if rule.source == "*" else browsers.app_name(rule.source)
        )
        self._host.setText("" if rule.host == "*" else rule.host)
        index = self._browser.findData(rule.browser)
        if index >= 0:
            self._browser.setCurrentIndex(index)

    def _rule_from_form(self) -> rules.Rule | None:
        browser = self._browser.currentData()
        if not browser:
            QMessageBox.warning(self, "Shunt", _("Pick a browser."))
            return None

        text = self._source.currentText().strip()
        index = self._source.findText(text)
        # Textul liber e luat ca atare: e util pentru aplicații fără .desktop.
        source = self._source.itemData(index) if index >= 0 else text
        return rules.Rule(
            source=source or "*", host=self._host.text().strip() or "*", browser=browser
        )

    def _start_exception(self) -> None:
        """Pregătește formularul pentru o regulă mai îngustă pe aceeași aplicație.

        Selecția încarcă deja regula în formular, dar nimeni n-ar ghici asta, iar
        o excepție începe oricum prin a goli adresa. Butonul face pasul vizibil.
        """
        row = self._selected_row()
        if row < 0:
            return
        rule = rules.load()[row]
        self._source.setCurrentText(
            _(ANY_SOURCE) if rule.source == "*" else browsers.app_name(rule.source)
        )
        self._host.clear()
        self._host.setFocus()

    def _add(self) -> None:
        rule = self._rule_from_form()
        if rule:
            self._commit(rules.insert(rules.load(), rule))

    def _update_selected(self) -> None:
        row = self._selected_row()
        rule = self._rule_from_form()
        if row < 0 or not rule:
            return
        current = rules.load()
        current[row] = rule
        self._commit(current, select=row)

    def _remove_selected(self) -> None:
        row = self._selected_row()
        if row < 0:
            return
        current = rules.load()
        del current[row]
        self._commit(current)

    def _move(self, delta: int) -> None:
        row = self._selected_row()
        current = rules.load()
        target = row + delta
        if row < 0 or not 0 <= target < len(current):
            return
        current[row], current[target] = current[target], current[row]
        self._commit(current, select=target)

    def _commit(self, new_rules: list[rules.Rule], select: int = -1) -> None:
        rules.save(new_rules)
        self.refresh()
        if 0 <= select < self._table.rowCount():
            self._table.selectRow(select)
        else:
            self._table.clearSelection()
        self.changed.emit()

    def _toggle_tray(self, enabled: bool) -> None:
        config.set_value("tray_icon", enabled)
        self.tray_toggled.emit(enabled)

    def _open_rules_file(self) -> None:
        path = rules.config_path()
        if not path.exists():
            rules.save([])
        subprocess.Popen(["gio", "open", str(path)], start_new_session=True)

    def _set_default(self) -> None:
        result = subprocess.run(
            ["xdg-settings", "set", "default-web-browser", APP_DESKTOP],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            QMessageBox.warning(self, "Shunt", result.stderr.strip() or _("It failed."))
        self.refresh()


APP_ID = "co.dumitres.Shunt"

ICON_SIZES = (16, 22, 24, 32, 48, 64, 128)


def _icon_dirs() -> list[Path]:
    home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    system = os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":")
    return [
        base / "icons/hicolor/scalable/apps"
        for base in [home, *(Path(d) for d in system if d)]
    ]


def _icon_file(name: str) -> Path | None:
    for directory in _icon_dirs():
        path = directory / f"{name}.svg"
        if path.is_file():
            return path
    return None


def _render(name: str, color: QColor) -> QIcon | None:
    """Desenează iconița cu o culoare dată, la toate mărimile.

    Plasma recolorează singură iconițele pe care le încarcă după nume, dar Qt
    nu, deci ferestrele noastre ar rămâne cu culorile din fișier. Așa că
    substituim currentColor și desenăm noi.
    """
    path = _icon_file(name)
    if path is None:
        return None
    try:
        source = path.read_text(encoding="utf-8")
    except OSError:
        return None

    source = source.replace('fill="currentColor"', f'fill="{color.name()}"')
    source = source.replace('stroke="currentColor"', f'stroke="{color.name()}"')
    renderer = QSvgRenderer(QByteArray(source.encode("utf-8")))
    if not renderer.isValid():
        return None

    icon = QIcon()
    for size in ICON_SIZES:
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        icon.addPixmap(pixmap)
    return icon


def app_icon() -> QIcon:
    """Placa urmează culoarea de accent, luată din paleta schemei de culori."""
    accent = QApplication.palette().highlight().color()
    return _render(APP_ID, accent) or QIcon.fromTheme(
        APP_ID, QIcon.fromTheme("internet-web-browser")
    )


def tray_icon() -> QIcon:
    """Doar deschis/închis, după panou. Cerută întâi după nume, ca s-o
    recoloreze Plasma; desenul nostru e doar plasa de siguranță."""
    from_theme = QIcon.fromTheme(f"{APP_ID}-symbolic")
    if not from_theme.isNull():
        return from_theme
    text = QApplication.palette().windowText().color()
    return _render(f"{APP_ID}-symbolic", text) or app_icon()
