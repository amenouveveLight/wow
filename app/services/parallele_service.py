"""Définition des cotisations parallèles (cahier des charges §3.5)."""
from __future__ import annotations

import sqlite3
from datetime import date

from app.database.connection import transaction
from app.models.cotisation_parallele import CotisationParallele
from app.repositories import cotisations_paralleles, exercices, membres, versements
from app.security import audit
from app.security.audit import Action
from app.security.session import Permission, Session
from app.services import cotisation_parallele


class ParalleleError(Exception):
    """Règle de gestion des cotisations parallèles non respectée (message affichable)."""


def _fmt(amount: int) -> str:
    return f"{amount:,}".replace(",", "\u00A0") + " FCFA"


def _d(value: date) -> str:
    return value.strftime("%d/%m/%Y")


def _check_amount(value, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ParalleleError(f"{label} : entrez un montant entier positif ou nul (en FCFA).")


def creer_cotisation(conn: sqlite3.Connection, session: Session, nom: str, date_debut: date,
                     date_fin: date, montant_homme: int, montant_femme: int) -> CotisationParallele:
    """Administrateur uniquement. La période doit tenir dans un seul exercice."""
    session.require(Permission.PARALLEL_DEFINE)
    nom = " ".join((nom or "").split())
    if len(nom) < 2:
        raise ParalleleError("Le nom de la cotisation est obligatoire (2 caractères minimum).")
    if len(nom) > 100:
        raise ParalleleError("Le nom de la cotisation est trop long (100 caractères maximum).")
    if not isinstance(date_debut, date) or not isinstance(date_fin, date):
        raise ParalleleError("Les dates de début et de fin sont obligatoires.")
    if date_debut > date_fin:
        raise ParalleleError("La date de fin ne peut pas précéder la date de début.")
    _check_amount(montant_homme, "Montant des hommes")
    _check_amount(montant_femme, "Montant des femmes")

    exercice = exercices.get_for_date(conn, date_debut)
    if exercice is None:
        raise ParalleleError("Aucun exercice ne couvre la date de début. Créez d'abord cet exercice.")
    if date_fin > exercice.date_fin:
        raise ParalleleError(
            f"La période doit tenir dans un seul exercice : l'exercice {exercice.libelle} "
            f"se termine le {_d(exercice.date_fin)}.")
    if not exercice.is_open:
        raise ParalleleError(f"L'exercice {exercice.libelle} est clôturé : on ne peut plus y ajouter de cotisation.")
    if cotisations_paralleles.get_by_nom(conn, exercice.id, nom):
        raise ParalleleError(f"Une cotisation « {nom} » existe déjà dans l'exercice {exercice.libelle}.")

    with transaction(conn):
        cotisation_id = cotisations_paralleles.create(
            conn, exercice.id, nom, date_debut, date_fin, montant_homme, montant_femme)
        audit.log(conn, session.user, Action.COTISATION_PARALLELE, f"Cotisation — {nom}",
                  f"{_d(date_debut)} → {_d(date_fin)} · hommes {_fmt(montant_homme)} · "
                  f"femmes {_fmt(montant_femme)} · exercice {exercice.libelle}")
    return cotisations_paralleles.get(conn, cotisation_id)


def get_cotisation(conn: sqlite3.Connection, cotisation_id: int) -> CotisationParallele | None:
    return cotisations_paralleles.get(conn, cotisation_id)


def list_cotisations(conn: sqlite3.Connection, exercice_id: int) -> list[CotisationParallele]:
    return cotisations_paralleles.list_for_exercice(conn, exercice_id)


def releve_parallele(conn: sqlite3.Connection, membre_id: int,
                     cotisation_id: int) -> cotisation_parallele.ParallelStatement:
    membre = membres.get(conn, membre_id)
    if membre is None:
        raise ParalleleError("Membre introuvable.")
    cotisation = cotisations_paralleles.get(conn, cotisation_id)
    if cotisation is None:
        raise ParalleleError("Cotisation parallèle introuvable.")
    paid = versements.total_paid_parallele(conn, membre_id, cotisation_id)
    return cotisation_parallele.build_statement(membre, cotisation, paid)