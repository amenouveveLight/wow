"""Données factices de démonstration (remplacées plus tard par les paramètres et les services)."""
from __future__ import annotations

from app.ui.ports import ExerciseInfo, NotificationInfo

ASSOCIATION_NAME = "Collectivité LANTCHIBLE"
BRAND_NAME = "Collectivité LANTCHIBLE"
BRAND_SUB = "Gestion d’association"
BRAND_INITIALS = "CL"
SIDEBAR_FOOTER = "Version 1.0 · Mode hors ligne"
LOGIN_TAGLINE = ("Cotisations, décès, amendes et bilan : tout le carnet de votre association, "
                 "simplement et sans Internet.")
LOGIN_FEATURES = (
    "Cotisations mensuelles, funéraires et parallèles",
    "Bilan financier et clôture d’exercice",
    "Sauvegarde automatique de vos données",
)
LOGIN_FOOTER = "© 2026 Association Collectivité LANTCHIBLE"

EXERCISES = (
    ExerciseInfo("2025–2026", True),
    ExerciseInfo("2024–2025", False),
    ExerciseInfo("2023–2024", False),
)

NOTIFICATIONS = (
    NotificationInfo("Fin d’exercice proche", "L’exercice 2025–2026 se termine dans 14 jours.", "Aujourd’hui"),
    NotificationInfo("Cotisation parallèle", "« Fête de rentrée » : 3 membres n’ont pas encore payé.", "Hier"),
    NotificationInfo("Sauvegarde", "Dernière sauvegarde automatique : 28/08/2026 à 17:42.", "28/08/2026"),
)

LAST_BACKUP = "Dernière sauvegarde : 28/08/2026 à 17:42"
DEMO_NOTICE = "Données fictives de démonstration"