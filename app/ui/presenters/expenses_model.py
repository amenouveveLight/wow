"""Modèle de vue pour les dépenses."""
from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple


@dataclass(frozen=True)
class ExpenseRow:
    id: int
    date: str
    label: str
    beneficiary: str
    amount_planned: str
    amount_spent: str
    is_over_budget: bool


@dataclass(frozen=True)
class ExpensesViewModel:
    subtitle: str
    total_planned: str
    total_spent: str
    rows: tuple[ExpenseRow, ...]
    empty: bool = False
    counter: str = ""


class ExpensesQuery(NamedTuple):
    search: str = ""
    sort_key: str = "date"
    ascending: bool = False
    page: int = 1


def _format_amount(amount: int) -> str:
    return f"{amount:,}".replace(",", " ")


def build_row(record) -> ExpenseRow:
    return ExpenseRow(
        id=record.id,
        date=record.date,
        label=record.label,
        beneficiary=record.beneficiary or "—",
        amount_planned=_format_amount(record.amount_planned),
        amount_spent=_format_amount(record.amount_spent),
        is_over_budget=record.amount_spent > record.amount_planned,
    )


def build_view_model(data, query: ExpensesQuery) -> ExpensesViewModel:
    filtered = data.records
    if query.search:
        search_lower = query.search.lower()
        filtered = tuple(r for r in filtered if search_lower in r.label.lower())

    if query.sort_key == "date":
        filtered = sorted(filtered, key=lambda r: r.date, reverse=not query.ascending)
    elif query.sort_key == "label":
        filtered = sorted(filtered, key=lambda r: r.label, reverse=not query.ascending)

    page_size = 20
    offset = (query.page - 1) * page_size
    page_records = filtered[offset:offset + page_size]
    total = len(filtered)
    page_count = (total + page_size - 1) // page_size if total else 1

    rows = tuple(build_row(r) for r in page_records)

    return ExpensesViewModel(
        subtitle=f"Exercice {data.exercise_label} · {total} dépense{'s' if total != 1 else ''}",
        total_planned=_format_amount(data.total_planned),
        total_spent=_format_amount(data.total_spent),
        rows=rows,
        empty=len(rows) == 0,
        counter=f"Page {query.page}/{page_count} · {total} résultat{'s' if total != 1 else ''}",
    )
