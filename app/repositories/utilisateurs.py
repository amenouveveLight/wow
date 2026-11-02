"""Accès aux données des utilisateurs (SQL uniquement)."""
from __future__ import annotations

import sqlite3

from app.models.utilisateur import Utilisateur
from app.security.session import Role


def _one(row: sqlite3.Row | None) -> Utilisateur | None:
    return Utilisateur.from_row(row) if row else None


def get_by_identifiant(conn: sqlite3.Connection, identifiant: str) -> Utilisateur | None:
    row = conn.execute(
        "SELECT * FROM utilisateurs WHERE identifiant = ?", (identifiant.strip(),)
    ).fetchone()
    return _one(row)


def get_by_id(conn: sqlite3.Connection, user_id: int) -> Utilisateur | None:
    return _one(conn.execute("SELECT * FROM utilisateurs WHERE id = ?", (user_id,)).fetchone())


def list_all(conn: sqlite3.Connection) -> list[Utilisateur]:
    rows = conn.execute("SELECT * FROM utilisateurs ORDER BY role, nom_complet").fetchall()
    return [Utilisateur.from_row(r) for r in rows]


def count_by_role(conn: sqlite3.Connection, role: Role, *, only_active: bool = False) -> int:
    sql = "SELECT COUNT(*) FROM utilisateurs WHERE role = ?"
    if only_active:
        sql += " AND actif = 1"
    return conn.execute(sql, (role.value,)).fetchone()[0]


def create(conn: sqlite3.Connection, identifiant: str, nom_complet: str,
           password_hash: str, role: Role) -> int:
    """Lève sqlite3.IntegrityError si l'identifiant existe (ou 2e administrateur)."""
    cur = conn.execute(
        "INSERT INTO utilisateurs (identifiant, nom_complet, mot_de_passe_hash, role) "
        "VALUES (?, ?, ?, ?)",
        (identifiant.strip(), nom_complet.strip(), password_hash, role.value),
    )
    return int(cur.lastrowid)


def update_hash(conn: sqlite3.Connection, user_id: int, password_hash: str) -> None:
    conn.execute("UPDATE utilisateurs SET mot_de_passe_hash = ? WHERE id = ?", (password_hash, user_id))


def set_active(conn: sqlite3.Connection, user_id: int, actif: bool) -> None:
    conn.execute("UPDATE utilisateurs SET actif = ? WHERE id = ?", (1 if actif else 0, user_id))


def record_failure(conn: sqlite3.Connection, user_id: int, attempts: int,
                   locked_until: str | None) -> None:
    conn.execute(
        "UPDATE utilisateurs SET tentatives_echouees = ?, verrouille_jusqua = ? WHERE id = ?",
        (attempts, locked_until, user_id),
    )


def reset_failures(conn: sqlite3.Connection, user_id: int) -> None:
    record_failure(conn, user_id, 0, None)