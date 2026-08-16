"""Fereastra de selecție a browserului."""

from __future__ import annotations

from PySide6.QtCore import Qt, QEvent, QSize, Signal
from PySide6.QtGui import QFontMetrics, QIcon, QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .browsers import Browser
from .i18n import _

ICON_SIZE = 48
MAX_URL_WIDTH = 460

# Titlul nu se vede (fereastra e fără ramă), dar scriptul KWin deosebește
# selectorul de fereastra de setări exact după el — deci rămâne netradus.
WINDOW_TITLE = "Shunt Chooser"


class Chooser(QWidget):
    """Emite (browser, remember) la alegere; se închide singură după."""

    chosen = Signal(object, bool)

    def __init__(self, browsers: list[Browser], url: str, source_name: str = ""):
        super().__init__(None, Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle(WINDOW_TITLE)

        self._browsers = browsers
        self._url = url
        self._buttons: list[QToolButton] = []

        panel = QWidget(self)
        panel.setObjectName("panel")
        panel.setStyleSheet(
            "#panel { background: palette(window); border-radius: 10px;"
            " border: 1px solid palette(mid); }"
        )

        row = QHBoxLayout()
        row.setSpacing(4)
        for index, browser in enumerate(browsers):
            button = self._make_button(browser, index)
            self._buttons.append(button)
            row.addWidget(button)

        self._url_label = QLabel(self._elide(url))
        self._url_label.setToolTip(url)
        self._url_label.setStyleSheet("color: palette(placeholder-text);")

        self._remember = QCheckBox(
            _("Remember for {app}").format(app=source_name)
            if source_name
            else _("Remember")
        )
        self._remember.setEnabled(bool(source_name))
        if not source_name:
            self._remember.setToolTip(_("Could not identify the source application."))

        inner = QVBoxLayout(panel)
        inner.setContentsMargins(12, 12, 12, 10)
        inner.setSpacing(8)
        inner.addLayout(row)
        inner.addWidget(self._url_label)
        inner.addWidget(self._remember)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(panel)

        if self._buttons:
            self._buttons[0].setFocus()

    def _make_button(self, browser: Browser, index: int) -> QToolButton:
        button = QToolButton(self)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        button.setIcon(QIcon.fromTheme(browser.icon, QIcon.fromTheme("web-browser")))
        button.setIconSize(QSize(ICON_SIZE, ICON_SIZE))
        button.setText(browser.name)
        button.setAutoRaise(True)
        button.setMinimumWidth(96)
        if index < 9:
            button.setShortcut(str(index + 1))
            button.setToolTip(
                _("{name}  ({key})").format(name=browser.name, key=index + 1)
            )
        button.clicked.connect(lambda _checked=False, b=browser: self._pick(b))
        return button

    def _elide(self, url: str) -> str:
        return QFontMetrics(self.font()).elidedText(
            url, Qt.TextElideMode.ElideMiddle, MAX_URL_WIDTH
        )

    def _pick(self, browser: Browser) -> None:
        shift = QApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier
        remember = self._remember.isChecked() or (
            bool(shift) and self._remember.isEnabled()
        )
        self.chosen.emit(browser, remember)
        self.close()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # QToolButton nu reacționează singur la Enter, doar la Space.
            focused = self.focusWidget()
            if isinstance(focused, QToolButton):
                focused.click()
        elif event.key() == Qt.Key.Key_C and (
            event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            QApplication.clipboard().setText(self._url)
            self.close()
        else:
            super().keyPressEvent(event)

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.WindowDeactivate:
            self.close()
        return super().event(event)
