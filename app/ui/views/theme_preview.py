"""Aperçu du thème : couleurs, typographie, boutons, champs, badges, tableau.
Vue temporaire de validation visuelle, à comparer à la page « Système de design » de Figma."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QPushButton, QScrollArea, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from app.config import APP_NAME
from app.ui.theme import apply_shadow, tokens
from app.ui.theme.tokens import Color, Layout, Radius, Shadow


def _label(texte: str, role: str | None = None, **proprietes: str) -> QLabel:
    etiquette = QLabel(texte)
    if role:
        etiquette.setProperty("role", role)
    for cle, valeur in proprietes.items():
        etiquette.setProperty(cle, valeur)
    return etiquette


def _bouton(texte: str, variante: str | None = None, actif: bool = True) -> QPushButton:
    bouton = QPushButton(texte)
    if variante:
        bouton.setProperty("variant", variante)
    bouton.setEnabled(actif)
    return bouton


def _badge(texte: str, genre: str) -> QLabel:
    badge = QLabel(texte)
    badge.setObjectName("Badge")
    badge.setProperty("kind", genre)
    badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return badge


def _carte() -> tuple[QFrame, QVBoxLayout]:
    carte = QFrame()
    carte.setObjectName("Card")
    apply_shadow(carte, Shadow.CARD)
    disposition = QVBoxLayout(carte)
    disposition.setContentsMargins(*(Layout.CARD_PADDING,) * 4)
    disposition.setSpacing(Layout.CARD_GAP)
    return carte, disposition


class ThemePreview(QMainWindow):
    """Fenêtre d'aperçu du thème."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} : aperçu du thème")
        self.setMinimumSize(*Layout.MIN_WINDOW)
        self.resize(1180, 860)

        page = QWidget()
        page.setObjectName("Page")
        racine = QVBoxLayout(page)
        racine.setContentsMargins(*Layout.PAGE_MARGINS)
        racine.setSpacing(Layout.SECTION_GAP)
        racine.addWidget(_label("Aperçu du thème", "page-title"))
        racine.addWidget(_label("À comparer avec la page « Système de design » du fichier Figma", "page-subtitle"))
        for section in (self._couleurs(), self._typographie(), self._boutons(), self._champs(),
                        self._badges(), self._tableau()):
            racine.addWidget(section)
        racine.addStretch(1)

        defilement = QScrollArea()
        defilement.setWidgetResizable(True)
        defilement.setFrameShape(QFrame.Shape.NoFrame)
        defilement.setWidget(page)
        self.setCentralWidget(defilement)

    def _couleurs(self) -> QFrame:
        carte, corps = _carte()
        corps.addWidget(_label("Couleurs", "card-title"))
        grille = QGridLayout()
        grille.setSpacing(Layout.CARD_GAP)
        for index, (nom, valeur) in enumerate(tokens.color_items()):
            echantillon = QFrame()
            echantillon.setFixedSize(150, 48)
            echantillon.setStyleSheet(
                f"background: {valeur}; border: 1px solid {Color.BORDER}; border-radius: {Radius.CONTROL}px;")
            cellule = QVBoxLayout()
            cellule.setSpacing(4)
            cellule.addWidget(echantillon)
            cellule.addWidget(_label(f"{nom.lower()}  {valeur}", "caption"))
            grille.addLayout(cellule, index // 5, index % 5)
        corps.addLayout(grille)
        return carte

    def _typographie(self) -> QFrame:
        carte, corps = _carte()
        corps.addWidget(_label("Typographie", "card-title"))
        for texte, role in (("Titre de page : 24 / Bold", "page-title"),
                            ("Montant de carte : 4 140 000 FCFA", "stat-amount"),
                            ("Titre de modale : 18 / Bold", "modal-title"),
                            ("Titre de carte : 16 / Semi Bold", "card-title"),
                            ("Corps de texte : 14 / Regular", None),
                            ("Légende : 12 / Regular", "caption")):
            corps.addWidget(_label(texte, role))
        return carte

    def _boutons(self) -> QFrame:
        carte, corps = _carte()
        corps.addWidget(_label("Boutons : repos, survol (passez la souris), appuyé, désactivé", "card-title"))
        ligne = QHBoxLayout()
        ligne.setSpacing(Layout.CARD_GAP)
        for texte, variante, actif in (("Enregistrer", "primary", True), ("Annuler", None, True),
                                       ("Supprimer", "danger", True), ("Enregistrer", "primary", False),
                                       ("Annuler", None, False), ("Voir le détail", "link", True)):
            ligne.addWidget(_bouton(texte, variante, actif))
        ligne.addStretch(1)
        corps.addLayout(ligne)
        return carte

    def _champs(self) -> QFrame:
        carte, corps = _carte()
        corps.addWidget(_label("Champs de formulaire", "card-title"))
        ligne = QHBoxLayout()
        ligne.setSpacing(Layout.CARD_GAP)
        normal = QLineEdit()
        normal.setPlaceholderText("Nom complet")
        erreur = QLineEdit("-5")
        erreur.setProperty("error", True)
        lecture = QLineEdit("043")
        lecture.setReadOnly(True)
        desactive = QLineEdit("Désactivé")
        desactive.setEnabled(False)
        liste = QComboBox()
        liste.addItems(["Tous les statuts", "Actifs", "Décédés"])
        for champ in (normal, erreur, lecture, desactive, liste):
            ligne.addWidget(champ)
        corps.addLayout(ligne)
        corps.addWidget(_label("Le montant doit être un entier positif.", "field-error"))
        return carte

    def _badges(self) -> QFrame:
        carte, corps = _carte()
        corps.addWidget(_label("Badges et situations (jamais de signe moins)", "card-title"))
        ligne = QHBoxLayout()
        ligne.setSpacing(Layout.SECTION_GAP)
        for texte, genre in (("Payé", "success"), ("Dette", "danger"), ("En attente", "warning"),
                             ("Décédé", "neutral"), ("Actif", "info")):
            ligne.addWidget(_badge(texte, genre))
        for texte, ton in (("Excédent : 122 000 FCFA", "vert"), ("Dette : 378 000 FCFA", "rouge"),
                           ("Soldé : 0 FCFA", "neutre")):
            ligne.addWidget(_label(texte, "situation", tone=ton))
        ligne.addStretch(1)
        corps.addLayout(ligne)
        return carte

    def _tableau(self) -> QFrame:
        carte, corps = _carte()
        corps.addWidget(_label("Tableau", "card-title"))
        lignes = [("001", "Komlan Akakpo", "Actif", "216 000", "—"),
                  ("006", "Efua Dosseh", "Actif", "168 000", "18 000"),
                  ("005", "Kossi Ayité", "Décédé", "126 000", "—"),
                  ("009", "Yawo Agbodjan", "Actif", "216 000", "85 000")]
        tableau = QTableWidget(len(lignes), 5)
        tableau.setHorizontalHeaderLabels(["N° CARNET", "NOM COMPLET", "STATUT", "DÛ (FCFA)", "DETTE (FCFA)"])
        tableau.verticalHeader().setVisible(False)
        tableau.verticalHeader().setDefaultSectionSize(Layout.TABLE_ROW_HEIGHT)
        tableau.horizontalHeader().setStretchLastSection(True)
        tableau.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        tableau.setShowGrid(False)
        tableau.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tableau.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tableau.setMinimumHeight(Layout.TABLE_HEADER_HEIGHT + Layout.TABLE_ROW_HEIGHT * len(lignes) + 4)
        for r, valeurs in enumerate(lignes):
            for c, texte in enumerate(valeurs):
                element = QTableWidgetItem(texte)
                if c >= 3:
                    element.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if c == 4 and texte != "—":
                    element.setForeground(self._rouge())
                tableau.setItem(r, c, element)
        corps.addWidget(tableau)
        return carte

    @staticmethod
    def _rouge():
        from PySide6.QtGui import QColor
        return QColor(Color.DANGER_600)