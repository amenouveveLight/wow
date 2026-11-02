"""Tableau d'une cotisation parallèle : une ligne par membre concerné."""
from __future__ import annotations

import calendar
import sqlite3
from dataclasses import dataclass
from datetime import date

from app.models.cotisation_parallele import CotisationParallele
from app.models.membre import Membre
from app.models.sexe import Sexe
from app.repositories import cotisations_paralleles, membres, versements
from app.services import cotisation_parallele
from app.services.cotisation_parallele import ParallelStatement
from app.services.tableau_mensuel import SITUATIONS, Totaux

_PY_SORTS = {
    "du": lambda l: l.releve.due,
    "percu": lambda l: l.releve.paid,
    "dette": lambda l: l.releve.debt,
    "avance": lambda l: l.releve.advance,
}


class TableauParalleleError(Exception):
    """Paramètres invalides pour le tableau (message affichable)."""


@dataclass(frozen=True)
class Ligne:
    membre: Membre
    releve: ParallelStatement


@dataclass(frozen=True)
class Page:
    cotisation: CotisationParallele
    lignes: list[Ligne]
    total: int
    page: Totaux
    general: Totaux


def _totaux(lignes: list[Ligne]) -> Totaux:
    return Totaux(
        membres=len(lignes),
        du=sum(l.releve.due for l in lignes),
        percu=sum(l.releve.paid for l in lignes),
        dette=sum(l.releve.debt for l in lignes),
        avance=sum(l.releve.advance for l in lignes),
    )


def _situation_ok(releve: ParallelStatement, situation: str) -> bool:
    if situation == "dette":
        return releve.debt > 0
    if situation == "avance":
        return releve.advance > 0
    return releve.debt == 0 and releve.advance == 0


def _lignes(conn: sqlite3.Connection, cotisation: CotisationParallele, *, search=None,
            statut=None, sexe: Sexe | None = None) -> list[Ligne]:
    fin = cotisation.date_fin
    fin_du_mois = date(fin.year, fin.month, calendar.monthrange(fin.year, fin.month)[1])
    paid = versements.totals_by_member_parallele(conn, cotisation.id)
    rows = membres.list_(
        conn, search=(search or "").strip() or None, statut=statut, sexe=sexe,
        concerned=(cotisation.date_debut, fin_du_mois),
    )
    lignes = [Ligne(m, cotisation_parallele.build_statement(m, cotisation, paid.get(m.id, 0)))
              for m in rows]
    return [l for l in lignes if l.releve.concerned]


def tableau(conn: sqlite3.Connection, cotisation_id: int, *, search: str | None = None,
            statut: str | None = None, sexe: Sexe | None = None, situation: str | None = None,
            sort: str = "carnet", descending: bool = False,
            limit: int | None = None, offset: int = 0) -> Page:
    cotisation = cotisations_paralleles.get(conn, cotisation_id)
    if cotisation is None:
        raise TableauParalleleError("Cotisation parallèle introuvable.")
    if situation is not None and situation not in SITUATIONS:
        raise TableauParalleleError("Situation inconnue.")

    lignes = _lignes(conn, cotisation, search=search, statut=statut, sexe=sexe)
    if situation:
        lignes = [l for l in lignes if _situation_ok(l.releve, situation)]
    if sort in _PY_SORTS:
        lignes = sorted(lignes, key=_PY_SORTS[sort], reverse=descending)
    elif sort == "nom":
        lignes = sorted(lignes, key=lambda l: l.membre.nom.lower(), reverse=descending)
    elif descending:
        lignes = list(reversed(lignes))

    visible = lignes[offset:offset + limit] if limit is not None else lignes[offset:]
    return Page(cotisation, visible, len(lignes), _totaux(visible), _totaux(lignes))


def resume(conn: sqlite3.Connection, cotisation_id: int) -> Totaux:
    """Attendu, perçu, dette et avance de toute la cotisation (tableau récapitulatif)."""
    cotisation = cotisations_paralleles.get(conn, cotisation_id)
    if cotisation is None:
        raise TableauParalleleError("Cotisation parallèle introuvable.")
    return _totaux(_lignes(conn, cotisation))


def list_resumes(conn: sqlite3.Connection, exercice_id: int) -> list[tuple[CotisationParallele, Totaux]]:
    return [(c, resume(conn, c.id)) for c in cotisations_paralleles.list_for_exercice(conn, exercice_id)]