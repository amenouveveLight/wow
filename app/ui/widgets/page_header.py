"""En-tête de page : titre, sous-titre, boutons d'action à droite."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from app.ui.widgets.base import make_label


class PageHeader(QWidget):
    def __init__(self, title: str, subtitle: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        textes = QVBoxLayout()
        textes.setSpacing(4)
        self._title = make_label(title, "page-title")
        self._subtitle = make_label(subtitle, "page-subtitle")
        textes.addWidget(self._title)
        textes.addWidget(self._subtitle)
        layout.addLayout(textes)
        layout.addStretch(1)
        self._actions = QHBoxLayout()
        self._actions.setSpacing(12)
        layout.addLayout(self._actions)
        layout.setAlignment(self._actions, Qt.AlignmentFlag.AlignVCenter)

    def set_title(self, text: str) -> None:
        self._title.setText(text)

    def set_subtitle(self, text: str) -> None:
        self._subtitle.setText(text)
        self._subtitle.setVisible(bool(text))

    def add_action(self, widget: QWidget) -> None:
        self._actions.addWidget(widget)

    def action_count(self) -> int:
        return self._actions.count()