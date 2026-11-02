"""Modèle Membre (données uniquement)."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date

from app.models.sexe import Sexe

ACTIF = "actif"
DECEDE = "decede"


@dataclass(frozen=True)
class Membre:
    id: int
    numero_carnet: str
    nom: str
    sexe: Sexe
    date_adhesion: date
    statut: str                      # ACTIF | DECEDE
    date_deces: date | None

    @property
    def is_active(self) -> bool:
        return self.statut == ACTIF

    @property
    def adhesion_month(self) -> tuple[int, int]:
        """(année, mois) à partir duquel le membre cotise."""
        return self.date_adhesion.year, self.date_adhesion.month

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Membre":
        return cls(
            id=row["id"],
            numero_carnet=row["numero_carnet"],
            nom=row["nom"],
            sexe=Sexe(row["sexe"]),
            date_adhesion=date.fromisoformat(row["date_adhesion"]),
            statut=row["statut"],
            date_deces=date.fromisoformat(row["date_deces"]) if row["date_deces"] else None,
        )