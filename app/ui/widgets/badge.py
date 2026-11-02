"""Badges de statut : toujours un libellé en plus de la couleur."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSizePolicy, QWidget

from app.ui.widgets.base import set_property


class Kind:
    SUCCESS = "success"
    DANGER = "danger"
    WARNING = "warning"
    NEUTRAL = "neutral"
    INFO = "info"
    ALL = (SUCCESS, DANGER, WARNING, NEUTRAL, INFO)


class Badge(QLabel):
    """Pastille de statut colorée."""

    def __init__(self, text: str = "", kind: str = Kind.NEUTRAL, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("Badge")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.set_kind(kind)

    @property
    def kind(self) -> str:
        return str(self.property("kind"))

    def set_kind(self, kind: str) -> None:
        if kind not in Kind.ALL:
            raise ValueError(f"Genre de badge inconnu : {kind}")
        set_property(self, "kind", kind)


# clé de statut métier → (libellé, genre)
STATUS_BADGES: dict[str, tuple[str, str]] = {
    "paye": ("Payé", Kind.SUCCESS),
    "partiel": ("Partiel", Kind.WARNING),
    "impaye": ("Dette", Kind.DANGER),
    "na": ("Non applicable", Kind.NEUTRAL),
    "actif": ("Actif", Kind.INFO),
    "decede": ("Décédé", Kind.NEUTRAL),
    "payee": ("Payée", Kind.SUCCESS),
    "partielle": ("Partielle", Kind.WARNING),
    "impayee": ("Impayée", Kind.DANGER),
    "manuelle": ("Manuelle", Kind.INFO),
    "automatique": ("Automatique", Kind.NEUTRAL),
    "verifiee": ("Vérifiée", Kind.SUCCESS),
    "administrateur": ("Administrateur", Kind.INFO),
    "secretaire": ("Secrétaire", Kind.NEUTRAL),
}


def status_badge(status: str, parent: QWidget | None = None) -> Badge:
    """Badge d'un statut des services (cotisation_mensuelle.PAYE, membre.statut, amende.statut…)."""
    if status not in STATUS_BADGES:
        raise ValueError(f"Statut inconnu : {status}")
    texte, genre = STATUS_BADGES[status]
    return Badge(texte, genre, parent)