"""Modèle Report : dette, avance ou solde reporté à l'exercice suivant (données uniquement)."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class Report:
    id: int
    exercice_source_id: int | None      # None : reprise initiale
    exercice_cible_id: int
    membre_id: int | None               # None : solde global de l'association
    type: str                           # 'dette' | 'avance' | 'solde'
    rubrique: str | None                # 'mensuelle' | 'funeraire' | 'parallele' | 'amende' | None
    montant: int                        # négatif possible pour un solde
    exercice_origine_id: int | None = None   # exercice où la dette est née

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Report":
        return cls(
            id=row["id"],
            exercice_source_id=row["exercice_source_id"],
            exercice_cible_id=row["exercice_cible_id"],
            membre_id=row["membre_id"],
            type=row["type"],
            rubrique=row["rubrique"],
            montant=row["montant"],
            exercice_origine_id=row["exercice_origine_id"],
        )