"""Accès aux données des encaissements d'amendes (SQL uniquement)."""
from __future__ import annotations

import sqlite3
from datetime import date


def add(conn: sqlite3.Connection, amende_id: int, montant: int, date_encaissement: date,
        cree_par: int | None) -> int:
    cur = conn.execute(
        "INSERT INTO encaissements_amendes (amende_id, montant, date_encaissement, cree_par) "
        "VALUES (?, ?, ?, ?)",
        (amende_id, montant, date_encaissement.isoformat(), cree_par),
    )
    return int(cur.lastrowid)


def total(conn: sqlite3.Connection, amende_id: int) -> int:
    row = conn.execute(
        "SELECT COALESCE(SUM(montant), 0) FROM encaissements_amendes WHERE amende_id = ?",
        (amende_id,),
    ).fetchone()
    return int(row[0])