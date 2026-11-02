"""Présentateur de la page Rapports."""
from __future__ import annotations

from PySide6.QtCore import QObject

from app.ui.ports_reports import ReportsData, ReportsPort
from app.ui.views.reports import ReportsView


class ReportsPresenter(QObject):
    def __init__(self, view: ReportsView, port: ReportsPort, parent: QObject | None = None) -> None:
        super().__init__(parent or view)
        self._view = view
        self._port = port

    def show_exercise(self, exercise_label: str) -> None:
        data = self._port.load(exercise_label)
        self._view.set_model(data)
