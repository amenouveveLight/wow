"""Coquille de l'application : barre latérale, barre supérieure, pages, barre d'état, popovers."""
from __future__ import annotations

from functools import partial

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QScrollArea, QStackedWidget, QVBoxLayout, QWidget

from app.ui.navigation import NAV_ITEMS, Page, allowed_keys
from app.ui.ports import ExerciseInfo, NotificationInfo, UserInfo
from app.ui.views.placeholder import PlaceholderPage
from app.ui.widgets.popover import Popover
from app.ui.widgets.sidebar import Sidebar
from app.ui.widgets.statusbar import AppStatusBar
from app.ui.widgets.topbar import TopBar


class Shell(QWidget):
    """Affichage seul : les actions de l'utilisateur sortent par des signaux."""

    logout_requested = Signal()
    password_requested = Signal()
    page_changed = Signal(str)
    exercise_selected = Signal(str)

    def __init__(self, *, association_name: str, brand_name: str, brand_sub: str, brand_initials: str,
                 footer: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        racine = QHBoxLayout(self)
        racine.setContentsMargins(0, 0, 0, 0)
        racine.setSpacing(0)
        self.sidebar = Sidebar(brand_name=brand_name, brand_sub=brand_sub,
                               brand_initials=brand_initials, footer=footer)
        self.topbar = TopBar(association_name)
        self.statusbar = AppStatusBar()
        self.pages = QStackedWidget()
        colonne = QVBoxLayout()
        colonne.setContentsMargins(0, 0, 0, 0)
        colonne.setSpacing(0)
        colonne.addWidget(self.topbar)
        colonne.addWidget(self.pages, 1)
        colonne.addWidget(self.statusbar)
        racine.addWidget(self.sidebar)
        racine.addLayout(colonne, 1)

        self._conteneurs: dict[str, QScrollArea] = {}
        self._cle_courante: str | None = None
        self._exercices: list[ExerciseInfo] = []
        self._exercice_courant = 0
        self._notifications: list[NotificationInfo] = []
        self._user: UserInfo | None = None
        self._popover: Popover | None = None
        for entree in NAV_ITEMS:
            self.set_page(entree.key, PlaceholderPage(entree))

        self.sidebar.navigate.connect(self.show_page)
        self.topbar.exercise_requested.connect(self._ouvrir_exercices)
        self.topbar.notifications_requested.connect(self._ouvrir_notifications)
        self.topbar.user_requested.connect(self._ouvrir_utilisateur)

    # ---------- pages ----------
    @property
    def current_key(self) -> str | None:
        return self._cle_courante

    @property
    def popover(self) -> Popover | None:
        return self._popover

    def page_container(self, key: str) -> QScrollArea:
        return self._conteneurs[key]

    def set_page(self, key: str, widget: QWidget) -> None:
        """Installe (ou remplace) la page d'une entrée de la barre latérale."""
        ancien = self._conteneurs.pop(key, None)
        if ancien is not None:
            self.pages.removeWidget(ancien)
            ancien.deleteLater()
        defilement = QScrollArea()
        defilement.setWidgetResizable(True)
        defilement.setFrameShape(QFrame.Shape.NoFrame)
        defilement.setWidget(widget)
        self.pages.addWidget(defilement)
        self._conteneurs[key] = defilement
        if key == self._cle_courante:
            self.pages.setCurrentWidget(defilement)

    def show_page(self, key: str) -> None:
        if key not in self._conteneurs:
            raise KeyError(key)
        self.pages.setCurrentWidget(self._conteneurs[key])
        self.sidebar.set_active(key)
        self._cle_courante = key
        self.page_changed.emit(key)

    # ---------- session et données ----------
    def start(self, user: UserInfo) -> None:
        """Affiche la coquille pour l'utilisateur connecté, sur le tableau de bord."""
        self._user = user
        self.topbar.set_user(user.full_name, user.role_label)
        self.sidebar.set_allowed(allowed_keys(user.is_admin))
        self.show_page(Page.DASHBOARD)

    def set_exercises(self, exercices: list[ExerciseInfo], current: int = 0) -> None:
        self._exercices = list(exercices)
        self._exercice_courant = current
        self._appliquer_exercice()

    @property
    def current_exercise_label(self) -> str:
        return self._exercices[self._exercice_courant].label if self._exercices else ""

    def set_notifications(self, notifications: list[NotificationInfo]) -> None:
        self._notifications = list(notifications)

    def close_popover(self) -> None:
        if self._popover is not None:
            self._popover.close()

    def _appliquer_exercice(self) -> None:
        if not self._exercices:
            return
        libelle = self.current_exercise_label
        self.topbar.set_exercise(f"Exercice {libelle} (sept. → août)")
        self.statusbar.set_exercise(f"Exercice actif : {libelle}")

    # ---------- popovers de la barre supérieure ----------
    def _afficher(self, popover: Popover, ancre: QWidget) -> None:
        self.close_popover()
        self._popover = popover
        popover.popup_below(ancre, align="right")

    def _ouvrir_exercices(self, ancre: QWidget) -> None:
        popover = Popover(self, width=300)
        popover.add_header("Exercice comptable")
        for index, exercice in enumerate(self._exercices):
            popover.add_item(f"Exercice {exercice.label}", "Ouvert" if exercice.is_open else "Clôturé",
                             icon_name="calendar", checked=index == self._exercice_courant,
                             on_click=partial(self._choisir_exercice, index))
        self._afficher(popover, ancre)

    def _choisir_exercice(self, index: int) -> None:
        self._exercice_courant = index
        self._appliquer_exercice()
        self.exercise_selected.emit(self.current_exercise_label)

    def _ouvrir_notifications(self, ancre: QWidget) -> None:
        popover = Popover(self, width=340)
        popover.add_header("Notifications", f"{len(self._notifications)} récentes" if self._notifications else "")
        if not self._notifications:
            popover.add_empty("Aucune notification pour le moment.")
        for notification in self._notifications:
            popover.add_item(notification.title, f"{notification.text} · {notification.when}", icon_name="bell")
        self._afficher(popover, ancre)

    def _ouvrir_utilisateur(self, ancre: QWidget) -> None:
        popover = Popover(self, width=260)
        if self._user is not None:
            popover.add_header(self._user.full_name, self._user.role_label)
        popover.add_separator()
        popover.add_item("Changer mon mot de passe", icon_name="lock", on_click=self.password_requested.emit)
        popover.add_item("Se déconnecter", icon_name="logout", tone="danger", on_click=self.logout_requested.emit)
        self._afficher(popover, ancre)