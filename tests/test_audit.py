# tests/test_audit.py
import sqlite3
import unittest

from app.database.schema import migrate
from app.security import audit
from app.security.audit import Action
from app.security.session import CurrentUser, Role


class AuditTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        migrate(self.conn)
        self.admin = CurrentUser(1, "ama", "Ama K.", Role.ADMINISTRATEUR)
        self.sec = CurrentUser(2, "yawa", "Yawa D.", Role.SECRETAIRE)

    def test_log_utilisateur(self):
        audit.log(self.conn, self.sec, Action.VERSEMENT_AJOUT, "Carnet 009", "5 000 FCFA")
        e = audit.list_entries(self.conn)[0]
        self.assertEqual((e["identifiant"], e["role"], e["action"]), ("yawa", "secretaire", Action.VERSEMENT_AJOUT))

    def test_log_systeme_et_echec(self):
        audit.log(self.conn, None, Action.SAUVEGARDE)
        audit.log(self.conn, None, Action.ECHEC_CONNEXION, identifiant="inconnu1")
        rows = audit.list_entries(self.conn)
        self.assertEqual(rows[0]["role"], "inconnu")
        self.assertEqual(rows[1]["identifiant"], "système")

    def test_filtres_et_comptage(self):
        audit.log(self.conn, self.admin, Action.CONNEXION)
        audit.log(self.conn, self.sec, Action.MEMBRE_AJOUT, "Carnet 043")
        audit.log(self.conn, self.sec, Action.VERSEMENT_AJOUT, "Carnet 009")
        self.assertEqual(audit.count_entries(self.conn), 3)
        self.assertEqual(audit.count_entries(self.conn, identifiant="yawa"), 2)
        self.assertEqual(audit.count_entries(self.conn, recherche="043"), 1)
        self.assertEqual(len(audit.list_entries(self.conn, limit=2)), 2)

    def test_rollback_annule_aussi_le_journal(self):
        try:
            self.conn.execute("BEGIN")
            audit.log(self.conn, self.admin, Action.CLOTURE)
            raise RuntimeError("échec de l'opération")
        except RuntimeError:
            self.conn.rollback()
        self.assertEqual(audit.count_entries(self.conn), 0)


if __name__ == "__main__":
    unittest.main()