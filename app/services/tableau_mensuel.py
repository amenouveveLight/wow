"""Tableau « Cotisations mensuelles » : une ligne par membre, 12 mois, totaux.

Les calculs viennent de cotisation_mensuelle (déjà testé). Les dettes et avances
reportées de l'exercice précédent sont prises en compte (imputation « plus
ancienne dette d'abord »). Un membre qui n'est plus concerné par l'exercice mais
garde une dette reportée y figure quand même.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from app.models.exercice import Exercice
from app.models.membre import Membre
from app.models.sexe import Sexe
from app.models.versement import MENSUELLE
from app.repositories import exercices, membres, reports, versements
from app.services import cotisation_mensuelle
from app.services.cotisation_mensuelle import MonthlyStatement

SITUATIONS = ("dette", "avance", "a_jour")

_PY_SORTS = {
    "du": lambda l: l.releve.total_due,
    "percu": lambda l: l.releve.total_paid,
    "dette": lambda l: l.releve.total_debt,
    "avance": lambda l: l.releve.advance,
}


class TableauError(Exception):
    """Données manquantes pour construire le tableau (message affichable)."""


@dataclass(frozen=True)
class Ligne:
    membre: Membre
    releve: MonthlyStatement


@dataclass(frozen=True)
class Totaux:
    membres: int
    du: int
    percu: int
    dette: int                  # tout ce qui reste dû (exercice + dettes reportées restantes)
    avance: int
    dette_reportee: int = 0     # dettes reportées reçues de l'exercice précédent
    avance_reportee: int = 0    # avances reportées reçues de l'exercice précédent


@dataclass(frozen=True)
class Page:
    lignes: list[Ligne]
    total: int          # nombre de membres après filtres
    page: Totaux        # totaux des lignes affichées
    general: Totaux     # totaux de tout le résultat filtré


def concerne(membre: Membre, exercice: Exercice) -> bool:
    """Adhésion au plus tard à la fin de l'exercice, et pas décédé avant son début."""
    return (membre.date_adhesion <= exercice.date_fin
            and (membre.date_deces is None or membre.date_deces >= exercice.date_debut))


def _totaux(lignes: list[Ligne]) -> Totaux:
    return Totaux(
        membres=len(lignes),
        du=sum(l.releve.total_due for l in lignes),
        percu=sum(l.releve.total_paid for l in lignes),
        dette=sum(l.releve.total_debt for l in lignes),
        avance=sum(l.releve.advance for l in lignes),
        dette_reportee=sum(l.releve.carried_debt for l in lignes),
        avance_reportee=sum(l.releve.carried_advance for l in lignes),
    )


def _situation_ok(releve: MonthlyStatement, situation: str) -> bool:
    if situation == "dette":
        return releve.total_debt > 0
    if situation == "avance":
        return releve.advance > 0
    return releve.total_debt == 0 and releve.advance == 0      # « a_jour »


def tableau(conn: sqlite3.Connection, exercice_id: int, *, search: str | None = None,
            statut: str | None = None, sexe: Sexe | None = None, situation: str | None = None,
            sort: str = "carnet", descending: bool = False,
            limit: int | None = None, offset: int = 0) -> Page:
    exercice = exercices.get(conn, exercice_id)
    if exercice is None:
        raise TableauError("Exercice introuvable.")
    if situation is not None and situation not in SITUATIONS:
        raise TableauError("Situation inconnue.")
    tarifs = exercices.get_tarifs(conn, exercice_id)
    paid = versements.totals_by_member(conn, exercice_id, MENSUELLE)
    dettes = reports.by_member(conn, exercice_id, "dette", "mensuelle")
    avances = reports.by_member(conn, exercice_id, "avance", "mensuelle")
    avec_report = set(dettes) | set(avances)

    rows = membres.list_(
        conn, search=(search or "").strip() or None, statut=statut, sexe=sexe,
        sort="carnet" if sort in _PY_SORTS else sort,
        descending=False if sort in _PY_SORTS else descending,
    )
    rows = [m for m in rows if concerne(m, exercice) or m.id in avec_report]

    lignes: list[Ligne] = []
    for membre in rows:
        tarif = tarifs.get(membre.sexe)
        if tarif is None:
            raise TableauError(
                f"Aucun montant mensuel défini pour les {membre.sexe.label.lower()}s en {exercice.libelle}.")
        releve = cotisation_mensuelle.monthly_statement(
            membre.date_adhesion, membre.date_deces, exercice.months, tarif,
            paid.get(membre.id, 0), dettes.get(membre.id, 0), avances.get(membre.id, 0))
        lignes.append(Ligne(membre, releve))

    if situation:
        lignes = [l for l in lignes if _situation_ok(l.releve, situation)]
    if sort in _PY_SORTS:
        lignes = sorted(lignes, key=_PY_SORTS[sort], reverse=descending)

    visible = lignes[offset:offset + limit] if limit is not None else lignes[offset:]
    return Page(visible, len(lignes), _totaux(visible), _totaux(lignes))