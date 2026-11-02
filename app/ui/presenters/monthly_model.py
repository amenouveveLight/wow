"""Modèle de vue pour les cotisations mensuelles : transformation des données brutes en structure d'affichage."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import NamedTuple


@dataclass(frozen=True)
class MonthlyMemberRow:
    carnet: str
    name: str
    sex: str
    joined: str
    cells: tuple[str, ...]
    total_due: str
    total_paid: str
    total_debt: str
    advance: str
    has_debt: bool
    has_advance: bool


@dataclass(frozen=True)
class MonthlyViewModel:
    subtitle: str
    tariff_man: str
    tariff_woman: str
    rows: tuple[MonthlyMemberRow, ...]
    empty: bool = False
    counter: str = ""


class MonthlyQuery(NamedTuple):
    search: str = ""
    sex: str = "all"
    sort_key: str = "carnet"
    ascending: bool = True
    page: int = 1


def _format_amount(amount: int) -> str:
    return f"{amount:,}".replace(",", " ")


def _cell_symbol(status: str) -> str:
    if status == "paye":
        return "✓"
    if status == "partiel":
        return "◐"
    if status == "impaye":
        return "✗"
    return "—"


def build_member_row(member, tariffs: dict[str, int]) -> MonthlyMemberRow:
    cells = tuple(_cell_symbol(cell.status) for cell in member.cells)
    return MonthlyMemberRow(
        carnet=member.carnet,
        name=member.name,
        sex=member.sex,
        joined=member.joined,
        cells=cells,
        total_due=_format_amount(member.total_due),
        total_paid=_format_amount(member.total_paid),
        total_debt=_format_amount(member.total_debt),
        advance=_format_amount(member.advance),
        has_debt=member.total_debt > 0,
        has_advance=member.advance > 0,
    )


def build_view_model(data, query: MonthlyQuery) -> MonthlyViewModel:
    filtered = data.members
    if query.search:
        search_lower = query.search.lower()
        filtered = tuple(m for m in filtered if search_lower in m.name.lower() or search_lower in m.carnet.lower())
    if query.sex != "all":
        filtered = tuple(m for m in filtered if m.sex == query.sex)

    if query.sort_key == "carnet":
        filtered = sorted(filtered, key=lambda m: m.carnet, reverse=not query.ascending)
    elif query.sort_key == "name":
        filtered = sorted(filtered, key=lambda m: m.name, reverse=not query.ascending)
    elif query.sort_key == "debt":
        filtered = sorted(filtered, key=lambda m: m.total_debt, reverse=not query.ascending)

    page_size = 20
    offset = (query.page - 1) * page_size
    page_members = filtered[offset:offset + page_size]
    total = len(filtered)
    page_count = (total + page_size - 1) // page_size if total else 1

    rows = tuple(build_member_row(m, {"M": data.tariff_man, "F": data.tariff_woman}) for m in page_members)

    return MonthlyViewModel(
        subtitle=f"Exercice {data.exercise_label} · {total} membre{'s' if total != 1 else ''}",
        tariff_man=_format_amount(data.tariff_man),
        tariff_woman=_format_amount(data.tariff_woman),
        rows=rows,
        empty=len(rows) == 0,
        counter=f"Page {query.page}/{page_count} · {total} résultat{'s' if total != 1 else ''}",
    )
