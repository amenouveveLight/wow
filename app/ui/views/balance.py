"""Page Bilan financier."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.ui.presenters.balance_model import BalanceViewModel
from app.ui.theme.tokens import Color, Layout
from app.ui.widgets.base import make_label
from app.ui.widgets.button import AppButton, Variant
from app.ui.widgets.card import Card, StatCard
from app.ui.widgets.page_header import PageHeader


class BalanceView(QWidget):
    close_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Page")
        corps = QVBoxLayout(self)
        corps.setContentsMargins(*Layout.PAGE_MARGINS)
        corps.setSpacing(Layout.SECTION_GAP)

        self.header = PageHeader("Bilan financier", "")
        self.close_button = AppButton("Clôturer l'exercice", Variant.PRIMARY, "check")
        self.header.add_action(self.close_button)
        corps.addWidget(self.header)

        corps.addWidget(self._carte_periode())
        corps.addWidget(self._carte_chiffres())
        corps.addStretch(1)

        self.close_button.clicked.connect(lambda: self.close_requested.emit())

    def _carte_periode(self) -> Card:
        carte = Card()
        ligne = QHBoxLayout()
        ligne.setSpacing(20)
        self.period_start_label = make_label("", "caption")
        self.period_end_label = make_label("", "caption")
        ligne.addWidget(make_label("Période :", "card-title"))
        ligne.addWidget(self.period_start_label)
        ligne.addWidget(make_label("→", "caption"))
        ligne.addWidget(self.period_end_label)
        ligne.addStretch(1)
        carte.body.addLayout(ligne)
        return carte

    def _carte_chiffres(self) -> Card:
        carte = Card()
        grille = QHBoxLayout()
        grille.setSpacing(Layout.CARD_GAP)
        self.revenue_card = StatCard()
        self.expenses_card = StatCard()
        self.balance_card = StatCard()
        self.carried_card = StatCard()
        self.closing_card = StatCard()
        grille.addWidget(self.revenue_card, 1)
        grille.addWidget(self.expenses_card, 1)
        grille.addWidget(self.balance_card, 1)
        grille.addWidget(self.carried_card, 1)
        grille.addWidget(self.closing_card, 1)
        carte.body.addLayout(grille)
        return carte

    def set_model(self, model: BalanceViewModel) -> None:
        self.header.set_subtitle(model.subtitle)
        self.period_start_label.setText(model.period_start)
        self.period_end_label.setText(model.period_end)
        self.revenue_card.set_content("Total des recettes", model.total_revenue, "", "vert")
        self.expenses_card.set_content("Total des dépenses", model.total_expenses, "", "neutre")
        self.balance_card.set_content("Solde de l'exercice", model.balance, "", "neutre")
        self.carried_card.set_content("Report de l'exercice précédent", model.carried_forward, "", "neutre")
        tone = "vert" if model.is_positive else "rouge"
        self.closing_card.set_content("Solde de clôture", model.closing_balance, "", tone)
