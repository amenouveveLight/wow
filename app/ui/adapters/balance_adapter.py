"""Adaptateur du bilan financier : connecte BalancePort aux services."""
from __future__ import annotations

import sqlite3
from datetime import date

from app.database.connection import get_connection
from app.repositories import exercices
from app.services.bilan_service import consulter
from app.ui.ports_balance import BalanceData


class BalanceAdapter:
    """Implémente BalancePort en utilisant les services."""

    def __init__(self) -> None:
        pass

    def load(self, exercise_label: str) -> BalanceData:
        conn = get_connection()
        try:
            exercice = conn.execute(
                "SELECT id, libelle, statut, date_debut, date_fin FROM exercices WHERE libelle = ?",
                (exercise_label,)
            ).fetchone()
            
            if not exercice:
                conn.close()
                return self._empty_data(exercise_label)
            
            exercice_id = exercice["id"]
            is_open = exercice["statut"] == "ouvert"
            period_start = date.fromisoformat(exercice["date_debut"])
            period_end = date.fromisoformat(exercice["date_fin"])
            
            # Calculer le bilan
            bilan = consulter(conn, exercice_id)
            
            conn.close()
            return BalanceData(
                exercise_label=exercise_label,
                is_open=is_open,
                period_start=period_start.strftime("%d/%m/%Y"),
                period_end=period_end.strftime("%d/%m/%Y"),
                total_revenue=bilan.recettes,
                total_expenses=bilan.depenses,
                balance=bilan.solde,
                carried_forward=bilan.report_precedent,
                closing_balance=bilan.solde_cloture,
                is_positive=bilan.solde_cloture >= 0,
            )
        except Exception as e:
            conn.close()
            print(f"Erreur balance adapter: {e}")
            return self._empty_data(exercise_label)

    def _empty_data(self, exercise_label: str) -> BalanceData:
        return BalanceData(
            exercise_label=exercise_label,
            is_open=True,
            period_start="01/09/2025",
            period_end="31/08/2026",
            total_revenue=0,
            total_expenses=0,
            balance=0,
            carried_forward=0,
            closing_balance=0,
            is_positive=True,
        )
