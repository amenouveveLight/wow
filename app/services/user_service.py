"""Gestion des comptes (cahier des charges : 1 administrateur, 3 secrétaires)."""
from __future__ import annotations

import re
import sqlite3

from app.database.connection import transaction
from app.models.utilisateur import Utilisateur
from app.repositories import utilisateurs
from app.security import audit
from app.security.audit import Action
from app.security.passwords import (
    PasswordPolicyError, hash_password, validate_policy, verify_password,
)
from app.security.session import Permission, Role, Session

MAX_SECRETAIRES = 3
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,29}$")


class UserError(Exception):
    """Règle de gestion des comptes non respectée (message affichable)."""


def _check_password(password: str) -> None:
    try:
        validate_policy(password)
    except PasswordPolicyError as exc:
        raise UserError(str(exc)) from None


def _get(conn: sqlite3.Connection, user_id: int) -> Utilisateur:
    user = utilisateurs.get_by_id(conn, user_id)
    if user is None:
        raise UserError("Compte introuvable.")
    return user


def list_users(conn: sqlite3.Connection, session: Session) -> list[Utilisateur]:
    session.require(Permission.USERS_MANAGE)
    return utilisateurs.list_all(conn)


def creer_secretaire(conn: sqlite3.Connection, session: Session, identifiant: str,
                     nom_complet: str, password: str) -> Utilisateur:
    session.require(Permission.USERS_MANAGE)
    ident = (identifiant or "").strip().lower()
    if not _ID_RE.match(ident):
        raise UserError("Identifiant invalide : 3 à 30 caractères, lettres minuscules, "
                        "chiffres, « . », « _ » ou « - ».")
    nom = " ".join((nom_complet or "").split())
    if len(nom) < 2:
        raise UserError("Le nom complet est obligatoire (2 caractères minimum).")
    if len(nom) > 100:
        raise UserError("Le nom complet est trop long (100 caractères maximum).")
    _check_password(password)
    if utilisateurs.get_by_identifiant(conn, ident):
        raise UserError("Cet identifiant est déjà utilisé.")
    if utilisateurs.count_by_role(conn, Role.SECRETAIRE, only_active=True) >= MAX_SECRETAIRES:
        raise UserError(f"Le nombre maximum de secrétaires actifs ({MAX_SECRETAIRES}) est atteint. "
                        "Désactivez-en un d'abord.")
    with transaction(conn):
        user_id = utilisateurs.create(conn, ident, nom, hash_password(password), Role.SECRETAIRE)
        audit.log(conn, session.user, Action.UTILISATEUR_AJOUT, ident, f"{nom} · secrétaire")
    return utilisateurs.get_by_id(conn, user_id)


def reinitialiser_mot_de_passe(conn: sqlite3.Connection, session: Session, user_id: int,
                               nouveau: str) -> None:
    """Administrateur : définit un nouveau mot de passe et déverrouille le compte."""
    session.require(Permission.USERS_MANAGE)
    user = _get(conn, user_id)
    _check_password(nouveau)
    with transaction(conn):
        utilisateurs.update_hash(conn, user.id, hash_password(nouveau))
        utilisateurs.reset_failures(conn, user.id)
        audit.log(conn, session.user, Action.UTILISATEUR_MODIF, user.identifiant,
                  "Mot de passe réinitialisé")


def changer_mon_mot_de_passe(conn: sqlite3.Connection, session: Session, ancien: str,
                             nouveau: str) -> None:
    """Tout utilisateur connecté, sur son propre compte, avec son mot de passe actuel."""
    user = _get(conn, session.user.id)
    if not verify_password(ancien or "", user.mot_de_passe_hash):
        raise UserError("Le mot de passe actuel est incorrect.")
    if nouveau == ancien:
        raise UserError("Le nouveau mot de passe doit être différent de l'ancien.")
    _check_password(nouveau)
    with transaction(conn):
        utilisateurs.update_hash(conn, user.id, hash_password(nouveau))
        audit.log(conn, session.user, Action.UTILISATEUR_MODIF, user.identifiant,
                  "Mot de passe modifié par son titulaire")


def set_actif(conn: sqlite3.Connection, session: Session, user_id: int, actif: bool) -> Utilisateur:
    session.require(Permission.USERS_MANAGE)
    user = _get(conn, user_id)
    if user.role is Role.ADMINISTRATEUR:
        raise UserError("Le compte administrateur ne peut pas être désactivé.")
    if user.actif == actif:
        raise UserError("Ce compte est déjà " + ("actif." if actif else "désactivé."))
    if actif and utilisateurs.count_by_role(conn, Role.SECRETAIRE, only_active=True) >= MAX_SECRETAIRES:
        raise UserError(f"Le nombre maximum de secrétaires actifs ({MAX_SECRETAIRES}) est atteint. "
                        "Désactivez-en un d'abord.")
    with transaction(conn):
        utilisateurs.set_active(conn, user.id, actif)
        audit.log(conn, session.user, Action.UTILISATEUR_MODIF, user.identifiant,
                  "Compte réactivé" if actif else "Compte désactivé")
    return utilisateurs.get_by_id(conn, user.id)