import unittest
from datetime import date

from app.services import calendrier
from app.services.regles import applicable_months, concerned_by_death, concerned_by_parallel

M2025 = calendrier.exercise_months(2025)     # sept. 2025 → août 2026
M2026 = calendrier.exercise_months(2026)     # sept. 2026 → août 2027


class MensuelleTest(unittest.TestCase):
    def test_membre_ancien_cotise_les_12_mois(self):
        self.assertEqual(len(applicable_months(date(2017, 9, 5), None, M2025)), 12)

    def test_nouveau_membre_cotise_a_partir_de_son_mois(self):
        mois = applicable_months(date(2027, 1, 10), None, M2026)
        self.assertEqual(mois[0], (2027, 1))
        self.assertEqual(len(mois), 8)                      # janv. → août
        self.assertNotIn((2026, 12), mois)

    def test_adhesion_le_dernier_jour_du_mois_compte_ce_mois(self):
        self.assertEqual(applicable_months(date(2026, 9, 30), None, M2026)[0], (2026, 9))

    def test_membre_decede_cotise_jusqu_au_mois_du_deces_inclus(self):
        mois = applicable_months(date(2017, 9, 5), date(2026, 3, 14), M2025)
        self.assertEqual((mois[0], mois[-1], len(mois)), ((2025, 9), (2026, 3), 7))

    def test_adhesion_apres_l_exercice(self):
        self.assertEqual(applicable_months(date(2027, 9, 1), None, M2026), [])


class FuneraireTest(unittest.TestCase):
    def test_membre_ancien_concerne(self):
        self.assertTrue(concerned_by_death(date(2017, 9, 5), None, date(2026, 5, 2)))

    def test_adhesion_dans_le_mois_du_deces_concerne(self):
        self.assertTrue(concerned_by_death(date(2026, 10, 15), None, date(2026, 10, 3)))

    def test_adhesion_apres_le_mois_du_deces_non_concerne(self):
        self.assertFalse(concerned_by_death(date(2026, 10, 15), None, date(2026, 9, 20)))

    def test_defunt_et_exempte_non_concernes(self):
        self.assertFalse(concerned_by_death(date(2017, 9, 5), None, date(2026, 5, 2), is_defunct=True))
        self.assertFalse(concerned_by_death(date(2017, 9, 5), None, date(2026, 5, 2), exempt=True))

    def test_membre_deja_decede_non_concerne_par_les_deces_suivants(self):
        kossi_deces = date(2026, 3, 14)
        self.assertTrue(concerned_by_death(date(2017, 9, 5), kossi_deces, date(2025, 12, 10)))
        self.assertFalse(concerned_by_death(date(2017, 9, 5), kossi_deces, date(2026, 5, 2)))


class ParalleleTest(unittest.TestCase):
    DEBUT, FIN = date(2026, 1, 1), date(2026, 6, 30)

    def test_membre_ancien_concerne(self):
        self.assertTrue(concerned_by_parallel(date(2017, 9, 5), None, self.DEBUT, self.FIN))

    def test_adhesion_en_cours_de_periode_concerne_montant_entier(self):
        self.assertTrue(concerned_by_parallel(date(2026, 3, 10), None, self.DEBUT, self.FIN))

    def test_adhesion_apres_la_periode_non_concerne(self):
        self.assertFalse(concerned_by_parallel(date(2026, 7, 1), None, self.DEBUT, self.FIN))

    def test_decede_avant_la_periode_non_concerne(self):
        self.assertFalse(concerned_by_parallel(date(2017, 9, 5), date(2025, 12, 31), self.DEBUT, self.FIN))


if __name__ == "__main__":
    unittest.main()