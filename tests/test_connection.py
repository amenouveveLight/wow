import unittest

from app.database.connection import get_connection, transaction


class TransactionTest(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")
        self.addCleanup(self.conn.close)
        self.conn.execute("CREATE TABLE t (v TEXT)")

    def _values(self):
        return [r["v"] for r in self.conn.execute("SELECT v FROM t ORDER BY rowid")]

    def test_validation(self):
        with transaction(self.conn):
            self.conn.execute("INSERT INTO t VALUES ('a')")
        self.assertFalse(self.conn.in_transaction)
        self.assertEqual(self._values(), ["a"])

    def test_erreur_annule_tout(self):
        with self.assertRaises(RuntimeError):
            with transaction(self.conn):
                self.conn.execute("INSERT INTO t VALUES ('a')")
                raise RuntimeError("échec")
        self.assertEqual(self._values(), [])

    def test_transaction_imbriquee_annule_seulement_l_interieur(self):
        with transaction(self.conn):
            self.conn.execute("INSERT INTO t VALUES ('externe')")
            try:
                with transaction(self.conn):
                    self.conn.execute("INSERT INTO t VALUES ('interne')")
                    raise RuntimeError("échec interne")
            except RuntimeError:
                pass
        self.assertEqual(self._values(), ["externe"])

    def test_ecriture_hors_transaction_ne_bloque_pas_la_suivante(self):
        self.conn.execute("INSERT INTO t VALUES ('brut')")
        with transaction(self.conn):
            self.conn.execute("INSERT INTO t VALUES ('b')")
        self.assertEqual(self._values(), ["brut", "b"])
        self.assertFalse(self.conn.in_transaction)


if __name__ == "__main__":
    unittest.main()