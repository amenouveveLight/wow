"""Présentateur de la page Paramètres."""
from __future__ import annotations

from PySide6.QtCore import QObject

from app.ui.views.settings import SettingsView


class SettingsPresenter(QObject):
    def __init__(self, view: SettingsView, parent: QObject | None = None) -> None:
        super().__init__(parent or view)
        self._view = view

    def show(self) -> None:
        self._view.set_model(None)
