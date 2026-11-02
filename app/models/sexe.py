# app/models/sexe.py
"""Sexe du membre : détermine les montants (cotisations mensuelle, funéraire, parallèle)."""
from __future__ import annotations

from enum import Enum


class Sexe(str, Enum):
    HOMME = "M"
    FEMME = "F"

    @property
    def label(self) -> str:
        return "Homme" if self is Sexe.HOMME else "Femme"