"""Modèle Utilisateur (données uniquement, aucune logique)."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from app.security.session import Role


@dataclass(frozen=True)
class Utilisateur:
    id: int
    identifiant: str
    nom_complet: str
    role: Role
    actif: bool
    mot_de_passe_hash: str
    tentatives_echouees: int
    verrouille_jusqua: str | None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Utilisateur":
        return cls(
            id=row["id"],
            identifiant=row["identifiant"],
            nom_complet=row["nom_complet"],
            role=Role(row["role"]),
            actif=bool(row["actif"]),
            mot_de_passe_hash=row["mot_de_passe_hash"],
            tentatives_echouees=row["tentatives_echouees"],
            verrouille_jusqua=row["verrouille_jusqua"],
        )