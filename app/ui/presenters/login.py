"""Présentateur de la connexion : valide la saisie, appelle le port d'authentification,
dit à la vue quoi afficher. Aucun widget créé ici."""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from app.ui.ports import AuthPort, LoginStatus
from app.ui.views.login import LoginView


class LoginPresenter(QObject):
    authenticated = Signal(object)          # UserInfo

    def __init__(self, view: LoginView, auth: AuthPort, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._view = view
        self._auth = auth
        view.submitted.connect(self.on_submitted)

    def on_submitted(self, identifiant: str, password: str) -> None:
        identifiant = identifiant.strip()
        if not identifiant or not password:
            self._view.show_field_errors(
                None if identifiant else "Saisissez votre identifiant.",
                None if password else "Saisissez votre mot de passe.")
            return
        self._view.clear_errors()
        self._view.set_busy(True)
        try:
            resultat = self._auth.login(identifiant, password)
        finally:
            self._view.set_busy(False)
        if resultat.status == LoginStatus.OK and resultat.user is not None:
            self._view.clear_password()
            self.authenticated.emit(resultat.user)
        elif resultat.status == LoginStatus.REFUSED:
            self._view.show_refused(resultat.message or "Identifiant ou mot de passe incorrect.")
        elif resultat.status == LoginStatus.LOCKED:
            self._view.show_locked(resultat.message or "Compte verrouillé.")
        else:
            raise ValueError(f"Résultat de connexion inconnu : {resultat.status}")