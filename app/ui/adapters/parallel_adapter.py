"""Adaptateur des cotisations parallèles : connecte ParallelPort aux services."""
from __future__ import annotations

import sqlite3

from app.database.connection import get_connection
from app.repositories import exercices, cotisations_paralleles
from app.ui.ports_parallel import ParallelData, ParallelSubscription


class ParallelAdapter:
    """Implémente ParallelPort en utilisant les services."""

    def __init__(self) -> None:
        pass

    def load(self, exercise_label: str) -> ParallelData:
        conn = get_connection()
        try:
            exercice = conn.execute(
                "SELECT id, libelle, statut FROM exercices WHERE libelle = ?",
                (exercise_label,)
            ).fetchone()
            
            if not exercice:
                conn.close()
                return self._empty_data(exercise_label)
            
            exercice_id = exercice["id"]
            is_open = exercice["statut"] == "ouvert"
            
            # Récupérer les cotisations parallèles
            subs = cotisations_paralleles.list_for_exercice(conn, exercice_id)
            
            # Convertir en ParallelSubscription
            subscriptions = []
            for s in subs:
                subscriptions.append(ParallelSubscription(
                    id=s["id"],
                    name=s["nom"],
                    start_date=s["date_debut"],
                    end_date=s["date_fin"],
                    amount_man=s["montant_homme"],
                    amount_woman=s["montant_femme"],
                    total_expected=s["total_attendu"] if "total_attendu" in s else 0,
                    total_collected=s["total_perçu"] if "total_perçu" in s else 0,
                ))
            
            conn.close()
            return ParallelData(
                exercise_label=exercise_label,
                is_open=is_open,
                subscriptions=tuple(subscriptions)
            )
        except Exception as e:
            conn.close()
            print(f"Erreur parallel adapter: {e}")
            return self._empty_data(exercise_label)

    def _empty_data(self, exercise_label: str) -> ParallelData:
        return ParallelData(
            exercise_label=exercise_label,
            is_open=True,
            subscriptions=()
        )
