"""Accès aux données des cotisations parallèles (SQL uniquement)."""
from __future__ import annotations

import sqlite3
from datetime import date

from app.models.cotisation_parallele import CotisationParallele


def create(conn: sqlite3.Connection, exercice_id: int, nom: str, date_debut: date,
           date_fin: date, montant_homme: int, montant_femme: int) -> int:
    cur = conn.execute(
        "INSERT INTO cotisations_paralleles (exercice_id, nom, date_debut, date_fin, "
        "montant_homme, montant_femme) VALUES (?, ?, ?, ?, ?, ?)",
        (exercice_id, nom, date_debut.isoformat(), date_fin.isoformat(), montant_homme, montant_femme),
    )
    return int(cur.lastrowid)


def get(conn: sqlite3.Connection, cotisation_id: int) -> CotisationParallele | None:
    row = conn.execute("SELECT * FROM cotisations_paralleles WHERE id = ?", (cotisation_id,)).fetchone()
    return CotisationParallele.from_row(row) if row else None


def get_by_nom(conn: sqlite3.Connection, exercice_id: int, nom: str) -> CotisationParallele | None:
    row = conn.execute(
        "SELECT * FROM cotisations_paralleles WHERE exercice_id = ? AND nom = ? COLLATE NOCASE",
        (exercice_id, nom),
    ).fetchone()
    return CotisationParallele.from_row(row) if row else None


def list_for_exercice(conn: sqlite3.Connection, exercice_id: int) -> list[CotisationParallele]:
    rows = conn.execute(
        "SELECT * FROM cotisations_paralleles WHERE exercice_id = ? ORDER BY date_debut, id",
        (exercice_id,),
    ).fetchall()
    return [CotisationParallele.from_row(r) for r in rows]