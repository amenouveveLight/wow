"""Accès aux données des amendes (SQL uniquement)."""
from __future__ import annotations

import sqlite3
from datetime import date

from app.models.amende import IMPAYEE, PARTIELLE, PAYEE, Amende, AmendeLigne

_FROM = "FROM amendes a JOIN membres m ON m.id = a.membre_id"

_STATUT_SQL = {
    PAYEE: "a.montant_collecte >= a.montant_attendu",
    PARTIELLE: "a.montant_collecte > 0 AND a.montant_collecte < a.montant_attendu",
    IMPAYEE: "a.montant_collecte = 0 AND a.montant_attendu > 0",
}


def create(conn: sqlite3.Connection, exercice_id: int, membre_id: int, nom: str, libelle: str,
           date_amende: date, montant_attendu: int, montant_collecte: int,
           cree_par: int | None) -> int:
    cur = conn.execute(
        "INSERT INTO amendes (exercice_id, membre_id, nom, libelle, date_amende, "
        "montant_attendu, montant_collecte, cree_par) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (exercice_id, membre_id, nom, libelle, date_amende.isoformat(), montant_attendu,
         montant_collecte, cree_par),
    )
    return int(cur.lastrowid)


def get(conn: sqlite3.Connection, amende_id: int) -> Amende | None:
    row = conn.execute("SELECT * FROM amendes WHERE id = ?", (amende_id,)).fetchone()
    return Amende.from_row(row) if row else None


def add_collecte(conn: sqlite3.Connection, amende_id: int, montant: int) -> None:
    conn.execute(
        "UPDATE amendes SET montant_collecte = montant_collecte + ? WHERE id = ?",
        (montant, amende_id),
    )


def _where(exercice_id: int, search: str | None, statut: str | None, membre_id: int | None):
    clauses, params = ["a.exercice_id = ?"], [exercice_id]
    if membre_id is not None:
        clauses.append("a.membre_id = ?")
        params.append(membre_id)
    if search:
        clauses.append("(a.nom LIKE ? OR a.libelle LIKE ? OR m.nom LIKE ? OR m.numero_carnet LIKE ?)")
        params += [f"%{search}%"] * 4
    if statut:
        clauses.append(f"({_STATUT_SQL[statut]})")
    return " WHERE " + " AND ".join(clauses), params


def list_(conn: sqlite3.Connection, exercice_id: int, *, search: str | None = None,
          statut: str | None = None, membre_id: int | None = None,
          limit: int | None = None, offset: int = 0) -> list[AmendeLigne]:
    where, params = _where(exercice_id, search, statut, membre_id)
    sql = (f"SELECT a.*, m.nom AS membre_nom, m.numero_carnet AS numero_carnet {_FROM}{where} "
           "ORDER BY a.date_amende DESC, a.id DESC")
    if limit is not None:
        sql += " LIMIT ? OFFSET ?"
        params += [limit, offset]
    return [AmendeLigne(Amende.from_row(r), r["membre_nom"], r["numero_carnet"])
            for r in conn.execute(sql, params).fetchall()]


def count(conn: sqlite3.Connection, exercice_id: int, *, search: str | None = None,
          statut: str | None = None, membre_id: int | None = None) -> int:
    where, params = _where(exercice_id, search, statut, membre_id)
    return conn.execute(f"SELECT COUNT(*) {_FROM}{where}", params).fetchone()[0]


def totals(conn: sqlite3.Connection, exercice_id: int, *, search: str | None = None,
           statut: str | None = None, membre_id: int | None = None) -> tuple[int, int, int]:
    """(attendu, collecté, manque à gagner)."""
    where, params = _where(exercice_id, search, statut, membre_id)
    row = conn.execute(
        "SELECT COALESCE(SUM(a.montant_attendu), 0), COALESCE(SUM(a.montant_collecte), 0), "
        f"COALESCE(SUM(MAX(a.montant_attendu - a.montant_collecte, 0)), 0) {_FROM}{where}",
        params,
    ).fetchone()
    return int(row[0]), int(row[1]), int(row[2])