"""Accès aux données des versements (SQL uniquement)."""
from __future__ import annotations

import sqlite3
from datetime import date

from app.models.versement import Versement


def add(conn: sqlite3.Connection, membre_id: int, exercice_id: int, rubrique: str,
        date_versement: date, montant: int, note: str | None, cree_par: int | None,
        cotisation_parallele_id: int | None = None, nature: str = "courant",
        exercice_origine_id: int | None = None, recu: int | None = None) -> int:
    cur = conn.execute(
        "INSERT INTO versements (membre_id, exercice_id, rubrique, nature, cotisation_parallele_id, "
        "exercice_origine_id, recu, date_versement, montant, note, cree_par) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (membre_id, exercice_id, rubrique, nature, cotisation_parallele_id, exercice_origine_id,
         recu, date_versement.isoformat(), montant, note, cree_par),
    )
    return int(cur.lastrowid)


def get(conn: sqlite3.Connection, versement_id: int) -> Versement | None:
    row = conn.execute("SELECT * FROM versements WHERE id = ?", (versement_id,)).fetchone()
    return Versement.from_row(row) if row else None


def update(conn: sqlite3.Connection, versement_id: int, montant: int,
           date_versement: date, note: str | None) -> None:
    conn.execute(
        "UPDATE versements SET montant = ?, date_versement = ?, note = ? WHERE id = ?",
        (montant, date_versement.isoformat(), note, versement_id),
    )


def delete(conn: sqlite3.Connection, versement_id: int) -> None:
    conn.execute("DELETE FROM versements WHERE id = ?", (versement_id,))


def list_for_member(conn: sqlite3.Connection, membre_id: int, *, exercice_id: int | None = None,
                    rubrique: str | None = None) -> list[Versement]:
    """Les plus récents d'abord."""
    clauses, params = ["membre_id = ?"], [membre_id]
    if exercice_id is not None:
        clauses.append("exercice_id = ?")
        params.append(exercice_id)
    if rubrique is not None:
        clauses.append("rubrique = ?")
        params.append(rubrique)
    sql = ("SELECT * FROM versements WHERE " + " AND ".join(clauses)
           + " ORDER BY date_versement DESC, id DESC")
    return [Versement.from_row(r) for r in conn.execute(sql, params).fetchall()]


def list_for_recu(conn: sqlite3.Connection, recu: int) -> list[Versement]:
    rows = conn.execute("SELECT * FROM versements WHERE recu = ? ORDER BY id", (recu,)).fetchall()
    return [Versement.from_row(r) for r in rows]


def next_recu(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COALESCE(MAX(recu), 0) + 1 FROM versements").fetchone()[0])


def total_paid(conn: sqlite3.Connection, membre_id: int, exercice_id: int, rubrique: str,
               nature: str | None = None) -> int:
    sql = ("SELECT COALESCE(SUM(montant), 0) FROM versements "
           "WHERE membre_id = ? AND exercice_id = ? AND rubrique = ?")
    params: list = [membre_id, exercice_id, rubrique]
    if nature:
        sql += " AND nature = ?"
        params.append(nature)
    return int(conn.execute(sql, params).fetchone()[0])


def totals_by_member(conn: sqlite3.Connection, exercice_id: int, rubrique: str,
                     nature: str | None = None) -> dict[int, int]:
    """Total versé par membre pour un exercice et une rubrique, en une seule requête."""
    sql = ("SELECT membre_id, SUM(montant) AS total FROM versements "
           "WHERE exercice_id = ? AND rubrique = ?")
    params: list = [exercice_id, rubrique]
    if nature:
        sql += " AND nature = ?"
        params.append(nature)
    sql += " GROUP BY membre_id"
    return {r["membre_id"]: int(r["total"]) for r in conn.execute(sql, params).fetchall()}


def total_paid_parallele(conn: sqlite3.Connection, membre_id: int, cotisation_id: int) -> int:
    row = conn.execute(
        "SELECT COALESCE(SUM(montant), 0) FROM versements "
        "WHERE membre_id = ? AND rubrique = 'parallele' AND cotisation_parallele_id = ?",
        (membre_id, cotisation_id),
    ).fetchone()
    return int(row[0])


def totals_by_member_parallele(conn: sqlite3.Connection, cotisation_id: int) -> dict[int, int]:
    """Total versé par membre pour une cotisation parallèle, en une seule requête."""
    rows = conn.execute(
        "SELECT membre_id, SUM(montant) AS total FROM versements "
        "WHERE rubrique = 'parallele' AND cotisation_parallele_id = ? GROUP BY membre_id",
        (cotisation_id,),
    ).fetchall()
    return {r["membre_id"]: int(r["total"]) for r in rows}


def arrears_paid_by_origin(conn: sqlite3.Connection, exercice_id: int, membre_id: int,
                           rubrique: str) -> dict[int, int]:
    """Arriérés d'un membre remboursés dans cet exercice, par exercice d'origine."""
    rows = conn.execute(
        "SELECT exercice_origine_id AS origine, SUM(montant) AS total FROM versements "
        "WHERE exercice_id = ? AND membre_id = ? AND rubrique = ? AND nature = 'arriere' "
        "GROUP BY exercice_origine_id",
        (exercice_id, membre_id, rubrique),
    ).fetchall()
    return {r["origine"]: int(r["total"]) for r in rows}


def arrears_paid(conn: sqlite3.Connection, exercice_id: int, rubrique: str) -> dict[tuple[int, int], int]:
    """Arriérés remboursés dans cet exercice : {(membre_id, exercice d'origine): total}."""
    rows = conn.execute(
        "SELECT membre_id, exercice_origine_id AS origine, SUM(montant) AS total FROM versements "
        "WHERE exercice_id = ? AND rubrique = ? AND nature = 'arriere' "
        "GROUP BY membre_id, exercice_origine_id",
        (exercice_id, rubrique),
    ).fetchall()
    return {(r["membre_id"], r["origine"]): int(r["total"]) for r in rows}


def total_arrears_paid(conn: sqlite3.Connection, exercice_id: int, rubrique: str) -> int:
    row = conn.execute(
        "SELECT COALESCE(SUM(montant), 0) FROM versements "
        "WHERE exercice_id = ? AND rubrique = ? AND nature = 'arriere'",
        (exercice_id, rubrique),
    ).fetchone()
    return int(row[0])