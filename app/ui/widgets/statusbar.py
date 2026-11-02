"""Barre d'état : base de données locale, exercice actif, dernière sauvegarde."""
from __future__ import annotations

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from app.ui.theme.tokens import Layout
from app.ui.widgets.base import set_property


class AppStatusBar(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("StatusBar")
        self.setFixedHeight(Layout.STATUSBAR_HEIGHT)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(20)
        self._dot = QLabel()
        self._dot.setObjectName("StatusDot")
        self._database = QLabel("")
        self._exercise = QLabel("")
        self._backup = QLabel("")
        self._notice = QLabel("")
        self._notice.setObjectName("StatusNotice")
        self._notice.hide()
        layout.addWidget(self._dot)
        for etiquette in (self._database, self._exercise, self._backup):
            layout.addWidget(etiquette)
        layout.addStretch(1)
        layout.addWidget(self._notice)

    def set_database(self, ok: bool, text: str) -> None:
        set_property(self._dot, "state", "ok" if ok else "error")
        self._database.setText(text)

    def set_exercise(self, text: str) -> None:
        self._exercise.setText(text)

    def set_last_backup(self, text: str) -> None:
        self._backup.setText(text)

    def set_notice(self, text: str | None) -> None:
        """Mention à droite (ex. « Données fictives de démonstration »), masquée si vide."""
        self._notice.setText(text or "")
        self._notice.setVisible(bool(text))