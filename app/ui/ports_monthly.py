"""Contrat de la page Cotisations mensuelles : types échangés entre l'interface et les services."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True)
class MonthlyCell:
    month: str
    status: str
    due: int
    paid: int
    debt: int


@dataclass(frozen=True)
class MonthlyMember:
    carnet: str
    name: str
    sex: str
    joined: str
    cells: tuple[MonthlyCell, ...]
    total_due: int
    total_paid: int
    total_debt: int
    advance: int
    carried_debt: int
    carried_advance: int


@dataclass(frozen=True)
class MonthlyData:
    exercise_label: str
    is_open: bool
    tariff_man: int
    tariff_woman: int
    members: tuple[MonthlyMember, ...]


class MonthlyPort(Protocol):
    """Données des cotisations mensuelles : MockMonthly aujourd'hui, services demain."""

    def load(self, exercise_label: str) -> MonthlyData: ...
