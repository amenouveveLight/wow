"""Présentateur du tableau de bord : charge les chiffres via le port, prépare le modèle de vue."""
from __future__ import annotations

from PySide6.QtCore import QObject

from app.ui.ports import DashboardPort
from app.ui.presenters.dashboard_model import build_view_model
from app.ui.views.dashboard import DashboardView


class DashboardPresenter(QObject):
    def __init__(self, view: DashboardView, port: DashboardPort, parent: QObject | None = None) -> None:
        super().__init__(parent or view)
        self._view = view
        self._port = port

    def show_exercise(self, exercise_label: str) -> None:
        """Affiche le tableau de bord de l'exercice demandé."""
        self._view.set_model(build_view_model(self._port.load(exercise_label)))