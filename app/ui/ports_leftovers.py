"""Contrat de la page Reliquats."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class LeftoverRecord:
    id: int
    name: str
    expense_label: str
    amount: int
    date: str


@dataclass(frozen=True)
class LeftoversData:
    exercise_label: str
    is_open: bool
    records: tuple[LeftoverRecord, ...]
    total: int


class LeftoversPort(Protocol):
    def load(self, exercise_label: str) -> LeftoversData: ...
