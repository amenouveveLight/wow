"""Modèle Transaction : une ligne de l'historique des paiements (données uniquement)."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date

ENTREE, SORTIE = "entree", "sortie"
COURANT, ARRIERE = "courant", "arriere"

RUBRIQUES = ("mensuelle", "funeraire", "parallele", "amende", "reliquat", "depense")
RUBRIQUE_LABELS = {
    "mensuelle": "Cotisation mensuelle",
    "funeraire": "Cotisation funéraire",
    "parallele": "Cotisation parallèle",
    "amende": "Amende",
    "reliquat": "Reliquat",
    "depense": "Dépense",
}


@dataclass(frozen=True)
class Transaction:
    source: str                 # 'versement' | 'amende' | 'reliquat' | 'depense'
    source_id: int
    date_operation: date
    rubrique: str
    sens: str                   # ENTREE | SORTIE
    montant: int                # toujours positif : « sens » dit si l'argent entre ou sort
    membre_id: int | None
    membre_nom: str | None
    numero_carnet: str | None
    libelle: str
    beneficiaire: str | None
    note: str | None
    saisi_par: str
    cree_le: str
    exercice_id: int
    nature: str = COURANT       # COURANT | ARRIERE (remboursement d'arriérés)
    periode: str | None = None  # « Exercice 2026-2027 » ou « Arriérés de 2025-2026 »
    recu: int | None = None     # numéro de reçu

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Transaction":
        return cls(
            source=row["source"],
            source_id=row["source_id"],
            date_operation=date.fromisoformat(row["date_operation"]),
            rubrique=row["rubrique"],
            sens=row["sens"],
            montant=row["montant"],
            membre_id=row["membre_id"],
            membre_nom=row["membre_nom"],
            numero_carnet=row["numero_carnet"],
            libelle=row["libelle"],
            beneficiaire=row["beneficiaire"],
            note=row["note"],
            saisi_par=row["saisi_par"],
            cree_le=row["cree_le"],
            exercice_id=row["exercice_id"],
            nature=row["nature"],
            periode=row["periode"],
            recu=row["recu"],
        )