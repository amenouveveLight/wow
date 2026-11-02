"""Adaptateur d'authentification : connecte AuthPort à auth_service."""
from __future__ import annotations

import sqlite3
from datetime import datetime

from app.database.connection import get_connection
from app.security.session import Session
from app.services.auth_service import login, AuthError, InvalidCredentials, AccountLocked, AccountDisabled
from app.ui.ports import LoginResult, LoginStatus, UserInfo, Role


class AuthAdapter:
    """Implémente AuthPort en utilisant auth_service."""

    def __init__(self) -> None:
        self._session = Session()

    def login(self, identifiant: str, password: str) -> LoginResult:
        try:
            conn = get_connection()
            current_user = login(conn, self._session, identifiant, password)
            conn.close()
            return LoginResult(
                LoginStatus.OK,
                UserInfo(
                    current_user.identifiant,
                    current_user.nom_complet,
                    current_user.role
                )
            )
        except InvalidCredentials as e:
            return LoginResult(LoginStatus.REFUSED, message=str(e))
        except AccountLocked as e:
            return LoginResult(LoginStatus.LOCKED, message=str(e))
        except AccountDisabled as e:
            return LoginResult(LoginStatus.REFUSED, message=str(e))
        except AuthError as e:
            return LoginResult(LoginStatus.REFUSED, message=str(e))
        except Exception as e:
            return LoginResult(LoginStatus.REFUSED, message=f"Erreur : {e}")

    @property
    def session(self) -> Session:
        return self._session
