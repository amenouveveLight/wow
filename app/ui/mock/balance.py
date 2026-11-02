"""Mock du bilan financier pour le développement."""
from __future__ import annotations

from app.ui.ports_balance import BalanceData, BalancePort


class MockBalance(BalancePort):
    def load(self, exercise_label: str) -> BalanceData:
        return BalanceData(
            exercise_label=exercise_label,
            is_open=True,
            period_start="01/09/2025",
            period_end="31/08/2026",
            total_revenue=1500000,
            total_expenses=850000,
            balance=650000,
            carried_forward=100000,
            closing_balance=750000,
        )
