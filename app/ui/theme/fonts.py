"""Chargement des polices (Inter si présente dans assets/fonts, sinon Segoe UI)."""
from __future__ import annotations

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

from app.ui.paths import FONTS_DIR
from app.ui.theme.tokens import Font, FontSize


def load_fonts() -> list[str]:
    """Enregistre les .ttf / .otf du dossier assets/fonts et retourne les familles chargées."""
    familles: list[str] = []
    for fichier in sorted(FONTS_DIR.glob("*.[ot]tf")):
        identifiant = QFontDatabase.addApplicationFont(str(fichier))
        if identifiant != -1:
            familles.extend(QFontDatabase.applicationFontFamilies(identifiant))
    return sorted(set(familles))


def configure_fonts(app: QApplication) -> None:
    """Police par défaut de l'application, en pixels pour une échelle HiDPI cohérente."""
    load_fonts()
    police = QFont()
    police.setFamilies([Font.FAMILY, *Font.FALLBACKS])
    police.setPixelSize(FontSize.BODY)
    app.setFont(police)