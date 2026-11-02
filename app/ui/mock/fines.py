"""Mock des amendes pour le développement."""
from __future__ import annotations

from app.ui.ports_fines import FinesData, FinesPort, FineRecord


class MockFines(FinesPort):
    def load(self, exercise_label: str) -> FinesData:
        records = [
            FineRecord(
                id=1,
                member_carnet="001",
                member_name="Jean Dupont",
                label="Retard à une réunion",
                date="10/10/2025",
                amount_expected=2000,
                amount_collected=2000,
                remaining=0,
            ),
            FineRecord(
                id=2,
                member_carnet="002",
                member_name="Marie Martin",
                label="Non-respect du règlement",
                date="15/10/2025",
                amount_expected=5000,
                amount_collected=2000,
                remaining=3000,
            ),
        ]
        return FinesData(
            exercise_label=exercise_label,
            is_open=True,
            records=tuple(records),
        )
