"""Contrat de la page Membres : types échangés entre l'interface et les services."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol


class MemberStatus:
    ACTIF = "actif"
    DECEDE = "decede"


@dataclass(frozen=True)
class MemberInfo:
    carnet: str           # « 001 »
    name: str
    sex: str              # 'M' | 'F'
    joined_on: date
    status: str           # MemberStatus
    du: int               # montant dû sur l'exercice
    recu: int             # montant reçu sur l'exercice


@dataclass(frozen=True)
class MembersData:
    exercise_label: str
    is_open: bool
    members: tuple[MemberInfo, ...]


class MembersPort(Protocol):
    """Liste des membres : MockMembers aujourd'hui, services demain."""

    def load(self, exercise_label: str) -> MembersData: ...
