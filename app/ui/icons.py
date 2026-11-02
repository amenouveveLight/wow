"""Chargement des icônes SVG, teintées à la demande et nettes sur écran HiDPI."""
from __future__ import annotations

from functools import lru_cache

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from app.ui.paths import ICONS_DIR
from app.ui.theme.tokens import Color


@lru_cache(maxsize=1024)
def icon(name: str, color: str = Color.NAVY_900, size: int = 18) -> QIcon:
    """Icône `name` (fichier assets/icons/<name>.svg) dans la couleur donnée.

    À appeler après la création de QApplication. Trois résolutions (×1, ×2, ×3) sont
    fournies : Qt choisit la bonne selon le facteur d'échelle de l'écran.
    """
    chemin = ICONS_DIR / f"{name}.svg"
    if not chemin.exists():
        raise FileNotFoundError(f"Icône introuvable : {name}. Lancez : python scripts\\generate_icons.py")
    svg = chemin.read_text(encoding="utf-8").replace("currentColor", color)
    moteur = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    resultat = QIcon()
    for echelle in (1, 2, 3):
        image = QPixmap(size * echelle, size * echelle)
        image.fill(Qt.GlobalColor.transparent)
        peintre = QPainter(image)
        peintre.setRenderHint(QPainter.RenderHint.Antialiasing)
        moteur.render(peintre)
        peintre.end()
        image.setDevicePixelRatio(echelle)
        resultat.addPixmap(image)
    return resultat