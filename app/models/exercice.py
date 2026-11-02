# app/models/exercice.py
"""Modèle Exercice (données uniquement)."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date

from app.services import calendrier


@dataclass(frozen=True)
class Exercice:
    id: int
    libelle: str
    date_debut: date
    date_fin: date
    statut: str                      # 'ouvert' | 'cloture'
    date_cloture: str | None

    @property
    def is_open(self) -> bool:
        return self.statut == "ouvert"

    @property
    def start_year(self) -> int:
        return self.date_debut.year

    @property
    def months(self) -> list[tuple[int, int]]:
        return calendrier.exercise_months(self.start_year)

    def contains(self, d: date) -> bool:
        return self.date_debut <= d <= self.date_fin

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Exercice":
        return cls(
            id=row["id"],
            libelle=row["libelle"],
            date_debut=date.fromisoformat(row["date_debut"]),
            date_fin=date.fromisoformat(row["date_fin"]),
            statut=row["statut"],
            date_cloture=row["date_cloture"],
        )