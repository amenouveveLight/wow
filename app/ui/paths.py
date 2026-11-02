"""Chemins des ressources de l'interface."""
from __future__ import annotations

from pathlib import Path

UI_DIR = Path(__file__).resolve().parent
ASSETS_DIR = UI_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
FONTS_DIR = ASSETS_DIR / "fonts"
THEME_DIR = UI_DIR / "theme"
# Feuilles de style (modèles), dans l'ordre d'application : composants, puis écrans
QSS_FILES = (THEME_DIR / "styles.qss", THEME_DIR / "screens.qss")
QSS_PATH = QSS_FILES[0]