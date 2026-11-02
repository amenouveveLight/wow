"""Sauvegarde, restauration et contrôle d'intégrité (cahier des charges §4 et §4.1).

- Copies faites avec l'API de sauvegarde de SQLite (cohérentes même en cours d'usage),
  vérifiées avant d'être validées.
- Sauvegarde automatique : on conserve les 30 dernières copies automatiques.
  Les copies manuelles et de sécurité ne sont jamais supprimées automatiquement.
- Restauration : copie de sécurité de la base actuelle, puis remplacement.
"""
from __future__ import annotations

import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.config import BACKUP_DIR, DB_PATH
from app.database.connection import get_connection, transaction
from app.database.schema import LATEST_VERSION, migrate
from app.security import audit
from app.security.audit import Action
from app.security.session import Permission, Session

KEEP_AUTOMATIC = 30
MANUELLE, AUTOMATIQUE, SECURITE = "manuelle", "automatique", "securite"
_CODES = {MANUELLE: "m", AUTOMATIQUE: "a", SECURITE: "s"}
_KINDS = {code: kind for kind, code in _CODES.items()}
_NAME_RE = re.compile(r"^association_(\d{8})_(\d{6})_([mas])\.db$")
_TABLES_REQUISES = ("membres", "journal_audit", "versements")


class BackupError(Exception):
    """Sauvegarde ou restauration impossible (message affichable)."""


@dataclass(frozen=True)
class Sauvegarde:
    path: Path
    kind: str            # MANUELLE | AUTOMATIQUE | SECURITE
    created: datetime
    size: int

    @property
    def name(self) -> str:
        return self.path.name


def _size_label(size: int) -> str:
    return f"{size / 1024:.0f} Ko" if size < 1024 * 1024 else f"{size / 1024 / 1024:.1f} Mo"


def verifier_fichier(path: Path | str) -> tuple[bool, str]:
    """Contrôle un fichier de base : lisible, intègre, et bien celui de l'application."""
    path = Path(path)
    if not path.exists():
        return False, "Fichier introuvable."
    try:
        conn = sqlite3.connect(str(path))
        try:
            messages = [r[0] for r in conn.execute("PRAGMA integrity_check").fetchall()]
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        finally:
            conn.close()
    except sqlite3.DatabaseError as exc:
        return False, f"Fichier illisible : {exc}"
    if messages != ["ok"]:
        return False, "Base endommagée : " + " ; ".join(messages[:3])
    if not all(t in tables for t in _TABLES_REQUISES):
        return False, "Ce fichier n'est pas une sauvegarde de l'application."
    return True, "ok"


def verifier_integrite(conn: sqlite3.Connection) -> tuple[bool, str]:
    """Vérification de la base ouverte, à faire à chaque démarrage."""
    try:
        messages = [r[0] for r in conn.execute("PRAGMA integrity_check").fetchall()]
    except sqlite3.DatabaseError as exc:
        return False, f"Base illisible : {exc}"
    if messages == ["ok"]:
        return True, "ok"
    return False, " ; ".join(messages[:3])


def _lire_version(path: Path) -> int:
    conn = sqlite3.connect(str(path))
    try:
        return conn.execute("PRAGMA user_version").fetchone()[0]
    finally:
        conn.close()


def _snapshot(source: sqlite3.Connection, dest: Path) -> None:
    out = sqlite3.connect(str(dest))
    try:
        source.backup(out)
        out.execute("PRAGMA journal_mode = DELETE")      # fichier autonome, sans -wal
    finally:
        out.close()


def _creer(conn: sqlite3.Connection, kind: str, backup_dir: Path | str | None,
           now: datetime | None) -> Path:
    folder = Path(backup_dir or BACKUP_DIR)
    folder.mkdir(parents=True, exist_ok=True)
    now = now or datetime.now()
    dest = folder / f"association_{now:%Y%m%d_%H%M%S}_{_CODES[kind]}.db"
    if dest.exists():
        raise BackupError("Une sauvegarde du même type existe déjà pour cette seconde. Réessayez.")
    tmp = dest.with_name(dest.name + ".tmp")
    try:
        _snapshot(conn, tmp)
        ok, message = verifier_fichier(tmp)
        if not ok:
            raise BackupError(f"La copie est invalide, elle n'a pas été conservée : {message}")
        os.replace(tmp, dest)
    finally:
        tmp.unlink(missing_ok=True)
    return dest


def lister(backup_dir: Path | str | None = None) -> list[Sauvegarde]:
    """Les plus récentes d'abord."""
    folder = Path(backup_dir or BACKUP_DIR)
    if not folder.exists():
        return []
    found = []
    for path in folder.glob("association_*.db"):
        match = _NAME_RE.match(path.name)
        if match:
            created = datetime.strptime(match.group(1) + match.group(2), "%Y%m%d%H%M%S")
            found.append(Sauvegarde(path, _KINDS[match.group(3)], created, path.stat().st_size))
    return sorted(found, key=lambda s: s.created, reverse=True)


def sauvegarder_manuelle(conn: sqlite3.Connection, session: Session,
                         backup_dir: Path | str | None = None,
                         now: datetime | None = None) -> Path:
    """Administrateur uniquement."""
    session.require(Permission.BACKUP_MANAGE)
    dest = _creer(conn, MANUELLE, backup_dir, now)
    with transaction(conn):
        audit.log(conn, session.user, Action.SAUVEGARDE, dest.name,
                  f"Sauvegarde manuelle · {_size_label(dest.stat().st_size)}")
    return dest


def sauvegarder_automatique(conn: sqlite3.Connection, backup_dir: Path | str | None = None,
                            now: datetime | None = None, keep: int = KEEP_AUTOMATIC) -> Path:
    """À la fermeture du logiciel (action du système). Conserve les `keep` dernières copies."""
    dest = _creer(conn, AUTOMATIQUE, backup_dir, now)
    with transaction(conn):
        audit.log(conn, None, Action.SAUVEGARDE, dest.name,
                  f"Sauvegarde automatique · {_size_label(dest.stat().st_size)}")
    for ancienne in [s for s in lister(backup_dir) if s.kind == AUTOMATIQUE][keep:]:
        ancienne.path.unlink(missing_ok=True)
    return dest


def restaurer(session: Session, backup_path: Path | str, db_path: Path | str | None = None,
              backup_dir: Path | str | None = None, now: datetime | None = None) -> Path | None:
    """Remplace la base par une sauvegarde. Administrateur uniquement.

    L'appelant doit avoir FERMÉ toutes les connexions à la base. Retourne le chemin de
    la copie de sécurité de la base remplacée (None si elle n'existait pas).
    """
    session.require(Permission.BACKUP_MANAGE)
    db_path = Path(db_path or DB_PATH)
    backup_path = Path(backup_path)

    ok, message = verifier_fichier(backup_path)
    if not ok:
        raise BackupError(f"Cette sauvegarde est inutilisable : {message}")
    if _lire_version(backup_path) > LATEST_VERSION:
        raise BackupError("Cette sauvegarde vient d'une version plus récente du logiciel.")

    securite = None
    if db_path.exists():
        actuelle = get_connection(db_path)
        try:
            securite = _creer(actuelle, SECURITE, backup_dir, now)
        finally:
            actuelle.close()

    tmp = db_path.with_name(db_path.name + ".restauration.tmp")
    try:
        src = sqlite3.connect(str(backup_path))
        dst = sqlite3.connect(str(tmp))
        try:
            src.backup(dst)
            dst.execute("PRAGMA journal_mode = DELETE")
        finally:
            src.close()
            dst.close()
        for suffixe in ("-wal", "-shm"):
            Path(str(db_path) + suffixe).unlink(missing_ok=True)
        try:
            os.replace(tmp, db_path)
        except PermissionError:
            raise BackupError("La base est en cours d'utilisation : fermez le logiciel "
                              "puis recommencez.") from None
    finally:
        tmp.unlink(missing_ok=True)

    conn = get_connection(db_path)
    try:
        migrate(conn)
        with transaction(conn):
            audit.log(conn, session.user, Action.RESTAURATION, backup_path.name,
                      "Base restaurée" + (f" · copie de sécurité {securite.name}" if securite else ""))
    finally:
        conn.close()
    return securite