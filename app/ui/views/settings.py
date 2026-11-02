"""Page Paramètres."""
from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.ui.theme.tokens import Layout
from app.ui.widgets.page_header import PageHeader


class SettingsView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Page")
        corps = QVBoxLayout(self)
        corps.setContentsMargins(*Layout.PAGE_MARGINS)
        corps.setSpacing(Layout.SECTION_GAP)

        self.header = PageHeader("Paramètres", "")
        corps.addWidget(self.header)
        corps.addWidget(QLabel("Fonctionnalité à implémenter"))
        corps.addStretch(1)

    def set_model(self, model) -> None:
        self.header.set_subtitle("Configuration générale")
