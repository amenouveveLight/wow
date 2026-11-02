"""Mock des cotisations funéraires pour le développement."""
from __future__ import annotations

from app.ui.ports_funeral import DeathRecord, FuneralData, FuneralPort


class MockFuneral(FuneralPort):
    def load(self, exercise_label: str) -> FuneralData:
        records = [
            DeathRecord(
                id=1,
                deceased_name="Pierre Lambert",
                death_type="membre",
                death_date="15/10/2025",
                member_carnet="003",
                amount_man=10000,
                amount_woman=5000,
                total_collected=15000,
                total_expected=15000,
                exempted=False,
            ),
            DeathRecord(
                id=2,
                deceased_name="Marie Durand",
                death_type="parent",
                death_date="02/11/2025",
                member_carnet="005",
                amount_man=15000,
                amount_woman=7500,
                total_collected=10000,
                total_expected=22500,
                exempted=False,
            ),
        ]
        return FuneralData(
            exercise_label=exercise_label,
            is_open=True,
            records=tuple(records),
        )
