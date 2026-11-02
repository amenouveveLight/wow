"""Mock des cotisations mensuelles pour le développement (remplacé par les services plus tard)."""
from __future__ import annotations

from app.ui.ports_monthly import MonthlyCell, MonthlyData, MonthlyMember, MonthlyPort


class MockMonthly(MonthlyPort):
    def load(self, exercise_label: str) -> MonthlyData:
        members = [
            MonthlyMember(
                carnet="001",
                name="Jean Dupont",
                sex="M",
                joined="01/09/2025",
                cells=(
                    MonthlyCell("Sep", "paye", 5000, 5000, 0),
                    MonthlyCell("Oct", "paye", 5000, 5000, 0),
                    MonthlyCell("Nov", "paye", 5000, 5000, 0),
                    MonthlyCell("Déc", "paye", 5000, 5000, 0),
                    MonthlyCell("Jan", "paye", 5000, 5000, 0),
                    MonthlyCell("Fév", "paye", 5000, 5000, 0),
                    MonthlyCell("Mar", "paye", 5000, 5000, 0),
                    MonthlyCell("Avr", "paye", 5000, 5000, 0),
                    MonthlyCell("Mai", "paye", 5000, 5000, 0),
                    MonthlyCell("Juin", "paye", 5000, 5000, 0),
                    MonthlyCell("Juil", "paye", 5000, 5000, 0),
                    MonthlyCell("Août", "paye", 5000, 5000, 0),
                ),
                total_due=60000,
                total_paid=60000,
                total_debt=0,
                advance=0,
                carried_debt=0,
                carried_advance=0,
            ),
            MonthlyMember(
                carnet="002",
                name="Marie Martin",
                sex="F",
                joined="15/09/2025",
                cells=(
                    MonthlyCell("Sep", "paye", 3000, 3000, 0),
                    MonthlyCell("Oct", "paye", 3000, 3000, 0),
                    MonthlyCell("Nov", "paye", 3000, 3000, 0),
                    MonthlyCell("Déc", "partiel", 3000, 1500, 1500),
                    MonthlyCell("Jan", "impaye", 3000, 0, 3000),
                    MonthlyCell("Fév", "impaye", 3000, 0, 3000),
                    MonthlyCell("Mar", "impaye", 3000, 0, 3000),
                    MonthlyCell("Avr", "impaye", 3000, 0, 3000),
                    MonthlyCell("Mai", "impaye", 3000, 0, 3000),
                    MonthlyCell("Juin", "impaye", 3000, 0, 3000),
                    MonthlyCell("Juil", "impaye", 3000, 0, 3000),
                    MonthlyCell("Août", "impaye", 3000, 0, 3000),
                ),
                total_due=36000,
                total_paid=10500,
                total_debt=25500,
                advance=0,
                carried_debt=0,
                carried_advance=0,
            ),
        ]
        return MonthlyData(
            exercise_label=exercise_label,
            is_open=True,
            tariff_man=5000,
            tariff_woman=3000,
            members=tuple(members),
        )
