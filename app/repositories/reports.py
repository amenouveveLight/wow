"""Accès aux données des reports d'exercice (SQL uniquement)."""
from __future__ import annotations

import sqlite3

from app.models.report import Report


def add(conn: sqlite3.Connection, source_id: int | None, cible_id: int, membre_id: int | None,
        type_: str, rubrique: str | None, montant: int,
        exercice_origine_id: int | None = None) -> int:
    """exercice_origine_id : exercice où la dette est née (par défaut, l'exercice qui reporte)."""
    if exercice_origine_id is None and type_ != "solde":
        exercice_origine_id = source_id
    cur = conn.execute(
        "INSERT INTO reports (exercice_source_id, exercice_cible_id, membre_id, type, rubrique, "
        "montant, exercice_origine_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (source_id, cible_id, membre_id, type_, rubrique, montant, exercice_origine_id),
    )
    return int(cur.lastrowid)


def list_for_cible(conn: sqlite3.Connection, cible_id: int) -> list[Report]:
    rows = conn.execute(
        "SELECT * FROM reports WHERE exercice_cible_id = ? ORDER BY id", (cible_id,)
    ).fetchall()
    return [Report.from_row(r) for r in rows]


def totals_by_type(conn: sqlite3.Connection, cible_id: int) -> dict[str, int]:
    rows = conn.execute(
        "SELECT type, SUM(montant) AS total FROM reports WHERE exercice_cible_id = ? GROUP BY type",
        (cible_id,),
    ).fetchall()
    return {r["type"]: int(r["total"]) for r in rows}


def by_member(conn: sqlite3.Connection, cible_id: int, type_: str, rubrique: str) -> dict[int, int]:
    """Reports reçus par l'exercice, par membre, pour un type (dette/avance) et une rubrique."""
    rows = conn.execute(
        "SELECT membre_id, SUM(montant) AS total FROM reports "
        "WHERE exercice_cible_id = ? AND type = ? AND rubrique = ? AND membre_id IS NOT NULL "
        "GROUP BY membre_id",
        (cible_id, type_, rubrique),
    ).fetchall()
    return {r["membre_id"]: int(r["total"]) for r in rows}


def by_member_and_origin(conn: sqlite3.Connection, cible_id: int, type_: str,
                         rubrique: str) -> dict[int, list[tuple[int, int]]]:
    """{membre_id: [(exercice d'origine, montant)]}, du plus ancien au plus récent."""
    rows = conn.execute(
        "SELECT t.membre_id AS membre_id, t.origine AS origine, SUM(t.montant) AS total FROM ("
        "  SELECT membre_id, COALESCE(exercice_origine_id, exercice_source_id) AS origine, montant "
        "  FROM reports WHERE exercice_cible_id = ? AND type = ? AND rubrique = ? "
        "  AND membre_id IS NOT NULL"
        ") t LEFT JOIN exercices o ON o.id = t.origine "
        "GROUP BY t.membre_id, t.origine ORDER BY o.date_debut",
        (cible_id, type_, rubrique),
    ).fetchall()
    result: dict[int, list[tuple[int, int]]] = {}
    for r in rows:
        result.setdefault(r["membre_id"], []).append((r["origine"], int(r["total"])))
    return result


def member_amount(conn: sqlite3.Connection, cible_id: int, membre_id: int, type_: str,
                  rubrique: str) -> int:
    row = conn.execute(
        "SELECT COALESCE(SUM(montant), 0) FROM reports "
        "WHERE exercice_cible_id = ? AND membre_id = ? AND type = ? AND rubrique = ?",
        (cible_id, membre_id, type_, rubrique),
    ).fetchone()
    return int(row[0])


def total(conn: sqlite3.Connection, cible_id: int, type_: str, rubrique: str) -> int:
    row = conn.execute(
        "SELECT COALESCE(SUM(montant), 0) FROM reports "
        "WHERE exercice_cible_id = ? AND type = ? AND rubrique = ?",
        (cible_id, type_, rubrique),
    ).fetchone()
    return int(row[0])


def solde_ouverture(conn: sqlite3.Connection, cible_id: int) -> int:
    """Solde reporté de l'exercice précédent (négatif possible : à ne pas afficher tel quel)."""
    row = conn.execute(
        "SELECT COALESCE(SUM(montant), 0) FROM reports WHERE exercice_cible_id = ? AND type = 'solde'",
        (cible_id,),
    ).fetchone()
    return int(row[0])