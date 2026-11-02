"""Adaptateur des membres : connecte MembersPort aux services."""
from __future__ import annotations

import sqlite3
from datetime import date

from app.database.connection import get_connection
from app.repositories import membres, exercices
from app.services.tableau_mensuel import tableau as tableau_mensuel
from app.ui.ports_members import MemberInfo, MembersData, MemberStatus


class MembersAdapter:
    """Implémente MembersPort en utilisant les services."""

    def __init__(self) -> None:
        pass

    def load(self, exercise_label: str) -> MembersData:
        conn = get_connection()
        try:
            exercice = conn.execute(
                "SELECT id, libelle, statut FROM exercices WHERE libelle = ?",
                (exercise_label,)
            ).fetchone()

            if not exercice:
                conn.close()
                return MembersData(exercise_label, True, ())

            exercice_id = exercice["id"]
            is_open = exercice["statut"] == "ouvert"

            # Récupérer tous les membres
            all_members = membres.list_(conn)

            # Calculer les totaux par membre pour cet exercice
            members_info = []
            for m in all_members:
                statut = MemberStatus.ACTIF if m.statut == "actif" else MemberStatus.DECEDE

                # Calculer dû et reçu pour cet exercice
                du = 0
                recu = 0

                if is_open:
                    # Utiliser le tableau mensuel pour calculer
                    try:
                        tableau = tableau_mensuel(conn, exercice_id)
                        for ligne in tableau:
                            if ligne.membre_id == m.id:
                                du = ligne.du
                                recu = ligne.perçu
                                break
                    except Exception:
                        pass

                members_info.append(MemberInfo(
                    m.numero_carnet,
                    m.nom,
                    m.sexe.value,
                    m.date_adhesion,
                    statut,
                    du,
                    recu
                ))

            conn.close()
            return MembersData(exercise_label, is_open, tuple(members_info))
        except Exception as e:
            conn.close()
            print(f"Erreur members adapter: {e}")
            import traceback
            traceback.print_exc()
            return MembersData(exercise_label, True, ())
