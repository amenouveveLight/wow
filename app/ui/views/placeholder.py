"""Page provisoire pour les écrans pas encore construits."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.ui import icons
from app.ui.navigation import NavEntry
from app.ui.theme.tokens import Color, Layout
from app.ui.widgets.base import make_label
from app.ui.widgets.card import Card
from app.ui.widgets.page_header import PageHeader


class PlaceholderPage(QWidget):
    def __init__(self, entry: NavEntry, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Page")
        corps = QVBoxLayout(self)
        corps.setContentsMargins(*Layout.PAGE_MARGINS)
        corps.setSpacing(Layout.SECTION_GAP)
        corps.addWidget(PageHeader(entry.label, "Écran en construction"))
        carte = Card()
        ligne = QHBoxLayout()
        ligne.setSpacing(16)
        icone = QLabel()
        icone.setObjectName("PlaceholderIcon")
        icone.setFixedSize(48, 48)
        icone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icone.setPixmap(icons.icon(entry.icon, Color.NAVY_700, 22).pixmap(22, 22))
        ligne.addWidget(icone)
        ligne.addWidget(make_label("Cet écran sera construit à l’une des prochaines étapes de l’interface.",
                                   "card-title", wrap=True), 1)
        carte.body.addLayout(ligne)
        corps.addWidget(carte)
        corps.addStretch(1)