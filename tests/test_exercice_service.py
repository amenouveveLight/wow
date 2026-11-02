import sqlite3
import unittest
from datetime import date

from app.database.schema import migrate
from app.models.sexe import Sexe
from app.security import audit
from app.security.audit import Action
from app.security.session import CurrentUser, Role, Session
from app.services import calendrier
from app.services import exercice_service as svc
from app.services.exercice_service import ExerciceError
from app.security.session import PermissionDenied


class CalendrierTest(unittest.TestCase):
    def test_annee_de_debut(self):
        self.assertEqual(calendrier.start_year_for_date(date(2026, 9, 1)), 2026)
        self.assertEqual(calendrier.start_year_for_date(date(2027, 8, 31)), 2026)
        self.assertEqual(calendrier.start_year_for_date(date(2026, 8, 31)), 2025)

    def test_libelle_et_bornes(self):
        self.assertEqual(calendrier.libelle(2026), "2026-2027")
        self.assertEqual(calendrier.start_year_from_libelle("2026-2027"), 2026)
        with self.assertRaises(ValueError):
            calendrier.start_year_from_libelle("2026-2028")
        self.assertEqual(calendrier.bounds(2026), (date(2026, 9, 1), date(2027, 8, 31)))

    def test_douze_mois_septembre_a_aout(self):
        months = calendrier.exercise_months(2026)
        self.assertEqual(len(months), 12)
        self.assertEqual(months[0], (2026, 9))
        self.assertEqual(months[3], (2026, 12))
        self.assertEqual(months[4], (2027, 1))
        self.assertEqual(months[-1], (2027, 8))
        self.assertEqual(calendrier.month_label(9), "Septembre")


class ExerciceServiceTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        migrate(self.conn)
        self.session = Session()
        self.session.login(CurrentUser(1, "ama", "Ama K.", Role.ADMINISTRATEUR))

    def test_creation(self):
        e = svc.create_exercice(self.conn, self.session, 2026, 1500, 1200)
        self.assertEqual(e.libelle, "2026-2027")
        self.assertTrue(e.is_open)
        self.assertEqual(svc.get_tarifs(self.conn, e.id), {Sexe.HOMME: 1500, Sexe.FEMME: 1200})
        self.assertEqual(audit.list_entries(self.conn)[0]["action"], Action.EXERCICE_CREATION)

    def test_doublon_refuse(self):
        svc.create_exercice(self.conn, self.session, 2026, 1500, 1200)
        with self.assertRaises(ExerciceError):
            svc.create_exercice(self.conn, self.session, 2026, 1500, 1200)

    def test_montants_invalides(self):
        for h, f in ((-1, 1000), (1000, 12.5), (True, 1000)):
            with self.assertRaises(ExerciceError):
                svc.create_exercice(self.conn, self.session, 2026, h, f)
        self.assertEqual(svc.list_exercices(self.conn), [])

    def test_secretaire_refuse(self):
        sec = Session()
        sec.login(CurrentUser(2, "yawa", "Yawa D.", Role.SECRETAIRE))
        with self.assertRaises(PermissionDenied):
            svc.create_exercice(self.conn, sec, 2026, 1500, 1200)

    def test_modification_des_tarifs_journalisee(self):
        e = svc.create_exercice(self.conn, self.session, 2026, 1500, 1200)
        svc.set_tarifs(self.conn, self.session, e.id, 2000, 1500)
        self.assertEqual(svc.get_tarifs(self.conn, e.id)[Sexe.HOMME], 2000)
        self.assertEqual(audit.list_entries(self.conn)[0]["action"], Action.TARIFS_MODIF)

    def test_exercice_cloture_non_modifiable(self):
        e = svc.create_exercice(self.conn, self.session, 2026, 1500, 1200)
        self.conn.execute("UPDATE exercices SET statut = 'cloture' WHERE id = ?", (e.id,))
        with self.assertRaises(ExerciceError):
            svc.set_tarifs(self.conn, self.session, e.id, 2000, 1500)

    def test_exercice_par_defaut(self):
        self.assertIsNone(svc.default_exercice(self.conn))
        svc.create_exercice(self.conn, self.session, 2025, 1500, 1200)
        e26 = svc.create_exercice(self.conn, self.session, 2026, 1500, 1200)
        self.assertEqual(svc.default_exercice(self.conn, date(2026, 11, 5)).id, e26.id)
        self.assertEqual(svc.default_exercice(self.conn, date(2026, 3, 1)).libelle, "2025-2026")
        self.assertEqual(svc.default_exercice(self.conn, date(2030, 1, 1)).libelle, "2026-2027")


if __name__ == "__main__":
    unittest.main()