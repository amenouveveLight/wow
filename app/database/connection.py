"""Connexion SQLite et gestion des transactions.

Seul module autorisé à ouvrir la base. Les repositories reçoivent une
connexion et n'ont pas à connaître le chemin du fichier.
"""
from __future__ import annotations

import itertools
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.config import DB_PATH, ensure_directories

_savepoint_ids = itertools.count(1)


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Ouvre une connexion configurée.

    - isolation_level=None : aucune transaction implicite ; seules celles
      ouvertes par transaction() existent
    - foreign_keys : refuse les références orphelines (ex. versement sans membre)
    - row_factory  : accès aux colonnes par nom (row["nom"])
    - journal WAL  : plus robuste en cas de coupure de courant
    """
    ensure_directories()
    conn = sqlite3.connect(str(db_path or DB_PATH), timeout=10, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Regroupe plusieurs écritures : tout est validé, ou tout est annulé.

    Imbriquable : si une transaction est déjà ouverte, on utilise un SAVEPOINT.
    En cas d'erreur interne, seul le travail du bloc interne est annulé.

        with transaction(conn):
            versements.add(conn, ...)
            audit.log(conn, ...)
    """
    if conn.in_transaction:
        name = f"sp_{next(_savepoint_ids)}"
        conn.execute(f"SAVEPOINT {name}")
        try:
            yield conn
        except Exception:
            conn.execute(f"ROLLBACK TO {name}")
            conn.execute(f"RELEASE {name}")
            raise
        else:
            conn.execute(f"RELEASE {name}")
        return

    conn.execute("BEGIN")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise