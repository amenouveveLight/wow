"""Graphiques légers dessinés à la main : histogramme mensuel et barre de proportion."""
from __future__ import annotations

from typing import Sequence

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QSizePolicy, QWidget

from app.ui.theme.tokens import Color, Font, FontSize


class MonthlyChart(QWidget):
    """Deux barres par mois : entrées (vert) et dépenses (marine)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._months: list[tuple[str, int, int]] = []
        self.setMinimumHeight(220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_months(self, months: Sequence[tuple[str, int, int]]) -> None:
        """months : suite de (libellé, entrées, dépenses)."""
        self._months = list(months)
        self.update()

    def month_count(self) -> int:
        return len(self._months)

    def paintEvent(self, _event) -> None:  # noqa: N802 (nom Qt)
        peintre = QPainter(self)
        peintre.setRenderHint(QPainter.RenderHint.Antialiasing)
        police = QFont(Font.FAMILY)
        police.setPixelSize(FontSize.SMALL)
        peintre.setFont(police)
        if not self._months:
            peintre.setPen(QColor(Color.GRAY_500))
            peintre.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Aucune donnée")
            peintre.end()
            return
        marge_haut, hauteur_libelle = 4, 24
        hauteur = max(1, self.height() - hauteur_libelle - marge_haut)
        case = self.width() / len(self._months)
        largeur_barre = min(case * 0.28, 22.0)
        maximum = max(max(e, d) for _, e, d in self._months) or 1
        for index, (libelle, entrees, depenses) in enumerate(self._months):
            centre = index * case + case / 2
            for valeur, couleur, decalage in ((entrees, Color.SUCCESS_600, -largeur_barre - 1),
                                              (depenses, Color.NAVY_900, 1)):
                h = hauteur * valeur / maximum
                peintre.setPen(Qt.PenStyle.NoPen)
                peintre.setBrush(QColor(couleur))
                peintre.drawRoundedRect(QRectF(centre + decalage, marge_haut + hauteur - h, largeur_barre, h), 2, 2)
            peintre.setPen(QColor(Color.GRAY_500))
            peintre.drawText(QRectF(index * case, marge_haut + hauteur + 6, case, hauteur_libelle - 6),
                             Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, libelle)
        peintre.end()


class RatioBar(QWidget):
    """Barre de proportion (0 à 1) sur un rail gris."""

    def __init__(self, ratio: float = 0.0, color: str = Color.NAVY_900,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._ratio = ratio
        self._color = color
        self.setFixedHeight(8)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_value(self, ratio: float, color: str) -> None:
        self._ratio, self._color = ratio, color
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        peintre = QPainter(self)
        peintre.setRenderHint(QPainter.RenderHint.Antialiasing)
        peintre.setPen(Qt.PenStyle.NoPen)
        peintre.setBrush(QColor(Color.GRAY_100))
        peintre.drawRoundedRect(QRectF(self.rect()), 4, 4)
        if self._ratio > 0:
            largeur = max(6.0, self.width() * min(self._ratio, 1.0))
            peintre.setBrush(QColor(self._color))
            peintre.drawRoundedRect(QRectF(0, 0, largeur, self.height()), 4, 4)
        peintre.end()