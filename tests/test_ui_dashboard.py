import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")      # tests sans écran

from PySide6.QtWidgets import QApplication

from app.services.affichage import DETTE, EXCEDENT, SOLDE, Situation
from app.ui.main_window import MainWindow
from app.ui.mock.auth import MockAuth
from app.ui.mock.dashboard import MockDashboard
from app.ui.navigation import Page
from app.ui.presenters.dashboard_model import build_view_model
from app.ui.theme import apply_theme
from app.ui.views.dashboard import DashboardView

NB = "\u00a0"


class ViewModelTest(unittest.TestCase):
    def test_exercice_de_reference_en_dette(self):
        m = build_view_model(MockDashboard().load("2025–2026"))
        self.assertEqual(m.subtitle, "Exercice 2025–2026 · du 01/09/2025 au 31/08/2026")
        self.assertFalse(m.read_only)
        stats = {s.label: s for s in m.stats}
        self.assertEqual((stats["Membres actifs"].amount, stats["Membres actifs"].note), ("412", "3 décédés cette année"))
        self.assertEqual((stats["Total perçu"].amount, stats["Total perçu"].tone), (f"802{NB}000 FCFA", "neutre"))
        self.assertEqual((stats["Dettes à recouvrer"].amount, stats["Dettes à recouvrer"].tone,
                          stats["Dettes à recouvrer"].note), (f"305{NB}000 FCFA", "rouge", "Non encaissé · 6 membres"))
        self.assertEqual((stats["Solde financier"].amount, stats["Solde financier"].tone),
                         (f"Dette : 378{NB}000 FCFA", "rouge"))
        lignes = {r.label: r for r in m.rubriques}
        self.assertEqual(lignes["Cotisations mensuelles"].situation, Situation(DETTE, 203000))
        self.assertEqual(lignes["Cotisations funéraires"].situation, Situation(DETTE, 58000))
        self.assertEqual(lignes["Cotisations parallèles"].situation, Situation(DETTE, 26000))
        self.assertEqual(lignes["Amendes"].situation, Situation(DETTE, 6000))
        self.assertEqual((lignes["Reliquats"].du, lignes["Reliquats"].percu, lignes["Reliquats"].situation),
                         ("—", f"120{NB}000 FCFA", None))
        self.assertEqual((m.total.du, m.total.percu, m.total.situation),
                         (f"975{NB}000 FCFA", f"682{NB}000 FCFA", Situation(DETTE, 293000)))
        montants = [s.amount for s in m.stats if s.label != "Solde financier"]
        for r in (*m.rubriques, m.total):
            montants += [r.du, r.percu]
        for texte in montants:
            self.assertNotIn("-", texte)                      # jamais de chiffre négatif
        self.assertEqual([a.kind for a in m.alerts], ["warning", "danger", "info"])
        self.assertEqual(len(m.payments), 5)
        self.assertEqual((m.payments[0].amount, m.payments[0].detail, m.payments[0].arrears),
                         (f"18{NB}000 FCFA", "Cotisation mensuelle · 28/08/2026", False))
        self.assertTrue(m.payments[2].arrears)

    def test_exercice_cloture_en_excedent(self):
        m = build_view_model(MockDashboard().load("2024–2025"))
        self.assertEqual(m.subtitle, "Exercice 2024–2025 · du 01/09/2024 au 31/08/2025")
        self.assertTrue(m.read_only)
        stats = {s.label: s for s in m.stats}
        self.assertEqual((stats["Solde financier"].amount, stats["Solde financier"].tone),
                         (f"Excédent : 490{NB}000 FCFA", "vert"))
        self.assertEqual((stats["Dettes à recouvrer"].amount, stats["Dettes à recouvrer"].tone,
                          stats["Dettes à recouvrer"].note), ("0 FCFA", "neutre", "Aucune dette en cours"))
        lignes = {r.label: r for r in m.rubriques}
        self.assertEqual(lignes["Cotisations mensuelles"].situation, Situation(SOLDE, 0))
        self.assertEqual(lignes["Cotisations funéraires"].situation, Situation(EXCEDENT, 20000))
        self.assertEqual(m.total.situation, Situation(EXCEDENT, 20000))
        self.assertEqual([a.kind for a in m.alerts], ["info"])


class AppTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        apply_theme(cls.app)


class DashboardViewTest(AppTestCase):
    def test_affichage_du_modele_et_signaux(self):
        vue = DashboardView()
        vue.show()
        self.addCleanup(vue.close)
        vue.set_model(build_view_model(MockDashboard().load("2025–2026")))
        self.assertEqual([c.amount_label.text() for c in vue.stat_cards],
                         ["412", f"802{NB}000 FCFA", f"305{NB}000 FCFA", f"Dette : 378{NB}000 FCFA"])
        self.assertEqual([c.tone for c in vue.stat_cards], ["neutre", "neutre", "rouge", "rouge"])
        self.assertEqual((vue.alert_count(), vue.payment_row_count(), vue.rubrique_row_count()), (3, 5, 6))
        self.assertTrue(vue.payment_button.isEnabled())
        recus = []
        vue.export_requested.connect(lambda: recus.append("export"))
        vue.payment_requested.connect(lambda: recus.append("paiement"))
        vue.history_requested.connect(lambda: recus.append("historique"))
        vue.export_button.click()
        vue.payment_button.click()
        vue.history_button.click()
        self.assertEqual(recus, ["export", "paiement", "historique"])

    def test_exercice_cloture_en_lecture_seule_et_rafraichissement(self):
        vue = DashboardView()
        vue.show()
        self.addCleanup(vue.close)
        vue.set_model(build_view_model(MockDashboard().load("2024–2025")))
        self.assertFalse(vue.payment_button.isEnabled())
        self.assertEqual((vue.alert_count(), vue.payment_row_count()), (1, 2))
        self.assertEqual((vue.stat_cards[3].tone, vue.stat_cards[3].amount_label.property("tone")), ("vert", "vert"))
        vue.set_model(build_view_model(MockDashboard().load("2025–2026")))      # pas d'empilement
        self.assertTrue(vue.payment_button.isEnabled())
        self.assertEqual((vue.alert_count(), vue.payment_row_count(), vue.rubrique_row_count()), (3, 5, 6))
        self.assertEqual(vue.stat_cards[3].tone, "rouge")


class DashboardIntegrationTest(AppTestCase):
    def test_apres_connexion_et_changement_d_exercice(self):
        fenetre = MainWindow(MockAuth())
        fenetre.show()
        self.addCleanup(fenetre.close)
        fenetre.login_view.submitted.emit("admin", "Admin2026")
        shell, vue = fenetre.shell, fenetre.dashboard_view
        self.assertIs(shell.page_container(Page.DASHBOARD).widget(), vue)
        self.assertEqual(vue.stat_cards[3].amount_label.text(), f"Dette : 378{NB}000 FCFA")
        self.assertIn("2025–2026", vue.header._subtitle.text())
        shell.topbar.exercise_requested.emit(shell.topbar.exercise_select)
        shell.popover.items()[1].clicked.emit()                                  # choisit 2024–2025 (clôturé)
        self.assertEqual(vue.stat_cards[3].amount_label.text(), f"Excédent : 490{NB}000 FCFA")
        self.assertFalse(vue.payment_button.isEnabled())
        self.assertIn("2024–2025", vue.header._subtitle.text())
        vue.payment_button.setEnabled(True)
        vue.payment_button.click()                                               # message « à venir »
        self.assertFalse(fenetre.toast.isHidden())


if __name__ == "__main__":
    unittest.main()