"""Règles des décès et des collectes funéraires (cahier des charges §3.4).

Le montant de la cotisation funéraire est fixé selon le sexe, et UNIQUEMENT selon
le sexe : il ne dépend ni du type de décès ni du lien de parenté. Il vient du
tarif funéraire de l'exercice (défini par l'administrateur) et il est figé dans
la collecte à sa création, pour que les décès passés ne changent jamais en silence.
"""
from __future__ import annotations

import sqlite3
from datetime import date

from app.database.connection import transaction
from app.models.deces import MEMBRE, TYPE_LABELS, TYPES, Deces
from app.models.membre import ACTIF
from app.models.sexe import Sexe
from app.models.versement import FUNERAIRE
from app.repositories import deces as deces_repo
from app.repositories import exercices, membres, reports, versements
from app.security import audit
from app.security.audit import Action
from app.security.session import Permission, Session
from app.services import cotisation_funeraire, membre_service
from app.services.membre_service import MembreError


class DecesError(Exception):
    """Règle de gestion des décès non respectée (message affichable)."""


def _fmt(amount: int) -> str:
    return f"{amount:,}".replace(",", "\u00A0") + " FCFA"


def _d(value: date) -> str:
    return value.strftime("%d/%m/%Y")


def creer_collecte(conn: sqlite3.Connection, session: Session, nom_defunt: str, type_deces: str,
                   date_deces: date, membre_defunt_id: int | None = None,
                   membre_endeuille_id: int | None = None, exempter_endeuille: bool = False,
                   today: date | None = None) -> Deces:
    """Crée la collecte d'un décès. Si le défunt est un membre, il passe « décédé ».
    Aucun montant à saisir : il vient du tarif funéraire de l'exercice."""
    session.require(Permission.DEATH_CREATE)
    today = today or date.today()

    if type_deces not in TYPES:
        raise DecesError("Choisissez le type de décès.")
    if not isinstance(date_deces, date):
        raise DecesError("La date du décès est obligatoire.")
    if date_deces > today:
        raise DecesError("La date du décès ne peut pas être dans le futur.")

    defunt = None
    if type_deces == MEMBRE:
        if membre_defunt_id is None:
            raise DecesError("Choisissez le membre décédé.")
        if membre_endeuille_id is not None or exempter_endeuille:
            raise DecesError("Le décès d'un membre n'a pas de membre endeuillé.")
        defunt = membres.get(conn, membre_defunt_id)
        if defunt is None:
            raise DecesError("Membre introuvable.")
        if deces_repo.get_by_membre_defunt(conn, defunt.id):
            raise DecesError(f"Une collecte existe déjà pour {defunt.nom}.")
        if defunt.statut != ACTIF and defunt.date_deces != date_deces:
            raise DecesError(
                f"{defunt.nom} est déjà déclaré décédé le {_d(defunt.date_deces)} : "
                "la date de la collecte doit être la même.")
        nom_defunt = defunt.nom
    else:
        if membre_defunt_id is not None:
            raise DecesError("Le membre décédé ne se choisit que pour le type « membre ».")
        nom_defunt = " ".join((nom_defunt or "").split())
        if len(nom_defunt) < 2:
            raise DecesError("Le nom du défunt est obligatoire.")
        if len(nom_defunt) > 100:
            raise DecesError("Le nom du défunt est trop long (100 caractères maximum).")
        if exempter_endeuille and membre_endeuille_id is None:
            raise DecesError("Choisissez le membre endeuillé à exempter.")

    endeuille = None
    if membre_endeuille_id is not None:
        endeuille = membres.get(conn, membre_endeuille_id)
        if endeuille is None:
            raise DecesError("Membre endeuillé introuvable.")
        if endeuille.statut != ACTIF:
            raise DecesError("Le membre endeuillé doit être actif.")

    exercice = exercices.get_for_date(conn, date_deces)
    if exercice is None:
        raise DecesError("Aucun exercice ne couvre la date du décès. Créez d'abord cet exercice.")
    if not exercice.is_open:
        raise DecesError(f"L'exercice {exercice.libelle} est clôturé : on ne peut plus y ajouter de collecte.")

    tarifs = exercices.get_funeral_tarifs(conn, exercice.id)
    if Sexe.HOMME not in tarifs or Sexe.FEMME not in tarifs:
        raise DecesError(
            f"La cotisation funéraire n'est pas définie pour l'exercice {exercice.libelle}. "
            "L'administrateur doit fixer le montant des hommes et celui des femmes dans les paramètres.")
    montant_homme, montant_femme = tarifs[Sexe.HOMME], tarifs[Sexe.FEMME]

    try:
        with transaction(conn):
            if defunt is not None and defunt.statut == ACTIF:
                membre_service.declare_deceased(conn, session, defunt.id, date_deces, today=today)
            deces_id = deces_repo.create(
                conn, exercice.id, nom_defunt, type_deces, membre_defunt_id, date_deces,
                montant_homme, montant_femme, membre_endeuille_id, bool(exempter_endeuille))
            detail = (f"{TYPE_LABELS[type_deces]} · {_d(date_deces)} · "
                      f"hommes {_fmt(montant_homme)} · femmes {_fmt(montant_femme)}")
            if exempter_endeuille and endeuille is not None:
                detail += f" · {endeuille.nom} exempté"
            audit.log(conn, session.user, Action.DECES_AJOUT, f"Décès — {nom_defunt}", detail)
    except MembreError as exc:
        raise DecesError(str(exc)) from None
    return deces_repo.get(conn, deces_id)


def list_collectes(conn: sqlite3.Connection, exercice_id: int) -> list[Deces]:
    return deces_repo.list_for_exercice(conn, exercice_id)


def releve_funeraire(conn: sqlite3.Connection, membre_id: int,
                     exercice_id: int) -> cotisation_funeraire.FuneralStatement:
    """Cases par décès, dû, dette et avance d'un membre pour un exercice. Les versements
    courants remplissent les décès de l'exercice ; les arriérés se règlent à part."""
    if exercices.get(conn, exercice_id) is None:
        raise DecesError("Exercice introuvable.")
    membre = membres.get(conn, membre_id)
    if membre is None:
        raise DecesError("Membre introuvable.")
    deaths = deces_repo.list_for_exercice(conn, exercice_id)
    paid = versements.total_paid(conn, membre_id, exercice_id, FUNERAIRE, nature="courant")
    arrears_paid = versements.total_paid(conn, membre_id, exercice_id, FUNERAIRE, nature="arriere")
    dette = reports.member_amount(conn, exercice_id, membre_id, "dette", "funeraire")
    avance = reports.member_amount(conn, exercice_id, membre_id, "avance", "funeraire")
    return cotisation_funeraire.build_statement(membre, deaths, paid, dette, avance, arrears_paid)