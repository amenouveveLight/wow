"""Accès aux données des membres (SQL uniquement)."""
from __future__ import annotations

import sqlite3
from datetime import date

from app.models.membre import Membre
from app.models.sexe import Sexe

_SORTS = {
    "carnet": "CASE WHEN numero_carnet GLOB '[0-9]*' THEN CAST(numero_carnet AS INTEGER) END {d}, numero_carnet {d}",
    "nom": "nom COLLATE NOCASE {d}, numero_carnet",
    "adhesion": "date_adhesion {d}, numero_carnet",
}


def create(conn: sqlite3.Connection, numero_carnet: str, nom: str, sexe: Sexe,
           date_adhesion: date) -> int:
    """Lève sqlite3.IntegrityError si le numéro de carnet existe déjà."""
    cur = conn.execute(
        "INSERT INTO membres (numero_carnet, nom, sexe, date_adhesion) VALUES (?, ?, ?, ?)",
        (numero_carnet, nom, sexe.value, date_adhesion.isoformat()),
    )
    return int(cur.lastrowid)


def update(conn: sqlite3.Connection, membre_id: int, nom: str, sexe: Sexe,
           date_adhesion: date) -> None:
    conn.execute(
        "UPDATE membres SET nom = ?, sexe = ?, date_adhesion = ? WHERE id = ?",
        (nom, sexe.value, date_adhesion.isoformat(), membre_id),
    )


def set_deceased(conn: sqlite3.Connection, membre_id: int, date_deces: date) -> None:
    conn.execute(
        "UPDATE membres SET statut = 'decede', date_deces = ? WHERE id = ?",
        (date_deces.isoformat(), membre_id),
    )


def delete(conn: sqlite3.Connection, membre_id: int) -> None:
    """Lève sqlite3.IntegrityError si le membre a un historique."""
    conn.execute("DELETE FROM membres WHERE id = ?", (membre_id,))


def get(conn: sqlite3.Connection, membre_id: int) -> Membre | None:
    row = conn.execute("SELECT * FROM membres WHERE id = ?", (membre_id,)).fetchone()
    return Membre.from_row(row) if row else None


def get_by_carnet(conn: sqlite3.Connection, numero_carnet: str) -> Membre | None:
    row = conn.execute("SELECT * FROM membres WHERE numero_carnet = ?", (numero_carnet,)).fetchone()
    return Membre.from_row(row) if row else None


def _where(search: str | None, statut: str | None, sexe: Sexe | None,
           concerned: tuple[date, date] | None = None):
    clauses, params = [], []
    if search:
        clauses.append("(nom LIKE ? OR numero_carnet LIKE ?)")
        params += [f"%{search}%", f"%{search}%"]
    if statut:
        clauses.append("statut = ?")
        params.append(statut)
    if sexe:
        clauses.append("sexe = ?")
        params.append(sexe.value)
    if concerned:
        debut, fin = concerned
        # adhéré au plus tard à la fin de la période, et pas décédé avant son début
        clauses.append("date_adhesion <= ? AND (date_deces IS NULL OR date_deces >= ?)")
        params += [fin.isoformat(), debut.isoformat()]
    return (" WHERE " + " AND ".join(clauses)) if clauses else "", params


def list_(conn: sqlite3.Connection, *, search: str | None = None, statut: str | None = None,
          sexe: Sexe | None = None, concerned: tuple[date, date] | None = None,
          sort: str = "carnet", descending: bool = False,
          limit: int | None = None, offset: int = 0) -> list[Membre]:
    where, params = _where(search, statut, sexe, concerned)
    order = _SORTS.get(sort, _SORTS["carnet"]).format(d="DESC" if descending else "ASC")
    sql = f"SELECT * FROM membres{where} ORDER BY {order}"
    if limit is not None:
        sql += " LIMIT ? OFFSET ?"
        params += [limit, offset]
    return [Membre.from_row(r) for r in conn.execute(sql, params).fetchall()]


def count(conn: sqlite3.Connection, *, search: str | None = None, statut: str | None = None,
          sexe: Sexe | None = None, concerned: tuple[date, date] | None = None) -> int:
    where, params = _where(search, statut, sexe, concerned)
    return conn.execute(f"SELECT COUNT(*) FROM membres{where}", params).fetchone()[0]


def all_carnets(conn: sqlite3.Connection) -> list[str]:
    return [r[0] for r in conn.execute("SELECT numero_carnet FROM membres")]