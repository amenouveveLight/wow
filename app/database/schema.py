"""Schéma SQLite et migrations.

La version de la structure est stockée dans PRAGMA user_version.
Pour une évolution future : ajouter (2, SQL) à MIGRATIONS, ne jamais
modifier une migration déjà livrée.
"""
from __future__ import annotations

import sqlite3

SCHEMA_V1 = """
-- ───────────── Exercices (septembre → août) ─────────────
CREATE TABLE exercices (
    id           INTEGER PRIMARY KEY,
    libelle      TEXT NOT NULL UNIQUE,              -- ex. '2026-2027'
    date_debut   TEXT NOT NULL,                     -- AAAA-09-01
    date_fin     TEXT NOT NULL,                     -- AAAA+1-08-31
    statut       TEXT NOT NULL DEFAULT 'ouvert'
                 CHECK (statut IN ('ouvert', 'cloture')),
    date_cloture TEXT,
    CHECK (date_debut < date_fin)
);

-- Cotisation mensuelle : montant fixé selon le sexe (3.3), par exercice
CREATE TABLE tarifs_mensuels (
    exercice_id INTEGER NOT NULL REFERENCES exercices(id),
    sexe        TEXT NOT NULL CHECK (sexe IN ('M', 'F')),
    montant     INTEGER NOT NULL CHECK (montant >= 0),
    PRIMARY KEY (exercice_id, sexe)
);

-- ───────────── Utilisateurs et journal d'audit ─────────────
CREATE TABLE utilisateurs (
    id                INTEGER PRIMARY KEY,
    identifiant       TEXT NOT NULL UNIQUE COLLATE NOCASE,
    nom_complet       TEXT NOT NULL,
    mot_de_passe_hash TEXT NOT NULL,
    role              TEXT NOT NULL
                      CHECK (role IN ('administrateur', 'secretaire')),
    actif             INTEGER NOT NULL DEFAULT 1 CHECK (actif IN (0, 1)),
    cree_le           TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
-- Un seul administrateur (cahier des charges). Les 3 secrétaires maximum
-- sont contrôlés par le service des utilisateurs.
CREATE UNIQUE INDEX ux_un_seul_administrateur
    ON utilisateurs(role) WHERE role = 'administrateur';

CREATE TABLE journal_audit (
    id             INTEGER PRIMARY KEY,
    date_heure     TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    utilisateur_id INTEGER,                 -- volontairement sans clé étrangère
    identifiant    TEXT NOT NULL,           -- copie figée au moment de l'action
    role           TEXT NOT NULL,
    action         TEXT NOT NULL,
    objet          TEXT,
    detail         TEXT
);
CREATE TRIGGER journal_audit_pas_de_modification
BEFORE UPDATE ON journal_audit
BEGIN SELECT RAISE(ABORT, 'Le journal d''audit est en lecture seule.'); END;
CREATE TRIGGER journal_audit_pas_de_suppression
BEFORE DELETE ON journal_audit
BEGIN SELECT RAISE(ABORT, 'Le journal d''audit ne peut pas être effacé.'); END;

-- ───────────── Membres (3.1) ─────────────
CREATE TABLE membres (
    id            INTEGER PRIMARY KEY,
    numero_carnet TEXT NOT NULL UNIQUE,
    nom           TEXT NOT NULL,
    sexe          TEXT NOT NULL CHECK (sexe IN ('M', 'F')),
    date_adhesion TEXT NOT NULL,
    statut        TEXT NOT NULL DEFAULT 'actif'
                  CHECK (statut IN ('actif', 'decede')),
    date_deces    TEXT,
    cree_le       TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- ───────────── Cotisations funéraires (3.4) ─────────────
-- Chaque décès = une collecte avec ses propres montants selon le sexe.
CREATE TABLE deces (
    id                  INTEGER PRIMARY KEY,
    exercice_id         INTEGER NOT NULL REFERENCES exercices(id),
    nom_defunt          TEXT NOT NULL,
    type_deces          TEXT NOT NULL
                        CHECK (type_deces IN ('membre', 'parent', 'beau_parent', 'autre')),
    membre_defunt_id    INTEGER REFERENCES membres(id),
    date_deces          TEXT NOT NULL,
    montant_homme       INTEGER NOT NULL CHECK (montant_homme >= 0),
    montant_femme       INTEGER NOT NULL CHECK (montant_femme >= 0),
    membre_endeuille_id INTEGER REFERENCES membres(id),
    exempter_endeuille  INTEGER NOT NULL DEFAULT 0 CHECK (exempter_endeuille IN (0, 1)),
    cree_le             TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    CHECK (type_deces <> 'membre' OR membre_defunt_id IS NOT NULL)
);

-- ───────────── Cotisations parallèles (3.5) ─────────────
CREATE TABLE cotisations_paralleles (
    id            INTEGER PRIMARY KEY,
    exercice_id   INTEGER NOT NULL REFERENCES exercices(id),
    nom           TEXT NOT NULL,
    date_debut    TEXT NOT NULL,
    date_fin      TEXT NOT NULL,
    montant_homme INTEGER NOT NULL CHECK (montant_homme >= 0),
    montant_femme INTEGER NOT NULL CHECK (montant_femme >= 0),
    cree_le       TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    CHECK (date_debut <= date_fin)
);

-- ───────────── Versements (mensuel, funéraire, parallèle) ─────────────
CREATE TABLE versements (
    id                      INTEGER PRIMARY KEY,
    membre_id               INTEGER NOT NULL REFERENCES membres(id),
    exercice_id             INTEGER NOT NULL REFERENCES exercices(id),
    rubrique                TEXT NOT NULL
                            CHECK (rubrique IN ('mensuelle', 'funeraire', 'parallele')),
    cotisation_parallele_id INTEGER REFERENCES cotisations_paralleles(id),
    date_versement          TEXT NOT NULL,
    montant                 INTEGER NOT NULL CHECK (montant > 0),
    note                    TEXT,
    cree_par                INTEGER REFERENCES utilisateurs(id),
    cree_le                 TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    CHECK ((rubrique = 'parallele') = (cotisation_parallele_id IS NOT NULL))
);
CREATE INDEX ix_versements_membre ON versements(membre_id, exercice_id, rubrique);

-- ───────────── Amendes (3.7) ─────────────
CREATE TABLE amendes (
    id               INTEGER PRIMARY KEY,
    exercice_id      INTEGER NOT NULL REFERENCES exercices(id),
    membre_id        INTEGER NOT NULL REFERENCES membres(id),
    nom              TEXT NOT NULL,
    libelle          TEXT NOT NULL,
    date_amende      TEXT NOT NULL,
    montant_attendu  INTEGER NOT NULL CHECK (montant_attendu >= 0),
    montant_collecte INTEGER NOT NULL DEFAULT 0 CHECK (montant_collecte >= 0),
    cree_par         INTEGER REFERENCES utilisateurs(id),
    cree_le          TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- ───────────── Dépenses et reliquats (3.6, 3.8) ─────────────
CREATE TABLE depenses (
    id              INTEGER PRIMARY KEY,
    exercice_id     INTEGER NOT NULL REFERENCES exercices(id),
    date_depense    TEXT NOT NULL,
    libelle         TEXT NOT NULL,
    beneficiaire    TEXT,
    montant_prevu   INTEGER NOT NULL CHECK (montant_prevu >= 0),
    montant_depense INTEGER NOT NULL CHECK (montant_depense >= 0),
    cree_par        INTEGER REFERENCES utilisateurs(id),
    cree_le         TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- Reliquat = entrée liée à sa dépense d'origine (une seule par dépense)
CREATE TABLE reliquats (
    id           INTEGER PRIMARY KEY,
    exercice_id  INTEGER NOT NULL REFERENCES exercices(id),
    depense_id   INTEGER NOT NULL UNIQUE REFERENCES depenses(id) ON DELETE CASCADE,
    nom          TEXT NOT NULL,
    montant      INTEGER NOT NULL CHECK (montant > 0),
    date_reliquat TEXT NOT NULL,
    cree_le      TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- ───────────── Reports à la clôture (3.2) ─────────────
CREATE TABLE reports (
    id                 INTEGER PRIMARY KEY,
    exercice_source_id INTEGER NOT NULL REFERENCES exercices(id),
    exercice_cible_id  INTEGER NOT NULL REFERENCES exercices(id),
    membre_id          INTEGER REFERENCES membres(id),     -- NULL = solde global
    type               TEXT NOT NULL CHECK (type IN ('dette', 'avance', 'solde')),
    rubrique           TEXT,
    montant            INTEGER NOT NULL CHECK (montant >= 0),
    cree_le            TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- ───────────── Paramètres généraux ─────────────
CREATE TABLE parametres (
    cle    TEXT PRIMARY KEY,
    valeur TEXT NOT NULL
);
"""

# (numéro de version, script SQL) — à compléter pour les futures évolutions
SCHEMA_V2 = """
-- Blocage temporaire après des échecs de connexion répétés
ALTER TABLE utilisateurs ADD COLUMN tentatives_echouees INTEGER NOT NULL DEFAULT 0;
ALTER TABLE utilisateurs ADD COLUMN verrouille_jusqua TEXT;
"""
SCHEMA_V3 = """
-- Cotisation funéraire : montant fixé selon le sexe uniquement, par exercice
CREATE TABLE tarifs_funeraires (
    exercice_id INTEGER NOT NULL REFERENCES exercices(id),
    sexe        TEXT NOT NULL CHECK (sexe IN ('M', 'F')),
    montant     INTEGER NOT NULL CHECK (montant >= 0),
    PRIMARY KEY (exercice_id, sexe)
);
"""

SCHEMA_V4 = """
-- La table des reports n'a pas encore servi : on la reconstruit pour
-- 1) autoriser un solde négatif (déficit reporté),
-- 2) autoriser une reprise initiale sans exercice source.
DROP TABLE reports;
CREATE TABLE reports (
    id                 INTEGER PRIMARY KEY,
    exercice_source_id INTEGER REFERENCES exercices(id),     -- NULL = reprise initiale
    exercice_cible_id  INTEGER NOT NULL REFERENCES exercices(id),
    membre_id          INTEGER REFERENCES membres(id),       -- NULL = solde global
    type               TEXT NOT NULL CHECK (type IN ('dette', 'avance', 'solde')),
    rubrique           TEXT CHECK (rubrique IN ('mensuelle', 'funeraire', 'parallele', 'amende')),
    montant            INTEGER NOT NULL,
    cree_le            TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    CHECK ((type = 'solde') = (membre_id IS NULL)),
    CHECK (type = 'solde' OR montant > 0)
);
CREATE INDEX ix_reports_cible ON reports(exercice_cible_id, membre_id);
"""

SCHEMA_V5 = """
-- Historique des encaissements d'amendes : une ligne par encaissement
CREATE TABLE encaissements_amendes (
    id                INTEGER PRIMARY KEY,
    amende_id         INTEGER NOT NULL REFERENCES amendes(id) ON DELETE CASCADE,
    montant           INTEGER NOT NULL CHECK (montant > 0),
    date_encaissement TEXT NOT NULL,
    cree_par          INTEGER REFERENCES utilisateurs(id),
    cree_le           TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
CREATE INDEX ix_encaissements_amende ON encaissements_amendes(amende_id);

-- Reprise des encaissements déjà enregistrés dans le champ de collecte
INSERT INTO encaissements_amendes (amende_id, montant, date_encaissement, cree_par)
SELECT id, montant_collecte, date_amende, cree_par FROM amendes WHERE montant_collecte > 0;
"""
SCHEMA_V6 = """
-- Paiement des arriérés : nature (courant / arriéré), exercice d'origine, numéro de reçu
CREATE TABLE versements_v6 (
    id                      INTEGER PRIMARY KEY,
    membre_id               INTEGER NOT NULL REFERENCES membres(id),
    exercice_id             INTEGER NOT NULL REFERENCES exercices(id),
    rubrique                TEXT NOT NULL
                            CHECK (rubrique IN ('mensuelle', 'funeraire', 'parallele', 'amende')),
    nature                  TEXT NOT NULL DEFAULT 'courant' CHECK (nature IN ('courant', 'arriere')),
    cotisation_parallele_id INTEGER REFERENCES cotisations_paralleles(id),
    exercice_origine_id     INTEGER REFERENCES exercices(id),
    recu                    INTEGER,
    date_versement          TEXT NOT NULL,
    montant                 INTEGER NOT NULL CHECK (montant > 0),
    note                    TEXT,
    cree_par                INTEGER REFERENCES utilisateurs(id),
    cree_le                 TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    CHECK (nature = 'arriere' OR rubrique <> 'amende'),
    CHECK (nature = 'courant' OR rubrique <> 'mensuelle'),
    CHECK (nature = 'courant' OR (exercice_origine_id IS NOT NULL AND cotisation_parallele_id IS NULL)),
    CHECK (nature = 'arriere' OR exercice_origine_id IS NULL),
    CHECK (nature = 'arriere' OR ((rubrique = 'parallele') = (cotisation_parallele_id IS NOT NULL)))
);
INSERT INTO versements_v6 (id, membre_id, exercice_id, rubrique, cotisation_parallele_id,
                           date_versement, montant, note, cree_par, cree_le)
SELECT id, membre_id, exercice_id, rubrique, cotisation_parallele_id,
       date_versement, montant, note, cree_par, cree_le FROM versements;
DROP TABLE versements;
ALTER TABLE versements_v6 RENAME TO versements;
CREATE INDEX ix_versements_membre ON versements(membre_id, exercice_id, rubrique);
CREATE INDEX ix_versements_recu ON versements(recu);

-- Reports : on garde l'exercice d'origine de chaque dette (arriérés « de 2025-2026 »)
ALTER TABLE reports ADD COLUMN exercice_origine_id INTEGER REFERENCES exercices(id);
UPDATE reports SET exercice_origine_id = exercice_source_id WHERE type <> 'solde';
"""

# (numéro de version, script SQL) — à compléter pour les futures évolutions
MIGRATIONS: list[tuple[int, str]] = [
    (1, SCHEMA_V1),
    (2, SCHEMA_V2),
    (3, SCHEMA_V3),
    (4, SCHEMA_V4),
    (5, SCHEMA_V5),
    (6, SCHEMA_V6),
]

# (numéro de version, script SQL) — à compléter pour les futures évolutions


LATEST_VERSION = MIGRATIONS[-1][0]


def get_version(conn: sqlite3.Connection) -> int:
    return conn.execute("PRAGMA user_version").fetchone()[0]


def migrate(conn: sqlite3.Connection) -> int:
    """Amène la base à la dernière version. Retourne la version atteinte.

    Chaque migration s'exécute dans une transaction : en cas d'erreur,
    la base reste dans son état précédent.
    """
    for version, sql in MIGRATIONS:
        if version <= get_version(conn):
            continue
        try:
            conn.executescript(f"BEGIN;\n{sql}\nPRAGMA user_version = {version};\nCOMMIT;")
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
    return get_version(conn)