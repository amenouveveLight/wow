"""Modèles Depense et Reliquat (données uniquement)."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Depense:
    id: int
    exercice_id: int
    date_depense: date
    libelle: str
    beneficiaire: str | None
    montant_prevu: int
    montant_depense: int

    @property
    def reliquat_montant(self) -> int:
        """Ce qui reste du montant prévu (devient un reliquat)."""
        return max(self.montant_prevu - self.montant_depense, 0)

    @property
    def depassement(self) -> int:
        """Ce qui a été dépensé au-delà du montant prévu."""
        return max(self.montant_depense - self.montant_prevu, 0)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Depense":
        return cls(
            id=row["id"],
            exercice_id=row["exercice_id"],
            date_depense=date.fromisoformat(row["date_depense"]),
            libelle=row["libelle"],
            beneficiaire=row["beneficiaire"],
            montant_prevu=row["montant_prevu"],
            montant_depense=row["montant_depense"],
        )


@dataclass(frozen=True)
class Reliquat:
    id: int
    exercice_id: int
    depense_id: int
    nom: str
    montant: int
    date_reliquat: date

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Reliquat":
        return cls(
            id=row["id"],
            exercice_id=row["exercice_id"],
            depense_id=row["depense_id"],
            nom=row["nom"],
            montant=row["montant"],
            date_reliquat=date.fromisoformat(row["date_reliquat"]),
        )


@dataclass(frozen=True)
class DepenseLigne:
    depense: Depense
    reliquat: Reliquat | None


@dataclass(frozen=True)
class ReliquatLigne:
    reliquat: Reliquat
    depense_libelle: str