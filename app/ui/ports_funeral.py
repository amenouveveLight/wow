"""Contrat de la page Cotisations funéraires : types échangés entre l'interface et les services."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True)
class DeathRecord:
    id: int
    deceased_name: str
    death_type: str
    death_date: str
    member_carnet: str | None
    amount_man: int
    amount_woman: int
    total_collected: int
    total_expected: int
    exempted: bool


@dataclass(frozen=True)
class FuneralData:
    exercise_label: str
    is_open: bool
    records: tuple[DeathRecord, ...]


class FuneralPort(Protocol):
    """Données des cotisations funéraires : MockFuneral aujourd'hui, services demain."""

    def load(self, exercise_label: str) -> FuneralData: ...
