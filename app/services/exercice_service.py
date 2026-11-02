"""Règles des exercices : création, tarifs mensuels, exercice affiché par défaut."""
from __future__ import annotations

import sqlite3
from datetime import date

from app.database.connection import transaction
from app.models.exercice import Exercice
from app.models.sexe import Sexe
from app.repositories import exercices
from app.security import audit
from app.security.audit import Action
from app.security.session import Permission, Session
from app.services import calendrier


class ExerciceError(Exception):
    """Règle de gestion des exercices non respectée."""


def _check_amount(value: int, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ExerciceError(f"{label} : entrez un montant entier positif ou nul (en FCFA).")


def _fmt(amount: int) -> str:
    return f"{amount:,}".replace(",", "\u00A0") + " FCFA"


def create_exercice(conn: sqlite3.Connection, session: Session, start_year: int,
                    tarif_homme: int, tarif_femme: int) -> Exercice:
    session.require(Permission.SETTINGS_MANAGE)
    if not 2000 <= start_year <= 2100:
        raise ExerciceError("Année de début invalide.")
    _check_amount(tarif_homme, "Cotisation mensuelle des hommes")
    _check_amount(tarif_femme, "Cotisation mensuelle des femmes")

    libelle = calendrier.libelle(start_year)
    if exercices.get_by_libelle(conn, libelle):
        raise ExerciceError(f"L'exercice {libelle} existe déjà.")

    debut, fin = calendrier.bounds(start_year)
    with transaction(conn):
        exercice_id = exercices.create(conn, libelle, debut, fin)
        exercices.upsert_tarif(conn, exercice_id, Sexe.HOMME, tarif_homme)
        exercices.upsert_tarif(conn, exercice_id, Sexe.FEMME, tarif_femme)
        audit.log(conn, session.user, Action.EXERCICE_CREATION, f"Exercice {libelle}",
                  f"Hommes {_fmt(tarif_homme)} · Femmes {_fmt(tarif_femme)} par mois")
    return exercices.get(conn, exercice_id)


def set_tarifs(conn: sqlite3.Connection, session: Session, exercice_id: int,
               tarif_homme: int, tarif_femme: int) -> None:
    session.require(Permission.SETTINGS_MANAGE)
    exercice = exercices.get(conn, exercice_id)
    if exercice is None:
        raise ExerciceError("Exercice introuvable.")
    if not exercice.is_open:
        raise ExerciceError(f"L'exercice {exercice.libelle} est clôturé : ses montants ne peuvent plus changer.")
    _check_amount(tarif_homme, "Cotisation mensuelle des hommes")
    _check_amount(tarif_femme, "Cotisation mensuelle des femmes")

    old = get_tarifs(conn, exercice_id)
    with transaction(conn):
        exercices.upsert_tarif(conn, exercice_id, Sexe.HOMME, tarif_homme)
        exercices.upsert_tarif(conn, exercice_id, Sexe.FEMME, tarif_femme)
        audit.log(
            conn, session.user, Action.TARIFS_MODIF, f"Exercice {exercice.libelle}",
            f"Hommes {_fmt(old.get(Sexe.HOMME, 0))} → {_fmt(tarif_homme)} · "
            f"Femmes {_fmt(old.get(Sexe.FEMME, 0))} → {_fmt(tarif_femme)}",
        )


def get_tarifs(conn: sqlite3.Connection, exercice_id: int) -> dict[Sexe, int]:
    return exercices.get_tarifs(conn, exercice_id)


def list_exercices(conn: sqlite3.Connection) -> list[Exercice]:
    return exercices.list_all(conn)


def default_exercice(conn: sqlite3.Connection, today: date | None = None) -> Exercice | None:
    """Exercice affiché au démarrage : celui qui contient aujourd'hui, sinon
    le dernier ouvert, sinon le plus récent, sinon None (premier lancement)."""
    today = today or date.today()
    all_ = exercices.list_all(conn)
    for exercice in all_:
        if exercice.contains(today):
            return exercice
    open_ = [e for e in all_ if e.is_open]
    if open_:
        return open_[0]
    return all_[0] if all_ else None
def set_funeral_tarifs(conn: sqlite3.Connection, session: Session, exercice_id: int,
                       montant_homme: int, montant_femme: int) -> None:
    """Cotisation funéraire : un montant par sexe, et rien d'autre.
    Ne modifie pas les collectes déjà créées (leur montant est figé à la création)."""
    session.require(Permission.SETTINGS_MANAGE)
    exercice = exercices.get(conn, exercice_id)
    if exercice is None:
        raise ExerciceError("Exercice introuvable.")
    if not exercice.is_open:
        raise ExerciceError(f"L'exercice {exercice.libelle} est clôturé : ses montants ne peuvent plus changer.")
    _check_amount(montant_homme, "Cotisation funéraire des hommes")
    _check_amount(montant_femme, "Cotisation funéraire des femmes")

    old = exercices.get_funeral_tarifs(conn, exercice_id)

    def avant(sexe: Sexe) -> str:
        return _fmt(old[sexe]) if sexe in old else "non défini"

    with transaction(conn):
        exercices.upsert_funeral_tarif(conn, exercice_id, Sexe.HOMME, montant_homme)
        exercices.upsert_funeral_tarif(conn, exercice_id, Sexe.FEMME, montant_femme)
        audit.log(
            conn, session.user, Action.TARIFS_MODIF, f"Exercice {exercice.libelle}",
            f"Cotisation funéraire · Hommes {avant(Sexe.HOMME)} → {_fmt(montant_homme)} · "
            f"Femmes {avant(Sexe.FEMME)} → {_fmt(montant_femme)}",
        )


def get_funeral_tarifs(conn: sqlite3.Connection, exercice_id: int) -> dict[Sexe, int]:
    return exercices.get_funeral_tarifs(conn, exercice_id)