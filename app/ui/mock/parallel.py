"""Mock des cotisations parallèles pour le développement."""
from __future__ import annotations

from app.ui.ports_parallel import ParallelData, ParallelPort, ParallelSubscription


class MockParallel(ParallelPort):
    def load(self, exercise_label: str) -> ParallelData:
        subscriptions = [
            ParallelSubscription(
                id=1,
                name="Fête de rentrée",
                start_date="01/09/2025",
                end_date="30/09/2025",
                amount_man=2000,
                amount_woman=1000,
                total_collected=45000,
                total_expected=48000,
            ),
            ParallelSubscription(
                id=2,
                name="Cadeau de fin d'année",
                start_date="01/12/2025",
                end_date="31/12/2025",
                amount_man=3000,
                amount_woman=1500,
                total_collected=0,
                total_expected=72000,
            ),
        ]
        return ParallelData(
            exercise_label=exercise_label,
            is_open=True,
            subscriptions=tuple(subscriptions),
        )
