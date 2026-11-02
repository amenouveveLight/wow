"""Page Cotisations mensuelles : tableau des membres avec leurs 12 mois de cotisation."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (QComboBox, QGridLayout, QHBoxLayout, QLabel, QLayout, QLineEdit,
                               QVBoxLayout, QWidget)

from app.ui.presenters.monthly_model import MonthlyMemberRow, MonthlyViewModel
from app.ui.theme.tokens import Color, Layout
from app.ui.widgets.badge import Badge
from app.ui.widgets.base import ClickableFrame, make_label
from app.ui.widgets.button import AppButton, Variant
from app.ui.widgets.card import Card, Separator
from app.ui.widgets.page_header import PageHeader

_MONTHS = ("Sep", "Oct", "Nov", "Déc", "Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août")
_COLONNES_BASE = (
    ("carnet", "N° CARNET", 2, False),
    ("name", "NOM COMPLET", 4, False),
    ("sex", "SEXE", 1, False),
    ("joined", "ADHÉSION", 2, False),
)
_PAD = 16


def _clear_layout(layout: QLayout) -> None:
    while layout.count():
        element = layout.takeAt(0)
        widget = element.widget()
        if widget is not None:
            widget.hide()
            widget.setParent(None)
            widget.deleteLater()
        elif element.layout() is not None:
            _clear_layout(element.layout())
            element.layout().deleteLater()


def _marges(colonne: int) -> tuple[int, int]:
    gauche = _PAD if colonne == 0 else 8
    droite = _PAD if colonne == len(_MONTHS) + len(_COLONNES_BASE) + 4 else 8
    return gauche, droite


class MonthlyView(QWidget):
    search_changed = Signal(str)
    sex_changed = Signal(str)
    sort_requested = Signal(str)
    page_requested = Signal(int)
    record_payment_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Page")
        corps = QVBoxLayout(self)
        corps.setContentsMargins(*Layout.PAGE_MARGINS)
        corps.setSpacing(Layout.SECTION_GAP)

        self.header = PageHeader("Cotisations mensuelles", "")
        corps.addWidget(self.header)

        corps.addWidget(self._carte_tarifs())
        corps.addWidget(self._carte_filtres())
        corps.addWidget(self._carte_tableau())
        corps.addStretch(1)

        self._row_count = 0
        self.search.textChanged.connect(self.search_changed.emit)
        self.sex_combo.currentIndexChanged.connect(
            lambda _i: self.sex_changed.emit(str(self.sex_combo.currentData())))
        self._find = QShortcut(QKeySequence(QKeySequence.StandardKey.Find), self)
        self._find.activated.connect(self.focus_search)

    def _carte_tarifs(self) -> Card:
        carte = Card(padding=14, spacing=0)
        ligne = QHBoxLayout()
        ligne.setSpacing(12)
        self.tariff_man_label = make_label("", "caption")
        self.tariff_woman_label = make_label("", "caption")
        ligne.addWidget(make_label("Tarifs mensuels :", "card-title"))
        ligne.addWidget(self.tariff_man_label)
        ligne.addWidget(make_label("Homme", "caption"))
        ligne.addWidget(self.tariff_woman_label)
        ligne.addWidget(make_label("Femme", "caption"))
        ligne.addStretch(1)
        carte.body.addLayout(ligne)
        return carte

    def _carte_filtres(self) -> Card:
        carte = Card(padding=14, spacing=0)
        ligne = QHBoxLayout()
        ligne.setSpacing(12)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher par nom ou n° de carnet…")
        self.search.setClearButtonEnabled(True)
        self.search.setFixedHeight(Layout.INPUT_HEIGHT)
        self.search.setMinimumWidth(320)
        ligne.addWidget(self.search, 3)
        self.sex_combo = self._liste((("Sexe : Tous", "all"), ("Sexe : Masculin", "M"),
                                      ("Sexe : Féminin", "F")))
        ligne.addWidget(self.sex_combo)
        ligne.addStretch(2)
        ligne.addWidget(make_label("Ctrl + F pour rechercher · clic sur un en-tête pour trier", "caption"))
        carte.body.addLayout(ligne)
        return carte

    @staticmethod
    def _liste(options: tuple[tuple[str, str], ...]) -> QComboBox:
        liste = QComboBox()
        for texte, cle in options:
            liste.addItem(texte, cle)
        liste.setFixedHeight(Layout.INPUT_HEIGHT)
        liste.setMinimumWidth(150)
        return liste

    def _carte_tableau(self) -> Card:
        carte = Card(padding=0, spacing=0)
        self._grid = QGridLayout()
        self._grid.setSpacing(0)
        total_cols = len(_COLONNES_BASE) + len(_MONTHS) + 4
        for colonne in range(total_cols):
            self._grid.setColumnStretch(colonne, 1)
        carte.body.addLayout(self._grid)
        carte.body.addWidget(Separator())
        pied = QHBoxLayout()
        pied.setContentsMargins(_PAD, 12, _PAD, 12)
        self.counter = make_label("", "caption")
        pied.addWidget(self.counter)
        pied.addStretch(1)
        self._pager = QHBoxLayout()
        self._pager.setSpacing(6)
        pied.addLayout(self._pager)
        carte.body.addLayout(pied)
        return carte

    def row_count(self) -> int:
        return self._row_count

    def focus_search(self) -> None:
        self.search.setFocus()
        self.search.selectAll()

    def set_model(self, model: MonthlyViewModel) -> None:
        self.header.set_subtitle(model.subtitle)
        self.tariff_man_label.setText(model.tariff_man)
        self.tariff_woman_label.setText(model.tariff_woman)
        self._fill_table(model)
        self.counter.setText(model.counter)
        self._fill_pager(model)

    def _fill_table(self, model: MonthlyViewModel) -> None:
        _clear_layout(self._grid)
        colonne = 0
        for cle, titre, poids, droite in _COLONNES_BASE:
            fleche = (" ▲" if model.rows and model.rows[0] else "") if cle == "carnet" else ""
            self._grid.addWidget(self._entete(cle, titre + fleche, colonne, droite), 0, colonne)
            colonne += 1
        for mois in _MONTHS:
            self._grid.addWidget(self._entete(f"month_{mois}", mois, colonne, False), 0, colonne)
            colonne += 1
        for titre in ("DÛ", "REÇU", "DETTE", "AVANCE"):
            self._grid.addWidget(self._entete(titre.lower(), titre, colonne, True), 0, colonne)
            colonne += 1
        self._grid.addWidget(self._entete("", "", colonne, False, cliquable=False), 0, colonne)

        ligne = 1
        for membre in model.rows:
            self._grid.addWidget(Separator(), ligne, 0, 1, colonne + 1)
            ligne += 1
            self._remplir_ligne(membre, ligne)
            ligne += 1
        if model.empty:
            vide = make_label("Aucun membre ne correspond à votre recherche.", "caption")
            vide.setContentsMargins(_PAD, 20, _PAD, 20)
            self._grid.addWidget(vide, ligne, 0, 1, colonne + 1)
        self._row_count = len(model.rows)

    def _entete(self, cle: str, texte: str, colonne: int, droite: bool, *, cliquable: bool = True) -> QWidget:
        cadre = ClickableFrame()
        cadre.setObjectName("ColHead")
        cadre.setStyleSheet(f"#ColHead {{ background: {Color.GRAY_100}; }}")
        cadre.setMinimumHeight(Layout.TABLE_HEADER_HEIGHT)
        disposition = QHBoxLayout(cadre)
        gauche, droit = _marges(colonne)
        disposition.setContentsMargins(gauche, 0, droit, 0)
        etiquette = make_label(texte, "grid-head")
        alignement = Qt.AlignmentFlag.AlignRight if droite else Qt.AlignmentFlag.AlignLeft
        etiquette.setAlignment(alignement | Qt.AlignmentFlag.AlignVCenter)
        disposition.addWidget(etiquette)
        if cliquable:
            cadre.clicked.connect(lambda k=cle: self.sort_requested.emit(k))
        else:
            cadre.setCursor(Qt.CursorShape.ArrowCursor)
            cadre.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        return cadre

    @staticmethod
    def _cellule(texte: str, role: str, colonne: int, droite: bool = False,
                 couleur: str | None = None, centre: bool = False) -> QLabel:
        etiquette = make_label(texte, role)
        etiquette.setMinimumHeight(Layout.TABLE_ROW_HEIGHT + 6)
        gauche, droit = _marges(colonne)
        etiquette.setContentsMargins(gauche, 0, droit, 0)
        if centre:
            etiquette.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            alignement = Qt.AlignmentFlag.AlignRight if droite else Qt.AlignmentFlag.AlignLeft
            etiquette.setAlignment(alignement | Qt.AlignmentFlag.AlignVCenter)
        if couleur:
            etiquette.setStyleSheet(f"color: {couleur};")
        return etiquette

    def _remplir_ligne(self, m: MonthlyMemberRow, ligne: int) -> None:
        gris = Color.GRAY_500
        self._grid.addWidget(self._cellule(m.carnet, "grid-total", 0), ligne, 0)
        self._grid.addWidget(self._cellule(m.name, "grid-cell", 1), ligne, 1)
        self._grid.addWidget(self._cellule(m.sex, "grid-cell", 2, couleur=gris), ligne, 2)
        self._grid.addWidget(self._cellule(m.joined, "grid-cell", 3, couleur=gris), ligne, 3)
        colonne = 4
        for cell in m.cells:
            couleur = Color.SUCCESS_600 if cell == "✓" else (Color.DANGER_600 if cell == "✗" else None)
            self._grid.addWidget(self._cellule(cell, "grid-cell", colonne, centre=True, couleur=couleur), ligne, colonne)
            colonne += 1
        couleur_dette = Color.DANGER_600 if m.has_debt else gris
        couleur_avance = Color.SUCCESS_600 if m.has_advance else gris
        role_dette = "grid-total" if m.has_debt else "grid-cell"
        role_avance = "grid-total" if m.has_advance else "grid-cell"
        self._grid.addWidget(self._cellule(m.total_due, "grid-cell", colonne, True), ligne, colonne)
        colonne += 1
        self._grid.addWidget(self._cellule(m.total_paid, "grid-cell", colonne, True), ligne, colonne)
        colonne += 1
        self._grid.addWidget(self._cellule(m.total_debt, role_dette, colonne, True, couleur_dette), ligne, colonne)
        colonne += 1
        self._grid.addWidget(self._cellule(m.advance, role_avance, colonne, True, couleur_avance), ligne, colonne)
        colonne += 1
        actions = AppButton("Enregistrer", Variant.SECONDARY)
        actions.setFixedWidth(80)
        actions.clicked.connect(lambda _=False, c=m.carnet: self.record_payment_requested.emit(c))
        self._grid.addWidget(actions, ligne, colonne, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def _fill_pager(self, model: MonthlyViewModel) -> None:
        _clear_layout(self._pager)
        precedent = AppButton("Précédent", Variant.SECONDARY)
        precedent.setEnabled(bool(model.rows and len(model.rows) > 0))
        precedent.clicked.connect(lambda: self.page_requested.emit(1))
        self._pager.addWidget(precedent)
        self._pager.addWidget(make_label("Pagination à implémenter", "caption"))
        suivant = AppButton("Suivant", Variant.SECONDARY)
        suivant.setEnabled(bool(model.rows and len(model.rows) > 0))
        suivant.clicked.connect(lambda: self.page_requested.emit(2))
        self._pager.addWidget(suivant)
