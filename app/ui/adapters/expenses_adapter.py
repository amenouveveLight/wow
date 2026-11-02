"""Adaptateur des dépenses : connecte ExpensesPort aux services."""
from __future__ import annotations

import sqlite3

from app.database.connection import get_connection
from app.repositories import exercices, depenses
from app.services.depense_service import resume
from app.ui.ports_expenses import ExpensesData, ExpenseRecord


class ExpensesAdapter:
    """Implémente ExpensesPort en utilisant les services."""

    def __init__(self) -> None:
        pass

    def load(self, exercise_label: str) -> ExpensesData:
        conn = get_connection()
        try:
            from app.repositories import exercices
            exercice = exercices.get_by_libelle(conn, exercise_label)

            if not exercice:
                conn.close()
                return self._empty_data(exercise_label)

            exercice_id = exercice.id
            is_open = exercice.statut == "ouvert"

            # Récupérer les dépenses
            expenses = depenses.list_for_exercice(conn, exercice_id)

            # Convertir en ExpenseRecord
            records = []
            for e in expenses:
                records.append(ExpenseRecord(
                    id=e.id,
                    date=e.date_depense,
                    label=e.libelle,
                    beneficiary=e.beneficiaire,
                    amount_planned=e.montant_prevu,
                    amount_spent=e.montant_depense,
                ))

            # Totaux
            totals = resume(conn, exercice_id)
            total_planned = totals.prevu
            total_spent = totals.depense

            conn.close()
            return ExpensesData(
                exercise_label=exercise_label,
                is_open=is_open,
                total_planned=total_planned,
                total_spent=total_spent,
                records=tuple(records)
            )
        except Exception as e:
            conn.close()
            print(f"Erreur expenses adapter: {e}")
            import traceback
            traceback.print_exc()
            return self._empty_data(exercise_label)

    def _empty_data(self, exercise_label: str) -> ExpensesData:
        return ExpensesData(
            exercise_label=exercise_label,
            is_open=True,
            total_planned=0,
            total_spent=0,
            records=()
        )
