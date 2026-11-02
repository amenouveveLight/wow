"""Modèle Deces : une collecte funéraire (données uniquement)."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date

from app.models.sexe import Sexe

MEMBRE = "membre"
PARENT = "parent"
BEAU_PARENT = "beau_parent"
AUTRE = "autre"

TYPES = (MEMBRE, PARENT, BEAU_PARENT, AUTRE)
TYPE_LABELS = {
    MEMBRE: "Membre de l’association",
    PARENT: "Parent",
    BEAU_PARENT: "Beau-parent",
    AUTRE: "Autre",
}


@dataclass(frozen=True)
class Deces:
    id: int
    exercice_id: int
    nom_defunt: str
    type_deces: str
    membre_defunt_id: int | None
    date_deces: date
    montant_homme: int
    montant_femme: int
    membre_endeuille_id: int | None
    exempter_endeuille: bool

    def montant_pour(self, sexe: Sexe) -> int:
        """Montant dû par un membre de ce sexe pour cette collecte."""
        return self.montant_homme if sexe is Sexe.HOMME else self.montant_femme

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Deces":
        return cls(
            id=row["id"],
            exercice_id=row["exercice_id"],
            nom_defunt=row["nom_defunt"],
            type_deces=row["type_deces"],
            membre_defunt_id=row["membre_defunt_id"],
            date_deces=date.fromisoformat(row["date_deces"]),
            montant_homme=row["montant_homme"],
            montant_femme=row["montant_femme"],
            membre_endeuille_id=row["membre_endeuille_id"],
            exempter_endeuille=bool(row["exempter_endeuille"]),
        )