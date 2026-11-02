"""Mock des rapports pour le développement."""
from __future__ import annotations

from app.ui.ports_reports import ReportsData, ReportsPort


class MockReports(ReportsPort):
    def load(self, exercise_label: str) -> ReportsData:
        return ReportsData(exercise_label=exercise_label, is_open=True)
