"""Contrat de la page Amendes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class FineRecord:
    id: int
    member_carnet: str
    member_name: str
    label: str
    date: str
    amount_expected: int
    amount_collected: int
    remaining: int


@dataclass(frozen=True)
class FinesData:
    exercise_label: str
    is_open: bool
    records: tuple[FineRecord, ...]


class FinesPort(Protocol):
    def load(self, exercise_label: str) -> FinesData: ...
