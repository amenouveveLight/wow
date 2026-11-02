"""Historique unifié des transactions (SQL uniquement).

Réunit en lecture : versements (courants et arriérés), encaissements d'amendes,
reliquats (entrées) et dépenses (sorties). Rien n'est stocké en double.
"""
from __future__ import annotations

import sqlite3
from datetime import date

from app.models.transaction import Transaction

_UNION = """
SELECT 'versement' AS source, v.id AS source_id, v.date_versement AS date_operation,
       v.rubrique AS rubrique, 'entree' AS sens, v.montant AS montant,
       v.membre_id AS membre_id, m.nom AS membre_nom, m.numero_carnet AS numero_carnet,
       CASE WHEN v.nature = 'arriere' THEN 'Arriérés — ' ||
                 CASE v.rubrique WHEN 'funeraire' THEN 'cotisation funéraire'
                                 WHEN 'parallele' THEN 'cotisation parallèle'
                                 ELSE 'amende' END
            WHEN v.rubrique = 'mensuelle' THEN 'Cotisation mensuelle'
            WHEN v.rubrique = 'funeraire' THEN 'Cotisation funéraire'
            ELSE 'Cotisation parallèle « ' || cp.nom || ' »' END AS libelle,
       NULL AS beneficiaire, v.note AS note,
       COALESCE(u.identifiant, 'système') AS saisi_par, v.cree_le AS cree_le,
       v.exercice_id AS exercice_id, v.nature AS nature,
       CASE WHEN v.nature = 'arriere' THEN 'Arriérés de ' || eo.libelle
            ELSE 'Exercice ' || ex.libelle END AS periode,
       v.recu AS recu
FROM versements v
JOIN membres m ON m.id = v.membre_id
JOIN exercices ex ON ex.id = v.exercice_id
LEFT JOIN exercices eo ON eo.id = v.exercice_origine_id
LEFT JOIN cotisations_paralleles cp ON cp.id = v.cotisation_parallele_id
LEFT JOIN utilisateurs u ON u.id = v.cree_par
UNION ALL
SELECT 'amende', e.id, e.date_encaissement, 'amende', 'entree', e.montant,
       a.membre_id, m.nom, m.numero_carnet, 'Amende « ' || a.nom || ' »', NULL, NULL,
       COALESCE(u.identifiant, 'système'), e.cree_le, a.exercice_id,
       'courant', 'Exercice ' || ex.libelle, NULL
FROM encaissements_amendes e
JOIN amendes a ON a.id = e.amende_id
JOIN membres m ON m.id = a.membre_id
JOIN exercices ex ON ex.id = a.exercice_id
LEFT JOIN utilisateurs u ON u.id = e.cree_par
UNION ALL
SELECT 'reliquat', r.id, r.date_reliquat, 'reliquat', 'entree', r.montant,
       NULL, NULL, NULL, r.nom, NULL, NULL,
       COALESCE(u.identifiant, 'système'), r.cree_le, r.exercice_id,
       'courant', 'Exercice ' || ex.libelle, NULL
FROM reliquats r
JOIN depenses d ON d.id = r.depense_id
JOIN exercices ex ON ex.id = r.exercice_id
LEFT JOIN utilisateurs u ON u.id = d.cree_par
UNION ALL
SELECT 'depense', d.id, d.date_depense, 'depense', 'sortie', d.montant_depense,
       NULL, NULL, NULL, d.libelle, d.beneficiaire, NULL,
       COALESCE(u.identifiant, 'système'), d.cree_le, d.exercice_id,
       'courant', 'Exercice ' || ex.libelle, NULL
FROM depenses d
JOIN exercices ex ON ex.id = d.exercice_id
LEFT JOIN utilisateurs u ON u.id = d.cree_par
WHERE d.montant_depense > 0
"""


def _where(exercice_id, search, rubrique, sens, nature, date_debut, date_fin, membre_id):
    clauses, params = [], []
    if exercice_id is not None:
        clauses.append("exercice_id = ?")
        params.append(exercice_id)
    if rubrique:
        clauses.append("rubrique = ?")
        params.append(rubrique)
    if sens:
        clauses.append("sens = ?")
        params.append(sens)
    if nature:
        clauses.append("nature = ?")
        params.append(nature)
    if date_debut:
        clauses.append("date_operation >= ?")
        params.append(date_debut.isoformat())
    if date_fin:
        clauses.append("date_operation <= ?")
        params.append(date_fin.isoformat())
    if membre_id is not None:
        clauses.append("membre_id = ?")
        params.append(membre_id)
    if search:
        clauses.append("(libelle LIKE ? OR membre_nom LIKE ? OR numero_carnet LIKE ? "
                       "OR beneficiaire LIKE ? OR note LIKE ? OR saisi_par LIKE ?)")
        params += [f"%{search}%"] * 6
    return (" WHERE " + " AND ".join(clauses)) if clauses else "", params


def list_(conn: sqlite3.Connection, *, exercice_id: int | None = None, search: str | None = None,
          rubrique: str | None = None, sens: str | None = None, nature: str | None = None,
          date_debut: date | None = None, date_fin: date | None = None,
          membre_id: int | None = None, limit: int | None = None,
          offset: int = 0) -> list[Transaction]:
    """Les plus récentes d'abord."""
    where, params = _where(exercice_id, search, rubrique, sens, nature, date_debut, date_fin, membre_id)
    sql = (f"WITH t AS ({_UNION}) SELECT * FROM t{where} "
           "ORDER BY date_operation DESC, cree_le DESC, source_id DESC")
    if limit is not None:
        sql += " LIMIT ? OFFSET ?"
        params += [limit, offset]
    return [Transaction.from_row(r) for r in conn.execute(sql, params).fetchall()]


def totals(conn: sqlite3.Connection, *, exercice_id: int | None = None, search: str | None = None,
           rubrique: str | None = None, sens: str | None = None, nature: str | None = None,
           date_debut: date | None = None, date_fin: date | None = None,
           membre_id: int | None = None) -> tuple[int, int, int]:
    """(total des entrées, total des sorties, nombre de transactions) du résultat filtré."""
    where, params = _where(exercice_id, search, rubrique, sens, nature, date_debut, date_fin, membre_id)
    row = conn.execute(
        f"WITH t AS ({_UNION}) SELECT "
        "COALESCE(SUM(CASE WHEN sens = 'entree' THEN montant END), 0), "
        "COALESCE(SUM(CASE WHEN sens = 'sortie' THEN montant END), 0), COUNT(*) "
        f"FROM t{where}",
        params,
    ).fetchone()
    return int(row[0]), int(row[1]), int(row[2])