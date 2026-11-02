import sqlite3
import unittest

from app.database.schema import LATEST_VERSION, get_version, migrate


class SchemaTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute("PRAGMA foreign_keys = ON")
        migrate(self.conn)

    def test_version(self):
        self.assertEqual(get_version(self.conn), LATEST_VERSION)

    def test_numero_carnet_unique(self):
        sql = "INSERT INTO membres (numero_carnet, nom, sexe, date_adhesion) VALUES (?, ?, ?, ?)"
        self.conn.execute(sql, ("001", "A", "M", "2026-09-01"))
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(sql, ("001", "B", "F", "2026-09-01"))

    def test_un_seul_administrateur(self):
        sql = "INSERT INTO utilisateurs (identifiant, nom_complet, mot_de_passe_hash, role) VALUES (?, ?, 'x', ?)"
        self.conn.execute(sql, ("admin", "Admin", "administrateur"))
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(sql, ("admin2", "Autre", "administrateur"))

    def test_journal_audit_intouchable(self):
        self.conn.execute(
            "INSERT INTO journal_audit (identifiant, role, action) VALUES ('admin', 'administrateur', 'test')"
        )
        with self.assertRaises(sqlite3.DatabaseError):
            self.conn.execute("UPDATE journal_audit SET action = 'x'")
        with self.assertRaises(sqlite3.DatabaseError):
            self.conn.execute("DELETE FROM journal_audit")

    def test_versement_parallele_exige_sa_cotisation(self):
        self.conn.execute("INSERT INTO exercices (libelle, date_debut, date_fin) VALUES ('2026-2027', '2026-09-01', '2027-08-31')")
        self.conn.execute("INSERT INTO membres (numero_carnet, nom, sexe, date_adhesion) VALUES ('001', 'A', 'M', '2026-09-01')")
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "INSERT INTO versements (membre_id, exercice_id, rubrique, date_versement, montant) "
                "VALUES (1, 1, 'parallele', '2026-10-01', 5000)"
            )


if __name__ == "__main__":
    unittest.main()