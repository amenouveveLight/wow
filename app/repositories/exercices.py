"""Accès aux données des exercices et de leurs tarifs mensuels (SQL uniquement)."""
from __future__ import annotations

import sqlite3
from datetime import date

from app.models.exercice import Exercice
from app.models.sexe import Sexe


def create(conn: sqlite3.Connection, libelle: str, debut: date, fin: date) -> int:
    cur = conn.execute(
        "INSERT INTO exercices (libelle, date_debut, date_fin) VALUES (?, ?, ?)",
        (libelle, debut.isoformat(), fin.isoformat()),
    )
    return int(cur.lastrowid)


def get(conn: sqlite3.Connection, exercice_id: int) -> Exercice | None:
    row = conn.execute("SELECT * FROM exercices WHERE id = ?", (exercice_id,)).fetchone()
    return Exercice.from_row(row) if row else None


def get_by_libelle(conn: sqlite3.Connection, libelle: str) -> Exercice | None:
    row = conn.execute("SELECT * FROM exercices WHERE libelle = ?", (libelle,)).fetchone()
    return Exercice.from_row(row) if row else None


def list_all(conn: sqlite3.Connection) -> list[Exercice]:
    """Du plus récent au plus ancien."""
    rows = conn.execute("SELECT * FROM exercices ORDER BY date_debut DESC").fetchall()
    return [Exercice.from_row(r) for r in rows]


def upsert_tarif(conn: sqlite3.Connection, exercice_id: int, sexe: Sexe, montant: int) -> None:
    conn.execute(
        "INSERT INTO tarifs_mensuels (exercice_id, sexe, montant) VALUES (?, ?, ?) "
        "ON CONFLICT(exercice_id, sexe) DO UPDATE SET montant = excluded.montant",
        (exercice_id, sexe.value, montant),
    )


def get_tarifs(conn: sqlite3.Connection, exercice_id: int) -> dict[Sexe, int]:
    rows = conn.execute(
        "SELECT sexe, montant FROM tarifs_mensuels WHERE exercice_id = ?", (exercice_id,)
    ).fetchall()
    return {Sexe(r["sexe"]): r["montant"] for r in rows}

def get_for_date(conn: sqlite3.Connection, d: date) -> Exercice | None:
    """L'exercice qui contient cette date (septembre → août), s'il existe."""
    row = conn.execute(
        "SELECT * FROM exercices WHERE date_debut <= ? AND date_fin >= ?",
        (d.isoformat(), d.isoformat()),
    ).fetchone()
    return Exercice.from_row(row) if row else None
def upsert_funeral_tarif(conn: sqlite3.Connection, exercice_id: int, sexe: Sexe, montant: int) -> None:
    conn.execute(
        "INSERT INTO tarifs_funeraires (exercice_id, sexe, montant) VALUES (?, ?, ?) "
        "ON CONFLICT(exercice_id, sexe) DO UPDATE SET montant = excluded.montant",
        (exercice_id, sexe.value, montant),
    )


def get_funeral_tarifs(conn: sqlite3.Connection, exercice_id: int) -> dict[Sexe, int]:
    rows = conn.execute(
        "SELECT sexe, montant FROM tarifs_funeraires WHERE exercice_id = ?", (exercice_id,)
    ).fetchall()
    return {Sexe(r["sexe"]): r["montant"] for r in rows}

def close(conn: sqlite3.Connection, exercice_id: int, date_cloture: date) -> None:
    conn.execute(
        "UPDATE exercices SET statut = 'cloture', date_cloture = ? WHERE id = ?",
        (date_cloture.isoformat(), exercice_id),
    )


def first_open_before(conn: sqlite3.Connection, d: date) -> Exercice | None:
    """Le plus ancien exercice encore ouvert qui commence avant cette date."""
    row = conn.execute(
        "SELECT * FROM exercices WHERE statut = 'ouvert' AND date_debut < ? "
        "ORDER BY date_debut LIMIT 1",
        (d.isoformat(),),
    ).fetchone()
    return Exercice.from_row(row) if row else None