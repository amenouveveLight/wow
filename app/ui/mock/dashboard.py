"""Chiffres fictifs du tableau de bord (remplacés plus tard par un adaptateur sur les services).

L'exercice de référence reprend le scénario de test : dû 975 000, perçu 802 000 (reliquats compris),
dépenses 1 180 000, donc un solde en dette de 378 000. Les exercices clôturés montrent un excédent.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import date

from app.ui.ports import AlertInfo, DashboardData, PaymentInfo, RubriqueFigures

_REFERENCE = DashboardData(
    exercise_label="2025–2026",
    is_open=True,
    period_start=date(2025, 9, 1),
    period_end=date(2026, 8, 31),
    active_members=412,
    deceased_members=3,
    rubriques=(
        RubriqueFigures("mensuelle", "Cotisations mensuelles", 790_000, 587_000),
        RubriqueFigures("funeraire", "Cotisations funéraires", 122_000, 64_000),
        RubriqueFigures("parallele", "Cotisations parallèles", 54_000, 28_000),
        RubriqueFigures("reliquats", "Reliquats", None, 120_000),
        RubriqueFigures("amendes", "Amendes", 9_000, 3_000),
    ),
    expenses=1_180_000,
    debts_total=305_000,
    debtor_members=6,
    payments=(
        PaymentInfo("Yawo Agbodjan", "Cotisation mensuelle", date(2026, 8, 28), 18_000, "courant"),
        PaymentInfo("Efua Dosseh", "Cotisation funéraire", date(2026, 8, 27), 8_000, "courant"),
        PaymentInfo("Mina Gbedemah", "Arriérés — cotisation funéraire", date(2026, 8, 26), 8_000, "arriere"),
        PaymentInfo("Abla Tsogbé", "Cotisation parallèle « Fête de rentrée »", date(2026, 8, 25), 10_000, "courant"),
        PaymentInfo("Komlan Akakpo", "Cotisation mensuelle", date(2026, 8, 24), 36_000, "courant"),
    ),
    alerts=(
        AlertInfo("warning", "L’exercice 2025–2026 se termine dans 14 jours : pensez à préparer la clôture."),
        AlertInfo("danger", "6 membres ont des dettes de cotisation à recouvrer."),
        AlertInfo("info", "Dernière sauvegarde automatique : 28/08/2026 à 17:42."),
    ),
)

_ARCHIVED = DashboardData(
    exercise_label="",
    is_open=False,
    period_start=date(2024, 9, 1),
    period_end=date(2025, 8, 31),
    active_members=398,
    deceased_members=2,
    rubriques=(
        RubriqueFigures("mensuelle", "Cotisations mensuelles", 1_800_000, 1_800_000),
        RubriqueFigures("funeraire", "Cotisations funéraires", 300_000, 320_000),
        RubriqueFigures("parallele", "Cotisations parallèles", 100_000, 100_000),
        RubriqueFigures("reliquats", "Reliquats", None, 150_000),
        RubriqueFigures("amendes", "Amendes", 20_000, 20_000),
    ),
    expenses=1_900_000,
    debts_total=0,
    debtor_members=0,
    payments=(
        PaymentInfo("Komlan Akakpo", "Cotisation mensuelle", date(2025, 8, 29), 18_000, "courant"),
        PaymentInfo("Yawo Agbodjan", "Cotisation mensuelle", date(2025, 8, 27), 18_000, "courant"),
    ),
    alerts=(AlertInfo("info", "Exercice clôturé : consultation seulement."),),
)


class MockDashboard:
    """Aucun accès à la base : renvoie le jeu de référence ou le jeu d'un exercice clôturé."""

    def load(self, exercise_label: str) -> DashboardData:
        if exercise_label == _REFERENCE.exercise_label:
            return _REFERENCE
        annee = int(exercise_label[:4])
        return replace(_ARCHIVED, exercise_label=exercise_label,
                       period_start=date(annee, 9, 1), period_end=date(annee + 1, 8, 31))