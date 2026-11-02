import unittest
from datetime import date

from app.models.exercice import Exercice
from app.services.affichage import DETTE, EXCEDENT, SOLDE, Situation, depuis_ecart, situation
from app.services.bilan_service import Bilan, LigneBilan

EX = Exercice(1, "2025-2026", date(2025, 9, 1), date(2026, 8, 31), "ouvert", None)


def bilan(lignes, depenses=0):
    return Bilan(EX, tuple(lignes), depenses, depenses)


class SituationTest(unittest.TestCase):
    def test_excedent_dette_et_solde(self):
        self.assertEqual(situation(100, 150), Situation(EXCEDENT, 50))
        self.assertEqual(situation(100, 40), Situation(DETTE, 60))
        self.assertEqual(situation(100, 100), Situation(SOLDE, 0))
        self.assertEqual([situation(100, 150).couleur, situation(100, 40).couleur, situation(5, 5).couleur],
                         ["vert", "rouge", "neutre"])

    def test_jamais_de_chiffre_negatif(self):
        for ecart in (-378000, -1, 0, 1, 500000):
            s = depuis_ecart(ecart)
            self.assertGreaterEqual(s.montant, 0)
            self.assertNotIn("-", s.texte())
        self.assertEqual(Situation(DETTE, 378000).texte(), "Dette : 378\u00a0000 FCFA")
        self.assertEqual(Situation(EXCEDENT, 122000).texte(), "Excédent : 122\u00a0000 FCFA")
        self.assertEqual(Situation(SOLDE, 0).texte(), "Soldé : 0 FCFA")

    def test_chaque_rubrique_du_bilan(self):
        b = bilan([
            LigneBilan("mensuelle", "Cotisations mensuelles", 790000, 587000, 215000, 12000),
            LigneBilan("funeraire", "Cotisations funéraires", 122000, 64000, 58000, 0),
            LigneBilan("parallele", "Cotisations parallèles", 54000, 28000, 26000, 0),
            LigneBilan("reliquats", "Reliquats", None, 120000),
            LigneBilan("amendes", "Amendes", 9000, 3000, 6000, 0),
        ], depenses=1180000)
        self.assertEqual(b.ligne("mensuelle").situation, Situation(DETTE, 203000))   # net : 215 000 − 12 000
        self.assertEqual(b.ligne("funeraire").situation, Situation(DETTE, 58000))
        self.assertEqual(b.ligne("parallele").situation, Situation(DETTE, 26000))
        self.assertIsNone(b.ligne("reliquats").situation)
        self.assertEqual(b.ligne("amendes").situation, Situation(DETTE, 6000))

        surplus = bilan([LigneBilan("amendes", "Amendes", 100000, 130000)])
        self.assertEqual(surplus.ligne("amendes").situation, Situation(EXCEDENT, 30000))
        self.assertEqual(surplus.ligne("amendes").situation.couleur, "vert")

    def test_global_et_solde_de_l_exercice(self):
        b = bilan([
            LigneBilan("mensuelle", "Cotisations mensuelles", 790000, 587000),
            LigneBilan("funeraire", "Cotisations funéraires", 122000, 64000),
            LigneBilan("parallele", "Cotisations parallèles", 54000, 28000),
            LigneBilan("reliquats", "Reliquats", None, 120000),
            LigneBilan("amendes", "Amendes", 9000, 3000),
        ], depenses=1180000)
        self.assertEqual((b.total_du, b.percu_hors_reliquats, b.total_entrees), (975000, 682000, 802000))
        self.assertEqual(b.situation_globale, Situation(DETTE, 293000))      # reliquats exclus
        self.assertEqual(b.situation_solde, Situation(DETTE, 378000))        # entrées − dépenses
        self.assertEqual(bilan(b.lignes, depenses=500000).situation_solde, Situation(EXCEDENT, 302000))


if __name__ == "__main__":
    unittest.main()