"""Hachage et vérification des mots de passe (bibliothèque standard uniquement).

Format stocké : pbkdf2_sha256$<itérations>$<sel hex>$<hash hex>
Le mot de passe n'est jamais stocké ni journalisé en clair.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 600_000          # recommandation OWASP pour PBKDF2-SHA256
SALT_BYTES = 16
MIN_LENGTH = 8


class PasswordPolicyError(ValueError):
    """Le mot de passe ne respecte pas les règles minimales."""


def validate_policy(password: str) -> None:
    """Règles minimales : 8 caractères, au moins une lettre et un chiffre."""
    if len(password) < MIN_LENGTH:
        raise PasswordPolicyError(
            f"Le mot de passe doit contenir au moins {MIN_LENGTH} caractères."
        )
    if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        raise PasswordPolicyError(
            "Le mot de passe doit contenir au moins une lettre et un chiffre."
        )


def _derive(password: str, salt: bytes, iterations: int) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)


def hash_password(password: str) -> str:
    """Retourne le hash à enregistrer dans utilisateurs.mot_de_passe_hash."""
    salt = secrets.token_bytes(SALT_BYTES)
    digest = _derive(password, salt, ITERATIONS)
    return f"{ALGORITHM}${ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Vérifie un mot de passe (comparaison à temps constant)."""
    try:
        algorithm, iterations, salt_hex, digest_hex = stored_hash.split("$")
        if algorithm != ALGORITHM:
            return False
        expected = bytes.fromhex(digest_hex)
        candidate = _derive(password, bytes.fromhex(salt_hex), int(iterations))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(candidate, expected)


def needs_rehash(stored_hash: str) -> bool:
    """True si le hash a été fait avec moins d'itérations que l'actuel."""
    try:
        _, iterations, _, _ = stored_hash.split("$")
        return int(iterations) < ITERATIONS
    except (ValueError, TypeError):
        return True