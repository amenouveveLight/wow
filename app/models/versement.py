"""Modèle Versement (données uniquement)."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date

MENSUELLE = "mensuelle"
FUNERAIRE = "funeraire"
PARALLELE = "parallele"
AMENDE = "amende"                 # uniquement pour le règlement d'arriérés

NATURE_COURANT = "courant"
NATURE_ARRIERE = "arriere"

RUBRIQUE_LABELS = {
    MENSUELLE: "cotisation mensuelle",
    FUNERAIRE: "cotisation funéraire",
    PARALLELE: "cotisation parallèle",
    AMENDE: "amende",
}
# Saisie ordinaire. Les arriérés (funéraire, parallèle, amendes) passent par reglement_service.
RUBRIQUES_SAISISSABLES = (MENSUELLE, FUNERAIRE, PARALLELE)


@dataclass(frozen=True)
class Versement:
    id: int
    membre_id: int
    exercice_id: int
    rubrique: str
    cotisation_parallele_id: int | None
    date_versement: date
    montant: int
    note: str | None
    cree_par: int | None
    cree_le: str
    nature: str = NATURE_COURANT              # 'courant' | 'arriere'
    exercice_origine_id: int | None = None    # arriéré : exercice dont on rembourse la dette
    recu: int | None = None                   # numéro de reçu (plusieurs lignes possibles)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Versement":
        return cls(
            id=row["id"],
            membre_id=row["membre_id"],
            exercice_id=row["exercice_id"],
            rubrique=row["rubrique"],
            cotisation_parallele_id=row["cotisation_parallele_id"],
            date_versement=date.fromisoformat(row["date_versement"]),
            montant=row["montant"],
            note=row["note"],
            cree_par=row["cree_par"],
            cree_le=row["cree_le"],
            nature=row["nature"],
            exercice_origine_id=row["exercice_origine_id"],
            recu=row["recu"],
        )