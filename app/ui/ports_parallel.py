"""Contrat de la page Cotisations parallèles."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ParallelSubscription:
    id: int
    name: str
    start_date: str
    end_date: str
    amount_man: int
    amount_woman: int
    total_collected: int
    total_expected: int


@dataclass(frozen=True)
class ParallelData:
    exercise_label: str
    is_open: bool
    subscriptions: tuple[ParallelSubscription, ...]


class ParallelPort(Protocol):
    def load(self, exercise_label: str) -> ParallelData: ...
