"""Présentateur de la page Bilan financier."""
from __future__ import annotations

from PySide6.QtCore import QObject

from app.ui.ports_balance import BalanceData, BalancePort
from app.ui.presenters.balance_model import build_view_model
from app.ui.views.balance import BalanceView


class BalancePresenter(QObject):
    def __init__(self, view: BalanceView, port: BalancePort, parent: QObject | None = None) -> None:
        super().__init__(parent or view)
        self._view = view
        self._port = port

    def show_exercise(self, exercise_label: str) -> None:
        data = self._port.load(exercise_label)
        self._view.set_model(build_view_model(data))
