"""Calendrier de l'exercice (septembre → août). Fonctions pures."""
from __future__ import annotations

import calendar
from datetime import date

from app.config import FISCAL_YEAR_START_MONTH

MOIS_FR = (
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
)


def month_label(month: int) -> str:
    return MOIS_FR[month - 1]


def start_year_for_date(d: date) -> int:
    """Année de début de l'exercice qui contient la date (1er sept. 2026 → 2026)."""
    return d.year if d.month >= FISCAL_YEAR_START_MONTH else d.year - 1


def libelle(start_year: int) -> str:
    return f"{start_year}-{start_year + 1}"


def start_year_from_libelle(text: str) -> int:
    first, second = (int(part) for part in text.split("-"))
    if second != first + 1:
        raise ValueError(f"Libellé d'exercice invalide : {text}")
    return first


def exercise_months(start_year: int) -> list[tuple[int, int]]:
    """Les 12 mois (année, mois) dans l'ordre de l'exercice."""
    months = []
    for i in range(12):
        index = FISCAL_YEAR_START_MONTH - 1 + i
        months.append((start_year + index // 12, index % 12 + 1))
    return months


def bounds(start_year: int) -> tuple[date, date]:
    """Premier et dernier jour de l'exercice."""
    months = exercise_months(start_year)
    first_year, first_month = months[0]
    last_year, last_month = months[-1]
    return (
        date(first_year, first_month, 1),
        date(last_year, last_month, calendar.monthrange(last_year, last_month)[1]),
    )