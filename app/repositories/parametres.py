"""Accès à la table des paramètres généraux (clé / valeur)."""
from __future__ import annotations

import sqlite3


def get(conn: sqlite3.Connection, cle: str, default: str | None = None) -> str | None:
    row = conn.execute("SELECT valeur FROM parametres WHERE cle = ?", (cle,)).fetchone()
    return row["valeur"] if row else default


def set_(conn: sqlite3.Connection, cle: str, valeur: str) -> None:
    conn.execute(
        "INSERT INTO parametres (cle, valeur) VALUES (?, ?) "
        "ON CONFLICT(cle) DO UPDATE SET valeur = excluded.valeur",
        (cle, valeur),
    )