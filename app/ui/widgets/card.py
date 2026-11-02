"""Cartes : conteneur générique, carte statistique, séparateur."""
from __future__ import annotations

from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget

from app.ui.theme import apply_shadow
from app.ui.theme.tokens import Layout, Shadow
from app.ui.widgets.base import make_label, set_property


class Card(QFrame):
    """Carte blanche à bordure et ombre légère. Le contenu s'ajoute à `body`."""

    def __init__(self, parent: QWidget | None = None, *, shadow: bool = True,
                 padding: int = Layout.CARD_PADDING, spacing: int = Layout.CARD_GAP) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(padding, padding, padding, padding)
        self.body.setSpacing(spacing)
        if shadow:
            apply_shadow(self, Shadow.CARD)


class StatCard(Card):
    """Carte de chiffre clé : libellé, montant, précision. `tone` : neutre, vert ou rouge."""

    def __init__(self, label: str = "", amount: str = "", note: str = "", tone: str = "neutre",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent, padding=18, spacing=6)
        self.label_label = make_label(label, "stat-label")
        self.amount_label = make_label(amount, "stat-amount")
        self.note_label = make_label(note, "stat-note", wrap=True)
        for etiquette in (self.label_label, self.amount_label, self.note_label):
            self.body.addWidget(etiquette)
        self.tone = tone
        self.set_tone(tone)

    def set_content(self, label: str, amount: str, note: str = "", tone: str = "neutre") -> None:
        self.label_label.setText(label)
        self.amount_label.setText(amount)
        self.note_label.setText(note)
        self.note_label.setVisible(bool(note))
        self.set_tone(tone)

    def set_tone(self, tone: str) -> None:
        if tone not in ("neutre", "vert", "rouge"):
            raise ValueError(f"Ton inconnu : {tone}")
        self.tone = tone
        set_property(self.amount_label, "tone", tone)
        set_property(self.note_label, "tone", tone)


class Separator(QFrame):
    """Trait horizontal de 1 px."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Separator")
        self.setFixedHeight(1)