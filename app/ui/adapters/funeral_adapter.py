"""Adaptateur des cotisations funéraires : connecte FuneralPort aux services."""
from __future__ import annotations

import sqlite3

from app.database.connection import get_connection
from app.repositories import exercices
from app.services.deces_service import list_collectes
from app.ui.ports_funeral import FuneralData, DeathRecord


class FuneralAdapter:
    """Implémente FuneralPort en utilisant les services."""

    def __init__(self) -> None:
        pass

    def load(self, exercise_label: str) -> FuneralData:
        conn = get_connection()
        try:
            from app.repositories import exercices
            exercice = exercices.get_by_libelle(conn, exercise_label)

            if not exercice:
                conn.close()
                return self._empty_data(exercise_label)

            exercice_id = exercice.id
            is_open = exercice.statut == "ouvert"

            # Récupérer les collectes de décès
            collectes = list_collectes(conn, exercice_id)

            # Convertir en DeathRecord
            records = []
            for c in collectes:
                records.append(DeathRecord(
                    id=c.id,
                    deceased_name=c.nom_defunt,
                    death_type=c.type_deces,
                    death_date=c.date_deces,
                    member_carnet=c.numero_carnet if c.membre_id else None,
                    amount_man=c.montant_homme,
                    amount_woman=c.montant_femme,
                    total_collected=c.total_perçu,
                    total_expected=c.total_attendu,
                    exempted=c.exempter_endeuille == 1,
                ))

            conn.close()
            return FuneralData(
                exercise_label=exercise_label,
                is_open=is_open,
                records=tuple(records)
            )
        except Exception as e:
            conn.close()
            print(f"Erreur funeral adapter: {e}")
            import traceback
            traceback.print_exc()
            return self._empty_data(exercise_label)

    def _empty_data(self, exercise_label: str) -> FuneralData:
        return FuneralData(
            exercise_label=exercise_label,
            is_open=True,
            records=()
        )
