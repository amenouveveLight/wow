"""Numéros de carnet : générés par le système, format défini par l'administrateur.

Format = préfixe + numéro d'ordre complété par des zéros.
Exemples : préfixe "" largeur 3 → 001, 002… ; préfixe "LT-" largeur 4 → LT-0043.
"""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass

from app.database.connection import transaction
from app.repositories import membres, parametres
from app.security import audit
from app.security.audit import Action
from app.security.session import Permission, Session

KEY_PREFIX = "carnet_prefixe"
KEY_WIDTH = "carnet_largeur"
KEY_NEXT = "carnet_prochain"

DEFAULT_PREFIX = ""
DEFAULT_WIDTH = 3
DEFAULT_NEXT = 1

_PREFIX_RE = re.compile(r"^[A-Z0-9\-/]{0,10}$")


class CarnetError(Exception):
    """Format de numéro de carnet invalide (message affichable)."""


@dataclass(frozen=True)
class CarnetFormat:
    prefix: str
    width: int
    next_number: int

    def render(self, number: int | None = None) -> str:
        n = self.next_number if number is None else number
        return f"{self.prefix}{n:0{self.width}d}"


def get_format(conn: sqlite3.Connection) -> CarnetFormat:
    return CarnetFormat(
        prefix=parametres.get(conn, KEY_PREFIX, DEFAULT_PREFIX) or "",
        width=int(parametres.get(conn, KEY_WIDTH, str(DEFAULT_WIDTH))),
        next_number=int(parametres.get(conn, KEY_NEXT, str(DEFAULT_NEXT))),
    )


def preview(conn: sqlite3.Connection) -> str:
    """Prochain numéro qui sera attribué, sans le consommer (affichage du formulaire)."""
    fmt = get_format(conn)
    n = fmt.next_number
    while membres.get_by_carnet(conn, fmt.render(n)):
        n += 1
    return fmt.render(n)


def allocate(conn: sqlite3.Connection) -> str:
    """Attribue le prochain numéro libre. À appeler DANS la transaction qui crée le membre."""
    fmt = get_format(conn)
    n = fmt.next_number
    while membres.get_by_carnet(conn, fmt.render(n)):
        n += 1
    parametres.set_(conn, KEY_NEXT, str(n + 1))
    return fmt.render(n)


def set_format(conn: sqlite3.Connection, session: Session, prefix: str, width: int,
               next_number: int) -> CarnetFormat:
    """Administrateur uniquement. Ne change pas les numéros déjà attribués."""
    session.require(Permission.SETTINGS_MANAGE)
    prefix = (prefix or "").strip().upper()
    if not _PREFIX_RE.match(prefix):
        raise CarnetError("Préfixe invalide : lettres, chiffres, « - » ou « / » (10 caractères maximum).")
    if isinstance(width, bool) or not isinstance(width, int) or not 1 <= width <= 8:
        raise CarnetError("Le nombre de chiffres doit être compris entre 1 et 8.")
    if isinstance(next_number, bool) or not isinstance(next_number, int) or next_number < 1:
        raise CarnetError("Le prochain numéro doit être un entier supérieur ou égal à 1.")

    old = get_format(conn)
    new = CarnetFormat(prefix, width, next_number)
    with transaction(conn):
        parametres.set_(conn, KEY_PREFIX, new.prefix)
        parametres.set_(conn, KEY_WIDTH, str(new.width))
        parametres.set_(conn, KEY_NEXT, str(new.next_number))
        audit.log(conn, session.user, Action.CARNET_FORMAT, "Numéros de carnet",
                  f"{old.render()} → {new.render()}")
    return new