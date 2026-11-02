"""Pages de l'application et entrées de la barre latérale (clés stables)."""
from __future__ import annotations

from typing import NamedTuple


class Page:
    DASHBOARD = "dashboard"
    MEMBERS = "members"
    MONTHLY = "monthly"
    FUNERAL = "funeral"
    PARALLEL = "parallel"
    FINES = "fines"
    EXPENSES = "expenses"
    LEFTOVERS = "leftovers"
    BALANCE = "balance"
    REPORTS = "reports"
    BACKUPS = "backups"
    AUDIT = "audit"
    SETTINGS = "settings"


class NavEntry(NamedTuple):
    key: str
    label: str
    icon: str


NAV_ITEMS: tuple[NavEntry, ...] = (
    NavEntry(Page.DASHBOARD, "Tableau de bord", "dashboard"),
    NavEntry(Page.MEMBERS, "Membres", "users"),
    NavEntry(Page.MONTHLY, "Cotisations mensuelles", "calendar"),
    NavEntry(Page.FUNERAL, "Cotisations funéraires", "heart"),
    NavEntry(Page.PARALLEL, "Cotisations parallèles", "layers"),
    NavEntry(Page.FINES, "Amendes", "alert"),
    NavEntry(Page.EXPENSES, "Dépenses", "wallet"),
    NavEntry(Page.LEFTOVERS, "Reliquats", "coins"),
    NavEntry(Page.BALANCE, "Bilan financier", "chart"),
    NavEntry(Page.REPORTS, "Rapports et exports", "file"),
    NavEntry(Page.BACKUPS, "Sauvegardes", "database"),
    NavEntry(Page.AUDIT, "Journal d’audit", "shield"),
    NavEntry(Page.SETTINGS, "Paramètres", "settings"),
)

# Masquées pour les secrétaires (vue secrétaire de la maquette)
ADMIN_ONLY = frozenset({Page.BALANCE, Page.BACKUPS, Page.AUDIT, Page.SETTINGS})


def allowed_keys(is_admin: bool) -> frozenset[str]:
    """Entrées visibles selon le rôle. Le contrôle réel des droits reste dans les services."""
    keys = frozenset(entry.key for entry in NAV_ITEMS)
    return keys if is_admin else keys - ADMIN_ONLY