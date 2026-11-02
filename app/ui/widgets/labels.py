"""Étiquette de situation : excédent (vert), dette (rouge), soldé (neutre), sans signe moins."""
from __future__ import annotations

from PySide6.QtWidgets import QLabel, QWidget

from app.services.affichage import Situation
from app.ui.widgets.base import set_property


class SituationLabel(QLabel):
    """Affiche une `Situation` de la couche métier (« Dette : 378 000 FCFA » en rouge)."""

    def __init__(self, situation: Situation | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("role", "situation")
        if situation is not None:
            self.set_situation(situation)

    def set_situation(self, situation: Situation) -> None:
        self.setText(situation.texte())
        set_property(self, "tone", situation.couleur)