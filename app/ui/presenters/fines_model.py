"""Modèle de vue pour les amendes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple


@dataclass(frozen=True)
class FineRow:
    id: int
    member_carnet: str
    member_name: str
    label: str
    date: str
    amount_expected: str
    amount_collected: str
    remaining: str
    is_paid: bool


@dataclass(frozen=True)
class FinesViewModel:
    subtitle: str
    rows: tuple[FineRow, ...]
    empty: bool = False
    counter: str = ""


class FinesQuery(NamedTuple):
    search: str = ""
    sort_key: str = "date"
    ascending: bool = False
    page: int = 1


def _format_amount(amount: int) -> str:
    return f"{amount:,}".replace(",", " ")


def build_row(record) -> FineRow:
    return FineRow(
        id=record.id,
        member_carnet=record.member_carnet,
        member_name=record.member_name,
        label=record.label,
        date=record.date,
        amount_expected=_format_amount(record.amount_expected),
        amount_collected=_format_amount(record.amount_collected),
        remaining=_format_amount(record.remaining),
        is_paid=record.remaining <= 0,
    )


def build_view_model(data, query: FinesQuery) -> FinesViewModel:
    filtered = data.records
    if query.search:
        search_lower = query.search.lower()
        filtered = tuple(r for r in filtered if search_lower in r.member_name.lower() or search_lower in r.member_carnet.lower())

    if query.sort_key == "date":
        filtered = sorted(filtered, key=lambda r: r.date, reverse=not query.ascending)
    elif query.sort_key == "name":
        filtered = sorted(filtered, key=lambda r: r.member_name, reverse=not query.ascending)

    page_size = 20
    offset = (query.page - 1) * page_size
    page_records = filtered[offset:offset + page_size]
    total = len(filtered)
    page_count = (total + page_size - 1) // page_size if total else 1

    rows = tuple(build_row(r) for r in page_records)

    return FinesViewModel(
        subtitle=f"Exercice {data.exercise_label} · {total} amende{'s' if total != 1 else ''}",
        rows=rows,
        empty=len(rows) == 0,
        counter=f"Page {query.page}/{page_count} · {total} résultat{'s' if total != 1 else ''}",
    )
