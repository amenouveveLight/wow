"""Historique de toutes les transactions : entrées (cotisations, arriérés, amendes, reliquats)
et sorties (dépenses), avec filtres, totaux et situation (excédent ou dette)."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date

from app.models.transaction import ARRIERE, COURANT, ENTREE, RUBRIQUES, SORTIE, Transaction
from app.repositories import exercices, historique
from app.services import affichage
from app.services.affichage import Situation


class HistoriqueError(Exception):
    """Paramètres invalides pour l'historique (message affichable)."""


@dataclass(frozen=True)
class PageHistorique:
    lignes: list[Transaction]
    total: int          # nombre de transactions après filtres
    entrees: int        # total des entrées du résultat filtré
    sorties: int        # total des sorties du résultat filtré

    @property
    def situation(self) -> Situation:
        """Entrées − sorties : excédent vert ou dette rouge."""
        return affichage.depuis_ecart(self.entrees - self.sorties)


def lister(conn: sqlite3.Connection, *, exercice_id: int | None = None, search: str | None = None,
           rubrique: str | None = None, sens: str | None = None, nature: str | None = None,
           date_debut: date | None = None, date_fin: date | None = None,
           membre_id: int | None = None, limit: int | None = None,
           offset: int = 0) -> PageHistorique:
    """exercice_id=None : toutes les transactions de tous les exercices.
    nature : 'courant' (cotisations courantes) ou 'arriere' (remboursements d'arriérés)."""
    if exercice_id is not None and exercices.get(conn, exercice_id) is None:
        raise HistoriqueError("Exercice introuvable.")
    if rubrique is not None and rubrique not in RUBRIQUES:
        raise HistoriqueError("Rubrique inconnue.")
    if sens is not None and sens not in (ENTREE, SORTIE):
        raise HistoriqueError("Sens inconnu (entrée ou sortie).")
    if nature is not None and nature not in (COURANT, ARRIERE):
        raise HistoriqueError("Nature inconnue (courant ou arriéré).")
    if date_debut and date_fin and date_debut > date_fin:
        raise HistoriqueError("La date de début ne peut pas suivre la date de fin.")
    filtres = dict(exercice_id=exercice_id, search=(search or "").strip() or None, rubrique=rubrique,
                   sens=sens, nature=nature, date_debut=date_debut, date_fin=date_fin,
                   membre_id=membre_id)
    lignes = historique.list_(conn, limit=limit, offset=offset, **filtres)
    entrees, sorties, total = historique.totals(conn, **filtres)
    return PageHistorique(lignes, total, entrees, sorties)


def historique_membre(conn: sqlite3.Connection, membre_id: int, *, exercice_id: int | None = None,
                      limit: int | None = None, offset: int = 0) -> PageHistorique:
    """Tous les paiements d'un membre (fiche membre)."""
    return lister(conn, exercice_id=exercice_id, membre_id=membre_id, limit=limit, offset=offset)