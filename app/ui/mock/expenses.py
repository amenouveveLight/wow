"""Mock des dépenses pour le développement."""
from __future__ import annotations

from app.ui.ports_expenses import ExpensesData, ExpensesPort, ExpenseRecord


class MockExpenses(ExpensesPort):
    def load(self, exercise_label: str) -> ExpensesData:
        records = [
            ExpenseRecord(
                id=1,
                date="05/09/2025",
                label="Fournitures de bureau",
                beneficiary="Librairie centrale",
                amount_planned=15000,
                amount_spent=12000,
            ),
            ExpenseRecord(
                id=2,
                date="20/10/2025",
                label="Location salle réunion",
                beneficiary="Mairie",
                amount_planned=50000,
                amount_spent=55000,
            ),
        ]
        total_planned = sum(r.amount_planned for r in records)
        total_spent = sum(r.amount_spent for r in records)
        return ExpensesData(
            exercise_label=exercise_label,
            is_open=True,
            records=tuple(records),
            total_planned=total_planned,
            total_spent=total_spent,
        )
