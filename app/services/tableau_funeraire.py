"""Tableau « Cotisations funéraires » : une ligne par membre, une colonne par décès.

Paiements courants imputés aux décès de l'exercice ; arriérés suivis à part.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from app.models.deces import Deces
from app.models.membre import Membre
from app.models.sexe import Sexe
from app.models.versement import FUNERAIRE
from app.repositories import deces as deces_repo
from app.repositories import exercices, membres, reports, versements
from app.services import cotisation_funeraire
from app.services.cotisation_funeraire import FuneralStatement
from app.services.tableau_mensuel import SITUATIONS, Totaux, concerne

_PY_SORTS = {
    "du": lambda l: l.releve.total_due,
    "percu": lambda l: l.releve.cash_total,
    "dette": lambda l: l.releve.total_debt,
    "avance": lambda l: l.releve.advance,
}


class TableauFuneraireError(Exception):
    """Paramètres invalides pour le tableau (message affichable)."""


@dataclass(frozen=True)
class Ligne:
    membre: Membre
    releve: FuneralStatement


@dataclass(frozen=True)
class Page:
    collectes: list[Deces]      # colonnes, du plus ancien au plus récent
    lignes: list[Ligne]
    total: int
    page: Totaux
    general: Totaux


def _totaux(lignes: list[Ligne]) -> Totaux:
    return Totaux(
        membres=len(lignes),
        du=sum(l.releve.total_due for l in lignes),
        percu=sum(l.releve.cash_total for l in lignes),
        dette=sum(l.releve.total_debt for l in lignes),
        avance=sum(l.releve.advance for l in lignes),
        dette_reportee=sum(l.releve.carried_debt for l in lignes),
        avance_reportee=sum(l.releve.carried_advance for l in lignes),
    )


def _situation_ok(releve: FuneralStatement, situation: str) -> bool:
    if situation == "dette":
        return releve.total_debt > 0
    if situation == "avance":
        return releve.advance > 0
    return releve.total_debt == 0 and releve.advance == 0


def tableau(conn: sqlite3.Connection, exercice_id: int, *, search: str | None = None,
            statut: str | None = None, sexe: Sexe | None = None, situation: str | None = None,
            sort: str = "carnet", descending: bool = False,
            limit: int | None = None, offset: int = 0) -> Page:
    exercice = exercices.get(conn, exercice_id)
    if exercice is None:
        raise TableauFuneraireError("Exercice introuvable.")
    if situation is not None and situation not in SITUATIONS:
        raise TableauFuneraireError("Situation inconnue.")

    collectes = deces_repo.list_for_exercice(conn, exercice_id)
    courant = versements.totals_by_member(conn, exercice_id, FUNERAIRE, nature="courant")
    arrieres = versements.totals_by_member(conn, exercice_id, FUNERAIRE, nature="arriere")
    dettes = reports.by_member(conn, exercice_id, "dette", "funeraire")
    avances = reports.by_member(conn, exercice_id, "avance", "funeraire")
    avec_report = set(dettes) | set(avances)

    rows = membres.list_(
        conn, search=(search or "").strip() or None, statut=statut, sexe=sexe,
        sort="carnet" if sort in _PY_SORTS else sort,
        descending=False if sort in _PY_SORTS else descending,
    )
    rows = [m for m in rows if concerne(m, exercice) or m.id in avec_report]
    lignes = [Ligne(m, cotisation_funeraire.build_statement(
        m, collectes, courant.get(m.id, 0), dettes.get(m.id, 0), avances.get(m.id, 0),
        arrieres.get(m.id, 0))) for m in rows]
    if situation:
        lignes = [l for l in lignes if _situation_ok(l.releve, situation)]
    if sort in _PY_SORTS:
        lignes = sorted(lignes, key=_PY_SORTS[sort], reverse=descending)

    visible = lignes[offset:offset + limit] if limit is not None else lignes[offset:]
    return Page(collectes, visible, len(lignes), _totaux(visible), _totaux(lignes))