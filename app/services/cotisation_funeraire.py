"""Cotisation funéraire : cases par décès, dû, dette, avance (fonctions pures).

Règles (cahier des charges §3.4 et paiement des arriérés) :
- un versement courant est imputé au décès le plus ancien de l'exercice ;
- les arriérés (dettes reportées) ne se règlent que par des paiements explicites
  de nature « arriéré » : ils ne touchent pas aux cases de l'exercice ;
- une avance reportée compte comme déjà versée ;
- les membres non concernés sont grisés et exclus du total dû.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.models.deces import Deces
from app.models.membre import Membre
from app.services.cotisation_mensuelle import IMPAYE, NON_APPLICABLE, PARTIEL, PAYE
from app.services.regles import concerned_by_death

DEFUNT = "defunt"
EXEMPTE = "exempte"
NON_CONCERNE = "non_concerne"


@dataclass(frozen=True)
class DeathCell:
    death: Deces
    status: str                 # PAYE | PARTIEL | IMPAYE | NON_APPLICABLE
    due: int
    paid: int
    reason: str | None = None   # DEFUNT | EXEMPTE | NON_CONCERNE si non applicable

    @property
    def debt(self) -> int:
        return self.due - self.paid


@dataclass(frozen=True)
class FuneralStatement:
    cells: tuple[DeathCell, ...]        # une case par décès, du plus ancien au plus récent
    total_due: int
    total_paid: int                     # versements COURANTS de l'exercice
    carried_debt: int = 0               # arriérés reçus de l'exercice précédent
    carried_debt_paid: int = 0          # arriérés remboursés dans l'exercice (paiements explicites)
    carried_advance: int = 0            # avance reportée, comptée comme déjà versée

    @property
    def credit(self) -> int:
        return self.total_paid + self.carried_advance

    @property
    def cash_total(self) -> int:
        """Tout l'argent encaissé dans l'exercice (courant + arriérés)."""
        return self.total_paid + self.carried_debt_paid

    @property
    def carried_debt_left(self) -> int:
        return self.carried_debt - self.carried_debt_paid

    @property
    def debt(self) -> int:
        """Dette de l'exercice en cours seulement."""
        return max(self.total_due - self.credit, 0)

    @property
    def total_debt(self) -> int:
        """Tout ce que le membre doit encore, arriérés restants compris."""
        return self.debt + self.carried_debt_left

    @property
    def advance(self) -> int:
        return max(self.credit - self.total_due, 0)


def build_statement(membre: Membre, deaths: list[Deces], paid_current: int,
                    carried_debt: int = 0, carried_advance: int = 0,
                    arrears_paid: int = 0) -> FuneralStatement:
    if min(paid_current, carried_debt, carried_advance, arrears_paid) < 0:
        raise ValueError("Les montants versés et les reports doivent être positifs ou nuls.")
    remaining = paid_current + carried_advance
    cells: list[DeathCell] = []
    for death in sorted(deaths, key=lambda d: (d.date_deces, d.id)):
        if death.membre_defunt_id == membre.id:
            reason = DEFUNT
        elif not concerned_by_death(membre.date_adhesion, membre.date_deces, death.date_deces):
            reason = NON_CONCERNE
        elif death.exempter_endeuille and death.membre_endeuille_id == membre.id:
            reason = EXEMPTE
        else:
            reason = None
        if reason:
            cells.append(DeathCell(death, NON_APPLICABLE, 0, 0, reason))
            continue
        due = death.montant_pour(membre.sexe)
        paid = min(remaining, due)
        remaining -= paid
        status = PAYE if paid >= due else (PARTIEL if paid > 0 else IMPAYE)
        cells.append(DeathCell(death, status, due, paid))
    return FuneralStatement(tuple(cells), sum(c.due for c in cells), paid_current,
                            carried_debt, min(arrears_paid, carried_debt), carried_advance)