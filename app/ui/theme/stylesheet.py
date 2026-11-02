"""Fabrique la feuille de style Qt : fichiers .qss (modèles) + jetons de tokens.py."""
from __future__ import annotations

import re

from app.ui.paths import ICONS_DIR, QSS_FILES
from app.ui.theme import tokens

_TOKEN = re.compile(r"@([a-z0-9_]+)")
_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)


def build() -> str:
    """Assemble les .qss, retire les commentaires, puis remplace chaque @jeton par sa valeur.
    Un jeton inconnu lève une KeyError (mieux qu'un style silencieusement cassé)."""
    mapping = tokens.mapping()
    chevron = ICONS_DIR / "chevron-down-gray.svg"
    if not chevron.exists():
        raise FileNotFoundError(f"Icône manquante : {chevron.name}. Lancez : python scripts\\generate_icons.py")
    mapping["chevron_url"] = chevron.as_posix()

    texte = "\n".join(chemin.read_text(encoding="utf-8") for chemin in QSS_FILES)
    texte = _COMMENT.sub("", texte)        # les commentaires peuvent citer « @nom » sans erreur

    def remplacer(match: re.Match) -> str:
        cle = match.group(1)
        if cle not in mapping:
            raise KeyError(f"Jeton inconnu dans les fichiers .qss : @{cle}")
        return mapping[cle]

    return _TOKEN.sub(remplacer, texte)