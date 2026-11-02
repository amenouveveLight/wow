"""Cotisation mensuelle : remplissage des 12 mois, dû, dette, avance (fonctions pures).

Règles (cahier des charges §3.3 et report d'exercice) :
- le total versé remplit les mois applicables dans l'ordre de l'exercice ;
- imputation « plus ancienne dette d'abord » : les versements règlent d'abord la
  dette reportée de l'exercice précédent, puis les mois de l'exercice ;
- une avance reportée compte comme déjà versée.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.services.regles import Month, applicable_months

PAYE = "paye"
PARTIEL = "partiel"
IMPAYE = "impaye"
NON_APPLICABLE = "na"


@dataclass(frozen=True)
class MonthCell:
    month: Month
    status: str            # PAYE | PARTIEL | IMPAYE | NON_APPLICABLE
    due: int
    paid: int

    @property
    def debt(self) -> int:
        return self.due - self.paid


@dataclass(frozen=True)
class MonthlyStatement:
    cells: tuple[MonthCell, ...]       # toujours 12 cases, dans l'ordre de l'exercice
    total_due: int                     # dû de l'exercice
    total_paid: int                    # argent versé par le membre dans l'exercice
    carried_debt: int = 0              # dette reportée de l'exercice précédent
    carried_debt_paid: int = 0         # part des versements qui l'a réglée (la plus ancienne d'abord)
    carried_advance: int = 0           # avance reportée, comptée comme déjà versée

    @property
    def credit(self) -> int:
        """Ce qui reste pour l'exercice : versements − ancienne dette réglée + avance reportée."""
        return self.total_paid - self.carried_debt_paid + self.carried_advance

    @property
    def carried_debt_left(self) -> int:
        return self.carried_debt - self.carried_debt_paid

    @property
    def debt(self) -> int:
        """Dette de l'exercice en cours seulement (dû − crédit)."""
        return max(self.total_due - self.credit, 0)

    @property
    def total_debt(self) -> int:
        """Tout ce que le membre doit encore : dette de l'exercice + ancienne dette restante."""
        return self.debt + self.carried_debt_left

    @property
    def advance(self) -> int:
        """Excédent, reporté sur l'exercice suivant comme avance."""
        return max(self.credit - self.total_due, 0)


def build_statement(tarif: int, months: list[Month], applicable: list[Month], total_paid: int,
                    carried_debt: int = 0, carried_advance: int = 0) -> MonthlyStatement:
    """Remplit les mois applicables dans l'ordre avec ce qui reste après l'ancienne dette."""
    if min(tarif, total_paid, carried_debt, carried_advance) < 0:
        raise ValueError("Le tarif, le total versé et les reports doivent être positifs ou nuls.")
    applicable_set = set(applicable)
    paid_old = min(total_paid, carried_debt)
    remaining = total_paid - paid_old + carried_advance
    cells: list[MonthCell] = []
    for month in months:
        if month not in applicable_set:
            cells.append(MonthCell(month, NON_APPLICABLE, 0, 0))
            continue
        paid = min(remaining, tarif)
        remaining -= paid
        if paid >= tarif:
            status = PAYE
        elif paid > 0:
            status = PARTIEL
        else:
            status = IMPAYE
        cells.append(MonthCell(month, status, tarif, paid))
    return MonthlyStatement(tuple(cells), sum(c.due for c in cells), total_paid,
                            carried_debt, paid_old, carried_advance)


def monthly_statement(adhesion: date, deces: date | None, months: list[Month], tarif: int,
                      total_paid: int, carried_debt: int = 0,
                      carried_advance: int = 0) -> MonthlyStatement:
    """Relevé complet d'un membre : applique la règle du mois d'adhésion / décès."""
    return build_statement(tarif, months, applicable_months(adhesion, deces, months),
                           total_paid, carried_debt, carried_advance)