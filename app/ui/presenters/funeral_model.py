"""Modèle de vue pour les cotisations funéraires."""
from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple


@dataclass(frozen=True)
class FuneralRow:
    id: int
    deceased_name: str
    death_type: str
    death_date: str
    member_carnet: str
    amount_man: str
    amount_woman: str
    total_expected: str
    total_collected: str
    remaining: str
    exempted: bool
    is_complete: bool


@dataclass(frozen=True)
class FuneralViewModel:
    subtitle: str
    rows: tuple[FuneralRow, ...]
    empty: bool = False
    counter: str = ""


class FuneralQuery(NamedTuple):
    search: str = ""
    sort_key: str = "date"
    ascending: bool = False
    page: int = 1


def _format_amount(amount: int) -> str:
    return f"{amount:,}".replace(",", " ")


def build_row(record) -> FuneralRow:
    remaining = record.total_expected - record.total_collected
    return FuneralRow(
        id=record.id,
        deceased_name=record.deceased_name,
        death_type=record.death_type,
        death_date=record.death_date,
        member_carnet=record.member_carnet or "—",
        amount_man=_format_amount(record.amount_man),
        amount_woman=_format_amount(record.amount_woman),
        total_expected=_format_amount(record.total_expected),
        total_collected=_format_amount(record.total_collected),
        remaining=_format_amount(remaining),
        exempted=record.exempted,
        is_complete=remaining <= 0,
    )


def build_view_model(data, query: FuneralQuery) -> FuneralViewModel:
    filtered = data.records
    if query.search:
        search_lower = query.search.lower()
        filtered = tuple(r for r in filtered if search_lower in r.deceased_name.lower())

    if query.sort_key == "date":
        filtered = sorted(filtered, key=lambda r: r.death_date, reverse=not query.ascending)
    elif query.sort_key == "name":
        filtered = sorted(filtered, key=lambda r: r.deceased_name, reverse=not query.ascending)

    page_size = 20
    offset = (query.page - 1) * page_size
    page_records = filtered[offset:offset + page_size]
    total = len(filtered)
    page_count = (total + page_size - 1) // page_size if total else 1

    rows = tuple(build_row(r) for r in page_records)

    return FuneralViewModel(
        subtitle=f"Exercice {data.exercise_label} · {total} décès enregistré{'s' if total != 1 else ''}",
        rows=rows,
        empty=len(rows) == 0,
        counter=f"Page {query.page}/{page_count} · {total} résultat{'s' if total != 1 else ''}",
    )
