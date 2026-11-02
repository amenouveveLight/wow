"""Données de démonstration pour les blocs du tableau de bord absents de MockDashboard.

Temporaire : à retirer quand MockDashboard (puis les services) fournit monthly, operations et debtors.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import date

from app.ui.ports import DashboardData, DashboardPort, DebtorInfo, MonthFigures, OperationInfo

_MOIS = ("Sep", "Oct", "Nov", "Déc", "Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août")
_ENTREES = (610, 575, 640, 700, 590, 560, 665, 500, 535, 570, 520, 690)
_DEPENSES = (170, 190, 310, 240, 175, 200, 275, 195, 225, 265, 185, 240)

DEMO_MONTHLY = tuple(MonthFigures(m, e * 1000, d * 1000) for m, e, d in zip(_MOIS, _ENTREES, _DEPENSES))
DEMO_OPERATIONS = (
    OperationInfo(date(2026, 6, 18), "Carnet 014 — Koffi Mensah", "Mensuelle", 10000, "paye"),
    OperationInfo(date(2026, 6, 17), "Collecte décès — M. Agbodjan", "Funéraire", 25000, "paye"),
    OperationInfo(date(2026, 6, 16), "Achat de chaises (prévu 120 000)", "Dépense", -105000, "reliquat"),
    OperationInfo(date(2026, 6, 15), "Amende retard — Esi Amegah", "Amende", 2000, "attente"),
    OperationInfo(date(2026, 6, 14), "Carnet 027 — Afi Adjovi", "Mensuelle", 5000, "partiel"),
)
DEMO_DEBTORS = (
    DebtorInfo("Yawo Agbodjan", "Carnet 009", 85000),
    DebtorInfo("Esi Amegah", "Carnet 031", 62000),
    DebtorInfo("Kodjo Tété", "Carnet 017", 48000),
    DebtorInfo("Mawuli Gbedemah", "Carnet 023", 35000),
    DebtorInfo("Dédé Lawson", "Carnet 044", 20000),
)


class AvecDonneesDemo:
    """Enveloppe un DashboardPort et complète les champs vides avec des données fictives."""

    def __init__(self, base: DashboardPort) -> None:
        self._base = base

    def load(self, exercise_label: str) -> DashboardData:
        data = self._base.load(exercise_label)
        return replace(data,
                       monthly=data.monthly or DEMO_MONTHLY,
                       operations=data.operations or DEMO_OPERATIONS,
                       debtors=data.debtors or DEMO_DEBTORS)

    def __getattr__(self, nom: str):
        return getattr(self._base, nom)