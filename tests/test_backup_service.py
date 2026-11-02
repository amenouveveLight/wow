import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from app.database.connection import get_connection
from app.database.schema import migrate
from app.models.sexe import Sexe
from app.security import audit
from app.security.audit import Action
from app.security.session import CurrentUser, PermissionDenied, Role, Session
from app.services import backup_service as svc
from app.services import membre_service
from app.services.backup_service import BackupError

NOW = datetime(2026, 8, 28, 17, 42, 10)


def nb_membres(path) -> int:
    conn = sqlite3.connect(str(path))
    try:
        return conn.execute("SELECT COUNT(*) FROM membres").fetchone()[0]
    finally:
        conn.close()


class BackupServiceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.db_path = self.dir / "association.db"
        self.backups = self.dir / "sauvegardes"
        self.conn = get_connection(self.db_path)
        self.addCleanup(self.conn.close)               # exécuté avant le nettoyage du dossier
        migrate(self.conn)
        self.admin, self.sec = Session(), Session()
        self.admin.login(CurrentUser(1, "ama", "Ama K.", Role.ADMINISTRATEUR))
        self.sec.login(CurrentUser(2, "yawa", "Yawa D.", Role.SECRETAIRE))

    def _membre(self, nom):
        membre_service.create_membre(self.conn, self.admin, nom, Sexe.HOMME, None)

    def test_sauvegarde_manuelle(self):
        self._membre("Premier Membre")
        self._membre("Second Membre")
        p = svc.sauvegarder_manuelle(self.conn, self.admin, self.backups, now=NOW)
        self.assertEqual(p.name, "association_20260828_174210_m.db")
        self.assertEqual(nb_membres(p), 2)
        self.assertEqual(svc.verifier_fichier(p), (True, "ok"))
        e = audit.list_entries(self.conn)[0]
        self.assertEqual((e["action"], e["objet"], e["identifiant"]), (Action.SAUVEGARDE, p.name, "ama"))
        liste = svc.lister(self.backups)
        self.assertEqual([(s.kind, s.created) for s in liste], [(svc.MANUELLE, NOW)])
        with self.assertRaises(PermissionDenied):
            svc.sauvegarder_manuelle(self.conn, self.sec, self.backups, now=NOW + timedelta(minutes=1))

    def test_sauvegarde_automatique_par_le_systeme(self):
        p = svc.sauvegarder_automatique(self.conn, self.backups, now=NOW)
        self.assertTrue(p.name.endswith("_a.db"))
        e = audit.list_entries(self.conn)[0]
        self.assertEqual((e["action"], e["identifiant"], e["role"]), (Action.SAUVEGARDE, "système", "système"))

    def test_rotation_des_30_dernieres_copies_automatiques(self):
        manuelle = svc.sauvegarder_manuelle(self.conn, self.admin, self.backups, now=NOW - timedelta(days=1))
        for i in range(33):
            svc.sauvegarder_automatique(self.conn, self.backups, now=NOW + timedelta(minutes=i))
        liste = svc.lister(self.backups)
        autos = [s for s in liste if s.kind == svc.AUTOMATIQUE]
        self.assertEqual(len(autos), 30)
        self.assertEqual(autos[0].created, NOW + timedelta(minutes=32))            # la plus récente d'abord
        self.assertEqual(autos[-1].created, NOW + timedelta(minutes=3))            # les 3 plus anciennes supprimées
        self.assertTrue(manuelle.exists())                                         # jamais supprimée
        self.assertEqual(len(liste), 31)

    def test_controle_d_integrite(self):
        p = svc.sauvegarder_automatique(self.conn, self.backups, now=NOW)
        self.assertEqual(svc.verifier_integrite(self.conn), (True, "ok"))
        self.assertEqual(svc.verifier_fichier(p), (True, "ok"))
        abime = self.dir / "abime.db"
        abime.write_bytes(b"ceci n'est pas une base de donnees " * 100)
        self.assertFalse(svc.verifier_fichier(abime)[0])
        vide = self.dir / "vide.db"
        sqlite3.connect(str(vide)).close()
        ok, message = svc.verifier_fichier(vide)
        self.assertFalse(ok)
        self.assertIn("pas une sauvegarde", message)
        self.assertFalse(svc.verifier_fichier(self.dir / "absent.db")[0])

    def test_restauration_avec_copie_de_securite(self):
        self._membre("Premier Membre")
        p = svc.sauvegarder_manuelle(self.conn, self.admin, self.backups, now=NOW)
        self._membre("Second Membre")
        self.conn.close()

        securite = svc.restaurer(self.admin, p, self.db_path, self.backups, now=NOW + timedelta(minutes=5))
        self.assertTrue(securite.name.endswith("_s.db"))
        self.assertEqual(nb_membres(securite), 2)                  # la base remplacée est conservée
        self.assertEqual(nb_membres(self.db_path), 1)              # retour à l'état de la sauvegarde
        restauree = get_connection(self.db_path)
        self.addCleanup(restauree.close)
        e = audit.list_entries(restauree, action=Action.RESTAURATION)
        self.assertEqual(len(e), 1)
        self.assertEqual((e[0]["identifiant"], e[0]["objet"]), ("ama", p.name))
        self.assertIn(securite.name, e[0]["detail"])

    def test_restauration_refusee_sans_toucher_a_la_base(self):
        self._membre("Premier Membre")
        bonne = svc.sauvegarder_manuelle(self.conn, self.admin, self.backups, now=NOW)
        self._membre("Second Membre")
        self.conn.close()

        abime = self.backups / "association_20260101_000000_m.db"
        abime.write_bytes(b"corrompu" * 500)
        with self.assertRaises(BackupError):
            svc.restaurer(self.admin, abime, self.db_path, self.backups)

        trop_recent = self.backups / "association_20260102_000000_m.db"
        trop_recent.write_bytes(bonne.read_bytes())
        c = sqlite3.connect(str(trop_recent))
        c.execute("PRAGMA user_version = 99")
        c.close()
        with self.assertRaises(BackupError):
            svc.restaurer(self.admin, trop_recent, self.db_path, self.backups)

        with self.assertRaises(PermissionDenied):
            svc.restaurer(self.sec, bonne, self.db_path, self.backups)
        self.assertEqual(nb_membres(self.db_path), 2)              # la base n'a pas bougé
        self.assertEqual([s for s in svc.lister(self.backups) if s.kind == svc.SECURITE], [])


if __name__ == "__main__":
    unittest.main()