"""Modèle Amende (données uniquement)."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date

PAYEE = "payee"
PARTIELLE = "partielle"
IMPAYEE = "impayee"
STATUTS = (PAYEE, PARTIELLE, IMPAYEE)


@dataclass(frozen=True)
class Amende:
    id: int
    exercice_id: int
    membre_id: int
    nom: str
    libelle: str
    date_amende: date
    montant_attendu: int
    montant_collecte: int

    @property
    def manque_a_gagner(self) -> int:
        """Part non encaissée."""
        return max(self.montant_attendu - self.montant_collecte, 0)

    @property
    def statut(self) -> str:
        if self.montant_collecte >= self.montant_attendu:
            return PAYEE
        if self.montant_collecte > 0:
            return PARTIELLE
        return IMPAYEE

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Amende":
        return cls(
            id=row["id"],
            exercice_id=row["exercice_id"],
            membre_id=row["membre_id"],
            nom=row["nom"],
            libelle=row["libelle"],
            date_amende=date.fromisoformat(row["date_amende"]),
            montant_attendu=row["montant_attendu"],
            montant_collecte=row["montant_collecte"],
        )


@dataclass(frozen=True)
class AmendeLigne:
    amende: Amende
    membre_nom: str
    numero_carnet: str