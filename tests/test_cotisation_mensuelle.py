import unittest
from datetime import date

from app.services import calendrier
from app.services.cotisation_mensuelle import (
    IMPAYE, NON_APPLICABLE, PARTIEL, PAYE, build_statement, monthly_statement,
)

M2025 = calendrier.exercise_months(2025)     # sept. 2025 → août 2026
M2026 = calendrier.exercise_months(2026)     # sept. 2026 → août 2027
ANCIEN = date(2017, 9, 5)


def statuts(statement):
    return [c.status for c in statement.cells]


class StatementTest(unittest.TestCase):
    def test_yawo_dette_de_85000(self):
        s = monthly_statement(ANCIEN, None, M2025, tarif=18000, total_paid=131000)
        self.assertEqual(statuts(s), [PAYE] * 7 + [PARTIEL] + [IMPAYE] * 4)
        self.assertEqual((s.cells[7].paid, s.cells[7].debt), (5000, 13000))
        self.assertEqual((s.total_due, s.debt, s.advance), (216000, 85000, 0))

    def test_efua_dette_de_18000(self):
        s = monthly_statement(ANCIEN, None, M2025, tarif=14000, total_paid=150000)
        self.assertEqual(statuts(s), [PAYE] * 10 + [PARTIEL, IMPAYE])
        self.assertEqual(s.cells[10].paid, 10000)
        self.assertEqual((s.total_due, s.debt, s.advance), (168000, 18000, 0))

    def test_abla_avance_de_12000(self):
        s = monthly_statement(ANCIEN, None, M2025, tarif=14000, total_paid=180000)
        self.assertEqual(statuts(s), [PAYE] * 12)
        self.assertEqual((s.debt, s.advance), (0, 12000))

    def test_kossi_decede_en_mars_7_mois(self):
        s = monthly_statement(ANCIEN, date(2026, 3, 14), M2025, tarif=18000, total_paid=126000)
        self.assertEqual(statuts(s), [PAYE] * 7 + [NON_APPLICABLE] * 5)
        self.assertEqual((s.total_due, s.debt, s.advance), (126000, 0, 0))

    def test_nouveau_membre_de_janvier(self):
        s = monthly_statement(date(2027, 1, 10), None, M2026, tarif=18000, total_paid=0)
        self.assertEqual(statuts(s), [NON_APPLICABLE] * 4 + [IMPAYE] * 8)
        self.assertEqual((s.total_due, s.debt, s.advance), (144000, 144000, 0))

    def test_aucun_versement(self):
        s = monthly_statement(ANCIEN, None, M2025, tarif=18000, total_paid=0)
        self.assertEqual(statuts(s), [IMPAYE] * 12)
        self.assertEqual(s.debt, 216000)

    def test_douze_cases_toujours_dans_l_ordre(self):
        s = monthly_statement(date(2027, 1, 10), None, M2026, tarif=18000, total_paid=0)
        self.assertEqual(len(s.cells), 12)
        self.assertEqual([c.month for c in s.cells], M2026)

    def test_tarif_nul_et_valeurs_negatives(self):
        s = monthly_statement(ANCIEN, None, M2025, tarif=0, total_paid=0)
        self.assertEqual(statuts(s), [PAYE] * 12)
        self.assertEqual(s.total_due, 0)
        with self.assertRaises(ValueError):
            build_statement(-1, M2025, M2025, 0)
        with self.assertRaises(ValueError):
            build_statement(18000, M2025, M2025, -5)

    def test_le_cumule_des_cases_ne_depasse_jamais_le_du(self):
        for total in range(0, 260000, 7000):
            s = monthly_statement(ANCIEN, None, M2025, tarif=18000, total_paid=total)
            self.assertEqual(sum(c.paid for c in s.cells), min(total, s.total_due))
            self.assertEqual(s.debt - s.advance, s.total_due - total)


if __name__ == "__main__":
    unittest.main()