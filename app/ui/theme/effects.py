"""Ombres : le QSS n'a pas de box-shadow, on utilise QGraphicsDropShadowEffect."""
from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget

from app.ui.theme.tokens import ShadowSpec


def apply_shadow(widget: QWidget, spec: ShadowSpec) -> None:
    """À réserver aux cartes, popovers et modales : un effet rend le widget dans un tampon,
    donc à éviter sur de grands tableaux défilants."""
    effet = QGraphicsDropShadowEffect(widget)
    effet.setBlurRadius(spec.blur)
    effet.setOffset(spec.dx, spec.dy)
    effet.setColor(QColor(*spec.rgba))
    widget.setGraphicsEffect(effet)