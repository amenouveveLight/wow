import unittest
from datetime import date

from app.database.connection import get_connection
from app.database.schema import migrate
from app.models.sexe import Sexe
from app.repositories import exercices, utilisateurs
from app.security.session import CurrentUser, Role, Session
from app.services import exercice_service, membre_service, versement_service
from app.services import tableau_mensuel as tm
from app.services.tableau_mensuel import TableauError

TODAY = date(2026, 8, 31)


class TableauMensuelTest(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")
        self.addCleanup(self.conn.close)
        migrate(self.conn)
        utilisateurs.create(self.conn, "ama", "Ama K.", "x", Role.ADMINISTRATEUR)
        utilisateurs.create(self.conn, "yawa", "Yawa D.", "x", Role.SECRETAIRE)
        self.admin, self.sec = Session(), Session()
        self.admin.login(CurrentUser(1, "ama", "Ama K.", Role.ADMINISTRATEUR))
        self.sec.login(CurrentUser(2, "yawa", "Yawa D.", Role.SECRETAIRE))
        self.ex = exercice_service.create_exercice(self.conn, self.admin, 2025, 18000, 14000)

        def mk(nom, sexe, adhesion=date(2017, 9, 5)):
            return membre_service.create_membre(self.conn, self.admin, nom, sexe, adhesion, today=TODAY)

        def pay(membre, montant):
            versement_service.enregistrer(self.conn, self.sec, membre.id, self.ex.id,
                                          versement_service.MENSUELLE, montant, date(2026, 2, 1), today=TODAY)

        self.yawo = mk("Yawo Agbodjan", Sexe.HOMME)
        self.efua = mk("Efua Dosseh", Sexe.FEMME)
        self.abla = mk("Abla Tsogbé", Sexe.FEMME)
        self.kossi = mk("Kossi Ayité", Sexe.HOMME)
        self.nouveau = mk("Mina Gbedemah", Sexe.FEMME, date(2026, 1, 10))
        self.ancien_decede = mk("Ancien Décédé", Sexe.HOMME)
        for membre, montant in ((self.yawo, 131000), (self.efua, 150000),
                                (self.abla, 180000), (self.kossi, 126000)):
            pay(membre, montant)
        membre_service.declare_deceased(self.conn, self.admin, self.kossi.id, date(2026, 3, 14), today=TODAY)
        membre_service.declare_deceased(self.conn, self.admin, self.ancien_decede.id, date(2025, 6, 15), today=TODAY)

    def _noms(self, page):
        return [l.membre.nom for l in page.lignes]

    def test_totaux_generaux(self):
        p = tm.tableau(self.conn, self.ex.id)
        g = p.general
        self.assertEqual((p.total, g.membres), (5, 5))
        self.assertEqual((g.du, g.percu, g.dette, g.avance), (790000, 587000, 215000, 12000))
        self.assertEqual(g.du - g.percu, g.dette - g.avance)

    def test_membres_non_concernes_exclus(self):
        noms = self._noms(tm.tableau(self.conn, self.ex.id))
        self.assertNotIn("Ancien Décédé", noms)           # décédé avant l'exercice
        self.assertIn("Kossi Ayité", noms)                # décédé pendant l'exercice

    def test_cases_du_nouveau_membre_et_du_decede(self):
        p = tm.tableau(self.conn, self.ex.id)
        par_nom = {l.membre.nom: l.releve for l in p.lignes}
        self.assertEqual([c.status for c in par_nom["Mina Gbedemah"].cells],
                         ["na"] * 4 + ["impaye"] * 8)
        self.assertEqual([c.status for c in par_nom["Kossi Ayité"].cells], ["paye"] * 7 + ["na"] * 5)

    def test_filtre_par_situation(self):
        dette = tm.tableau(self.conn, self.ex.id, situation="dette")
        self.assertEqual(set(self._noms(dette)), {"Yawo Agbodjan", "Efua Dosseh", "Mina Gbedemah"})
        self.assertEqual(self._noms(tm.tableau(self.conn, self.ex.id, situation="avance")), ["Abla Tsogbé"])
        self.assertEqual(self._noms(tm.tableau(self.conn, self.ex.id, situation="a_jour")), ["Kossi Ayité"])
        self.assertEqual(dette.general.dette, 215000)

    def test_tri_par_dette_decroissante(self):
        p = tm.tableau(self.conn, self.ex.id, sort="dette", descending=True)
        self.assertEqual(self._noms(p)[:3], ["Mina Gbedemah", "Yawo Agbodjan", "Efua Dosseh"])

    def test_recherche_et_pagination_gardent_les_totaux_generaux(self):
        p = tm.tableau(self.conn, self.ex.id, limit=2, offset=0)
        self.assertEqual((len(p.lignes), p.total), (2, 5))
        self.assertEqual(p.general.du, 790000)
        self.assertLess(p.page.du, p.general.du)
        self.assertEqual(self._noms(tm.tableau(self.conn, self.ex.id, search="dosseh")), ["Efua Dosseh"])
        dernier = tm.tableau(self.conn, self.ex.id, limit=2, offset=4)
        self.assertEqual(len(dernier.lignes), 1)

    def test_tarif_manquant_et_situation_inconnue(self):
        sans_tarif = exercices.create(self.conn, "2024-2025", date(2024, 9, 1), date(2025, 8, 31))
        with self.assertRaises(TableauError):
            tm.tableau(self.conn, sans_tarif)
        with self.assertRaises(TableauError):
            tm.tableau(self.conn, self.ex.id, situation="inconnue")
        with self.assertRaises(TableauError):
            tm.tableau(self.conn, 999)


if __name__ == "__main__":
    unittest.main()