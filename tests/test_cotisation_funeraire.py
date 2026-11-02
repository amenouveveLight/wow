import unittest
from datetime import date

from app.models.deces import PARENT, Deces
from app.models.membre import Membre
from app.models.sexe import Sexe
from app.services.cotisation_funeraire import (
    DEFUNT, EXEMPTE, NON_CONCERNE, build_statement,
)
from app.services.cotisation_mensuelle import IMPAYE, NON_APPLICABLE, PARTIEL, PAYE


def membre(id=1, sexe=Sexe.HOMME, adhesion=date(2017, 9, 5), deces=None):
    return Membre(id, f"{id:03d}", "Test", sexe, adhesion, "decede" if deces else "actif", deces)


def deces(id, d, mh=10000, mf=10000, defunt=None, endeuille=None, exempt=False):
    return Deces(id, 1, f"Défunt {id}", PARENT, defunt, d, mh, mf, endeuille, exempt)


class FuneraireTest(unittest.TestCase):
    def test_imputation_au_deces_le_plus_ancien(self):
        liste = [deces(3, date(2026, 6, 1)), deces(1, date(2025, 10, 1)), deces(2, date(2026, 2, 1))]
        s = build_statement(membre(), liste, 25000)           # liste volontairement désordonnée
        self.assertEqual([c.death.id for c in s.cells], [1, 2, 3])
        self.assertEqual([c.status for c in s.cells], [PAYE, PAYE, PARTIEL])
        self.assertEqual((s.cells[2].paid, s.cells[2].debt), (5000, 5000))
        self.assertEqual((s.total_due, s.debt, s.advance), (30000, 5000, 0))

    def test_raisons_des_cases_grisees(self):
        m = membre(id=1, adhesion=date(2026, 1, 10))
        liste = [
            deces(1, date(2025, 12, 10)),                       # avant l'adhésion
            deces(2, date(2026, 3, 14), defunt=1),              # le défunt lui-même
            deces(3, date(2026, 5, 2), endeuille=1, exempt=True),   # exempté
            deces(4, date(2026, 6, 20)),                        # concerné
        ]
        s = build_statement(m, liste, 0)
        self.assertEqual([c.reason for c in s.cells], [NON_CONCERNE, DEFUNT, EXEMPTE, None])
        self.assertEqual([c.status for c in s.cells], [NON_APPLICABLE] * 3 + [IMPAYE])
        self.assertEqual((s.total_due, s.debt), (10000, 10000))

    def test_montant_selon_le_sexe(self):
        liste = [deces(1, date(2026, 3, 1), mh=10000, mf=8000)]
        self.assertEqual(build_statement(membre(sexe=Sexe.HOMME), liste, 0).total_due, 10000)
        self.assertEqual(build_statement(membre(sexe=Sexe.FEMME), liste, 0).total_due, 8000)

    def test_versement_sans_deces_concerne_devient_avance(self):
        s = build_statement(membre(), [], 5000)
        self.assertEqual((s.total_due, s.debt, s.advance), (0, 0, 5000))
        with self.assertRaises(ValueError):
            build_statement(membre(), [], -1)


if __name__ == "__main__":
    unittest.main()