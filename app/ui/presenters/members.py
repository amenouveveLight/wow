"""Présentateur de la page Membres : garde l'état (filtres, tri, page) et met la vue à jour."""
from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import QObject

from app.ui.ports_members import MembersData, MembersPort
from app.ui.presenters.members_model import MembersQuery, build_view_model
from app.ui.views.members import MembersView


class MembersPresenter(QObject):
    def __init__(self, view: MembersView, port: MembersPort, parent: QObject | None = None) -> None:
        super().__init__(parent or view)
        self._view = view
        self._port = port
        self._data: MembersData | None = None
        self._query = MembersQuery()
        view.search_changed.connect(lambda t: self._changer(text=t, page=1))
        view.status_changed.connect(lambda s: self._changer(status=s, page=1))
        view.sex_changed.connect(lambda s: self._changer(sex=s, page=1))
        view.sort_requested.connect(self._trier)
        view.page_requested.connect(lambda p: self._changer(page=p))

    def show_exercise(self, exercise_label: str) -> None:
        self._data = self._port.load(exercise_label)
        self._changer(page=1)

    def _trier(self, cle: str) -> None:
        if cle == self._query.sort_key:
            self._changer(ascending=not self._query.ascending, page=1)
        else:
            self._changer(sort_key=cle, ascending=True, page=1)

    def _changer(self, **champs) -> None:
        self._query = replace(self._query, **champs)
        if self._data is None:
            return
        modele = build_view_model(self._data, self._query)
        self._query = replace(self._query, page=modele.page)
        self._view.set_model(modele)
