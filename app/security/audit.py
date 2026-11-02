"""Journal d'audit : qui a fait quoi, et quand (lecture et ajout uniquement).

À appeler DANS la transaction de l'opération journalisée :

    with transaction(conn):
        versements.add(conn, ...)
        audit.log(conn, session.user, Action.VERSEMENT_AJOUT, "Carnet 009", "5 000 FCFA")
"""
from __future__ import annotations

import sqlite3

from app.security.session import CurrentUser


class Action:
    CONNEXION = "Connexion"
    ECHEC_CONNEXION = "Échec de connexion"
    DECONNEXION = "Déconnexion"
    MEMBRE_AJOUT = "Ajout d’un membre"
    MEMBRE_MODIF = "Modification d’un membre"
    MEMBRE_DECES = "Membre déclaré décédé"
    MEMBRE_SUPPR = "Suppression d’un membre"
    VERSEMENT_AJOUT = "Enregistrement d’un versement"
    VERSEMENT_MODIF = "Modification d’un versement"
    VERSEMENT_SUPPR = "Suppression d’un versement"
    DECES_AJOUT = "Création d’une collecte funéraire"
    COTISATION_PARALLELE = "Création d’une cotisation parallèle"
    AMENDE_AJOUT = "Enregistrement d’une amende"
    DEPENSE_AJOUT = "Saisie d’une dépense"
    DEPENSE_SUPPR = "Suppression d’une dépense"
    EXPORT = "Export de rapport"
    SAUVEGARDE = "Sauvegarde"
    RESTAURATION = "Restauration d’une sauvegarde"
    CLOTURE = "Clôture d’exercice"
    UTILISATEUR_AJOUT = "Création d’un compte"
    UTILISATEUR_MODIF = "Modification d’un compte"
    TARIFS_MODIF = "Modification des montants"
    EXERCICE_CREATION = "Création d’un exercice"
    CARNET_FORMAT = "Modification du format des numéros de carnet"
    AMENDE_COLLECTE = "Encaissement d’une amende"
    REGLEMENT_ARRIERES = "Règlement d’arriérés"
  

def log(
    conn: sqlite3.Connection,
    user: CurrentUser | None,
    action: str,
    objet: str | None = None,
    detail: str | None = None,
    *,
    identifiant: str | None = None,
) -> int:
    """Ajoute une entrée au journal. Retourne son id.

    - user connu : identité et rôle viennent de la session.
    - user None + identifiant : tentative de connexion d'un compte
      (rôle « inconnu »), ex. identifiant incorrect.
    - user None sans identifiant : action du système (sauvegarde auto).
    """
    if user is not None:
        uid, ident, role = user.id, user.identifiant, user.role.value
    elif identifiant is not None:
        uid, ident, role = None, identifiant, "inconnu"
    else:
        uid, ident, role = None, "système", "système"

    cur = conn.execute(
        "INSERT INTO journal_audit (utilisateur_id, identifiant, role, action, objet, detail) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (uid, ident, role, action, objet, detail),
    )
    return int(cur.lastrowid)


def _where(identifiant, action, date_debut, date_fin, recherche):
    clauses, params = [], []
    if identifiant:
        clauses.append("identifiant = ?")
        params.append(identifiant)
    if action:
        clauses.append("action = ?")
        params.append(action)
    if date_debut:
        clauses.append("date(date_heure) >= date(?)")
        params.append(date_debut)
    if date_fin:
        clauses.append("date(date_heure) <= date(?)")
        params.append(date_fin)
    if recherche:
        clauses.append("(action LIKE ? OR objet LIKE ? OR detail LIKE ?)")
        params.extend([f"%{recherche}%"] * 3)
    return (" WHERE " + " AND ".join(clauses)) if clauses else "", params


def list_entries(
    conn: sqlite3.Connection,
    *,
    identifiant: str | None = None,
    action: str | None = None,
    date_debut: str | None = None,   # AAAA-MM-JJ
    date_fin: str | None = None,
    recherche: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[sqlite3.Row]:
    """Entrées les plus récentes d'abord, avec filtres et pagination."""
    where, params = _where(identifiant, action, date_debut, date_fin, recherche)
    sql = f"SELECT * FROM journal_audit{where} ORDER BY id DESC LIMIT ? OFFSET ?"
    return conn.execute(sql, [*params, limit, offset]).fetchall()


def count_entries(
    conn: sqlite3.Connection,
    *,
    identifiant: str | None = None,
    action: str | None = None,
    date_debut: str | None = None,
    date_fin: str | None = None,
    recherche: str | None = None,
) -> int:
    where, params = _where(identifiant, action, date_debut, date_fin, recherche)
    return conn.execute(f"SELECT COUNT(*) FROM journal_audit{where}", params).fetchone()[0]

    