"""Contrat de la page Dépenses."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ExpenseRecord:
    id: int
    date: str
    label: str
    beneficiary: str | None
    amount_planned: int
    amount_spent: int


@dataclass(frozen=True)
class ExpensesData:
    exercise_label: str
    is_open: bool
    records: tuple[ExpenseRecord, ...]
    total_planned: int
    total_spent: int


class ExpensesPort(Protocol):
    def load(self, exercise_label: str) -> ExpensesData: ...
