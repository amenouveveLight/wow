"""Modèle de vue pour les cotisations parallèles."""
from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple


@dataclass(frozen=True)
class ParallelRow:
    id: int
    name: str
    start_date: str
    end_date: str
    amount_man: str
    amount_woman: str
    total_expected: str
    total_collected: str
    remaining: str
    is_complete: bool


@dataclass(frozen=True)
class ParallelViewModel:
    subtitle: str
    rows: tuple[ParallelRow, ...]
    empty: bool = False
    counter: str = ""


class ParallelQuery(NamedTuple):
    search: str = ""
    sort_key: str = "name"
    ascending: bool = True
    page: int = 1


def _format_amount(amount: int) -> str:
    return f"{amount:,}".replace(",", " ")


def build_row(sub) -> ParallelRow:
    remaining = sub.total_expected - sub.total_collected
    return ParallelRow(
        id=sub.id,
        name=sub.name,
        start_date=sub.start_date,
        end_date=sub.end_date,
        amount_man=_format_amount(sub.amount_man),
        amount_woman=_format_amount(sub.amount_woman),
        total_expected=_format_amount(sub.total_expected),
        total_collected=_format_amount(sub.total_collected),
        remaining=_format_amount(remaining),
        is_complete=remaining <= 0,
    )


def build_view_model(data, query: ParallelQuery) -> ParallelViewModel:
    filtered = data.subscriptions
    if query.search:
        search_lower = query.search.lower()
        filtered = tuple(s for s in filtered if search_lower in s.name.lower())

    if query.sort_key == "name":
        filtered = sorted(filtered, key=lambda s: s.name, reverse=not query.ascending)
    elif query.sort_key == "date":
        filtered = sorted(filtered, key=lambda s: s.start_date, reverse=not query.ascending)

    page_size = 20
    offset = (query.page - 1) * page_size
    page_subs = filtered[offset:offset + page_size]
    total = len(filtered)
    page_count = (total + page_size - 1) // page_size if total else 1

    rows = tuple(build_row(s) for s in page_subs)

    return ParallelViewModel(
        subtitle=f"Exercice {data.exercise_label} · {total} cotisation{'s' if total != 1 else ''}",
        rows=rows,
        empty=len(rows) == 0,
        counter=f"Page {query.page}/{page_count} · {total} résultat{'s' if total != 1 else ''}",
    )
