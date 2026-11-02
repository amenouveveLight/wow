"""Adaptateur des rapports : connecte ReportsPort aux services."""
from __future__ import annotations

from app.ui.ports_reports import ReportsData


class ReportsAdapter:
    """Implémente ReportsPort en utilisant les services."""

    def __init__(self) -> None:
        pass

    def load(self, exercise_label: str) -> ReportsData:
        # Pour l'instant, retourne des données vides
        # À implémenter avec les services de génération de rapports
        return ReportsData(
            exercise_label=exercise_label,
            can_export_excel=False,
            can_export_pdf=False,
        )
