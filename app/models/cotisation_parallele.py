"""Modèle CotisationParallele (données uniquement)."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date

from app.models.sexe import Sexe


@dataclass(frozen=True)
class CotisationParallele:
    id: int
    exercice_id: int
    nom: str
    date_debut: date
    date_fin: date
    montant_homme: int
    montant_femme: int

    def montant_pour(self, sexe: Sexe) -> int:
        return self.montant_homme if sexe is Sexe.HOMME else self.montant_femme

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "CotisationParallele":
        return cls(
            id=row["id"],
            exercice_id=row["exercice_id"],
            nom=row["nom"],
            date_debut=date.fromisoformat(row["date_debut"]),
            date_fin=date.fromisoformat(row["date_fin"]),
            montant_homme=row["montant_homme"],
            montant_femme=row["montant_femme"],
        )