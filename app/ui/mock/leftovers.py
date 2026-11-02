"""Mock des reliquats pour le développement."""
from __future__ import annotations

from app.ui.ports_leftovers import LeftoversData, LeftoversPort, LeftoverRecord


class MockLeftovers(LeftoversPort):
    def load(self, exercise_label: str) -> LeftoversData:
        records = [
            LeftoverRecord(
                id=1,
                name="Excédent location",
                expense_label="Location salle réunion",
                amount=5000,
                date="20/10/2025",
            ),
        ]
        total = sum(r.amount for r in records)
        return LeftoversData(
            exercise_label=exercise_label,
            is_open=True,
            records=tuple(records),
            total=total,
        )
