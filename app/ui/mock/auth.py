"""Authentification fictive pour la démonstration de l'interface (aucun accès à la base)."""
from __future__ import annotations

from app.ui.ports import LoginResult, LoginStatus, Role, UserInfo

MAX_ATTEMPTS = 5            # à aligner sur auth_service au branchement
LOCK_MINUTES = 15

_COMPTES = {
    "admin": ("Admin2026", "Ama Kpodar", Role.ADMINISTRATEUR),
    "yawa": ("Secret2026", "Yawa Dovi", Role.SECRETAIRE),
}


class MockAuth:
    """Deux comptes fictifs. Cinq échecs verrouillent l'identifiant (jusqu'à la fermeture)."""

    def __init__(self) -> None:
        self._echecs: dict[str, int] = {}

    def login(self, identifiant: str, password: str) -> LoginResult:
        cle = identifiant.strip().lower()
        if self._echecs.get(cle, 0) >= MAX_ATTEMPTS:
            return self._verrouille()
        compte = _COMPTES.get(cle)
        if compte is not None and compte[0] == password:
            self._echecs.pop(cle, None)
            return LoginResult(LoginStatus.OK, UserInfo(cle, compte[1], compte[2]))
        echecs = self._echecs.get(cle, 0) + 1
        self._echecs[cle] = echecs
        if echecs >= MAX_ATTEMPTS:
            return self._verrouille()
        restantes = MAX_ATTEMPTS - echecs
        pluriel = "s" if restantes > 1 else ""
        return LoginResult(LoginStatus.REFUSED, message=(
            f"Identifiant ou mot de passe incorrect. Il vous reste {restantes} tentative{pluriel}."))

    @staticmethod
    def _verrouille() -> LoginResult:
        return LoginResult(LoginStatus.LOCKED, message=(
            f"Compte verrouillé après {MAX_ATTEMPTS} tentatives échouées. Réessayez dans {LOCK_MINUTES} minutes "
            "ou demandez à l’administrateur de réinitialiser votre mot de passe."))