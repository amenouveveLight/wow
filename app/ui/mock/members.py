"""Membres fictifs de démonstration : 42 membres dont 2 décédés (remplacés plus tard par les services)."""
from __future__ import annotations

from dataclasses import replace
from datetime import date

from app.ui.ports_members import MemberInfo, MembersData, MemberStatus

_REFERENCE = "2025–2026"
_PRENOMS = {
    "M": ("Mawuli", "Kodjo", "Komi", "Edem", "Yao", "Senyo", "Kwami", "Dodzi", "Kafui", "Têko"),
    "F": ("Ama", "Akossiwa", "Afi", "Mawusi", "Elom", "Sédjro", "Adjo", "Enyonam", "Kokou", "Delali"),
}
_NOMS = ("Agbeko", "Atsou", "Lawson", "Gbedemah", "Tété", "Amegah", "Adjovi", "Mensah",
         "Dosseh", "Kpodar", "Houngbo", "Sossou", "Aziabu", "Fiawoo")


def _premiers() -> list[MemberInfo]:
    a, d = MemberStatus.ACTIF, MemberStatus.DECEDE
    return [
        MemberInfo("001", "Komlan Akakpo", "M", date(2017, 9, 5), a, 216_000, 216_000),
        MemberInfo("002", "Abla Tsogbé", "F", date(2017, 9, 5), a, 168_000, 180_000),
        MemberInfo("003", "Koffi Dzakpasu", "M", date(2017, 9, 19), a, 216_000, 216_000),
        MemberInfo("004", "Sika Amouzou", "F", date(2017, 10, 3), a, 168_000, 168_000),
        MemberInfo("005", "Kossi Ayité", "M", date(2017, 10, 3), d, 126_000, 126_000),
        MemberInfo("006", "Efua Dosseh", "F", date(2017, 10, 17), a, 168_000, 150_000),
        MemberInfo("007", "Selom Ahiabor", "M", date(2017, 11, 7), a, 216_000, 216_000),
        MemberInfo("008", "Dzifa Kuwonu", "F", date(2017, 11, 7), a, 168_000, 168_000),
        MemberInfo("009", "Yawo Agbodjan", "M", date(2017, 11, 21), a, 216_000, 131_000),
        MemberInfo("010", "Ayélé Amoussou", "F", date(2017, 12, 5), a, 168_000, 175_000),
    ]


def _generes() -> list[MemberInfo]:
    membres = []
    for n in range(11, 43):
        sexe = "M" if n % 2 else "F"
        du = 216_000 if sexe == "M" else 168_000
        recu = du
        if n % 7 == 0:
            recu = du - 24_000
        elif n % 11 == 0:
            recu = du + 12_000
        statut = MemberStatus.ACTIF
        if n == 31:
            statut, du, recu = MemberStatus.DECEDE, 126_000, 126_000
        nom = f"{_PRENOMS[sexe][n % 10]} {_NOMS[(n * 3) % len(_NOMS)]}"
        entree = date(2018 + (n - 11) // 8, 1 + (n * 5) % 12, 1 + (n * 7) % 28)
        membres.append(MemberInfo(f"{n:03d}", nom, sexe, entree, statut, du, recu))
    return membres


_MEMBRES = tuple(_premiers() + _generes())


class MockMembers:
    """Aucun accès à la base. Les exercices clôturés sont soldés : reçu = dû."""

    def load(self, exercise_label: str) -> MembersData:
        if exercise_label == _REFERENCE:
            return MembersData(exercise_label, True, _MEMBRES)
        soldes = tuple(replace(m, recu=m.du) for m in _MEMBRES)
        return MembersData(exercise_label, False, soldes)
