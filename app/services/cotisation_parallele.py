"""Cotisation parallèle : attendu, perçu, dette d'un membre (fonctions pures).

Le montant est celui du sexe du membre, dû en entier (pas de proratisation).
Un membre non concerné est exclu : adhésion après le mois de fin de la période,
ou décès avant son début.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.models.cotisation_parallele import CotisationParallele
from app.models.membre import Membre
from app.services.cotisation_mensuelle import IMPAYE, NON_APPLICABLE, PARTIEL, PAYE
from app.services.regles import concerned_by_parallel


@dataclass(frozen=True)
class ParallelStatement:
    concerned: bool
    due: int
    paid: int
    status: str            # PAYE | PARTIEL | IMPAYE | NON_APPLICABLE

    @property
    def debt(self) -> int:
        return max(self.due - self.paid, 0)

    @property
    def advance(self) -> int:
        """Excédent versé au-delà du montant attendu."""
        return max(self.paid - self.due, 0)


def build_statement(membre: Membre, cotisation: CotisationParallele, total_paid: int) -> ParallelStatement:
    if total_paid < 0:
        raise ValueError("Le total versé doit être positif ou nul.")
    if not concerned_by_parallel(membre.date_adhesion, membre.date_deces,
                                 cotisation.date_debut, cotisation.date_fin):
        return ParallelStatement(False, 0, total_paid, NON_APPLICABLE)
    due = cotisation.montant_pour(membre.sexe)
    if total_paid >= due:
        status = PAYE
    elif total_paid > 0:
        status = PARTIEL
    else:
        status = IMPAYE
    return ParallelStatement(True, due, total_paid, status)