"""Thème de l'application : tokens, feuille de style, polices, ombres."""
from __future__ import annotations

from PySide6.QtWidgets import QApplication

from app.ui.theme import tokens
from app.ui.theme.effects import apply_shadow
from app.ui.theme.fonts import configure_fonts
from app.ui.theme.stylesheet import build as build_stylesheet


def apply_theme(app: QApplication) -> None:
    """Style Fusion (rendu identique d'un poste à l'autre), polices, puis QSS."""
    app.setStyle("Fusion")
    configure_fonts(app)
    app.setStyleSheet(build_stylesheet())


__all__ = ["apply_shadow", "apply_theme", "build_stylesheet", "tokens"]