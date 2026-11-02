"""Accès aux données des décès / collectes funéraires (SQL uniquement)."""
from __future__ import annotations

import sqlite3
from datetime import date

from app.models.deces import Deces


def create(conn: sqlite3.Connection, exercice_id: int, nom_defunt: str, type_deces: str,
           membre_defunt_id: int | None, date_deces: date, montant_homme: int,
           montant_femme: int, membre_endeuille_id: int | None, exempter_endeuille: bool) -> int:
    cur = conn.execute(
        "INSERT INTO deces (exercice_id, nom_defunt, type_deces, membre_defunt_id, date_deces, "
        "montant_homme, montant_femme, membre_endeuille_id, exempter_endeuille) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (exercice_id, nom_defunt, type_deces, membre_defunt_id, date_deces.isoformat(),
         montant_homme, montant_femme, membre_endeuille_id, 1 if exempter_endeuille else 0),
    )
    return int(cur.lastrowid)


def get(conn: sqlite3.Connection, deces_id: int) -> Deces | None:
    row = conn.execute("SELECT * FROM deces WHERE id = ?", (deces_id,)).fetchone()
    return Deces.from_row(row) if row else None


def get_by_membre_defunt(conn: sqlite3.Connection, membre_id: int) -> Deces | None:
    row = conn.execute("SELECT * FROM deces WHERE membre_defunt_id = ?", (membre_id,)).fetchone()
    return Deces.from_row(row) if row else None


def list_for_exercice(conn: sqlite3.Connection, exercice_id: int) -> list[Deces]:
    """Du plus ancien au plus récent (ordre d'imputation des versements)."""
    rows = conn.execute(
        "SELECT * FROM deces WHERE exercice_id = ? ORDER BY date_deces, id", (exercice_id,)
    ).fetchall()
    return [Deces.from_row(r) for r in rows]