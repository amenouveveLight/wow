import unittest
from datetime import date

from app.database.connection import get_connection
from app.database.schema import migrate
from app.models.deces import AUTRE, BEAU_PARENT, MEMBRE, PARENT
from app.models.sexe import Sexe
from app.repositories import utilisateurs
from app.security import audit
from app.security.audit import Action
from app.security.session import CurrentUser, PermissionDenied, Role, Session
from app.services import deces_service as svc
from app.services import exercice_service, membre_service, versement_service
from app.services import tableau_funeraire as tf
from app.services.cotisation_mensuelle import IMPAYE, NON_APPLICABLE, PARTIEL, PAYE
from app.services.deces_service import DecesError
from app.services.exercice_service import ExerciceError

TODAY = date(2026, 8, 31)


class DecesServiceTest(unittest.TestCase):
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
        exercice_service.set_funeral_tarifs(self.conn, self.admin, self.ex.id, 10000, 8000)

        def mk(nom, sexe, adhesion=date(2017, 9, 5)):
            return membre_service.create_membre(self.conn, self.admin, nom, sexe, adhesion, today=TODAY)

        self.yawo = mk("Yawo Agbodjan", Sexe.HOMME)
        self.efua = mk("Efua Dosseh", Sexe.FEMME)
        self.abla = mk("Abla Tsogbé", Sexe.FEMME)
        self.kossi = mk("Kossi Ayité", Sexe.HOMME)
        self.mina = mk("Mina Gbedemah", Sexe.FEMME, date(2026, 1, 10))

    def _collecte(self, *args, **kwargs):
        return svc.creer_collecte(self.conn, self.sec, *args, today=TODAY, **kwargs)

    def _pay(self, membre, montant):
        versement_service.enregistrer(self.conn, self.sec, membre.id, self.ex.id,
                                      versement_service.FUNERAIRE, montant, date(2026, 2, 1), today=TODAY)

    def _maquette(self):
        self._collecte("Mme Lawson", PARENT, date(2025, 12, 10))
        self._collecte("", MEMBRE, date(2026, 3, 14), membre_defunt_id=self.kossi.id)
        self._collecte("M. Dosseh", BEAU_PARENT, date(2026, 5, 2),
                       membre_endeuille_id=self.efua.id, exempter_endeuille=True)
        self._collecte("Mme Tsogbé", PARENT, date(2026, 6, 20),
                       membre_endeuille_id=self.abla.id, exempter_endeuille=True)
        for membre, montant in ((self.yawo, 10000), (self.efua, 20000),
                                (self.abla, 24000), (self.kossi, 10000)):
            self._pay(membre, montant)

    def test_creation_journalisee_montants_pris_du_tarif(self):
        c = self._collecte("  Mme   Lawson ", PARENT, date(2025, 12, 10))
        self.assertEqual((c.nom_defunt, c.type_deces, c.exercice_id), ("Mme Lawson", PARENT, self.ex.id))
        self.assertEqual((c.montant_homme, c.montant_femme), (10000, 8000))
        e = audit.list_entries(self.conn)[0]
        self.assertEqual((e["action"], e["identifiant"]), (Action.DECES_AJOUT, "yawa"))

    def test_deces_de_membre_passe_le_membre_au_statut_decede(self):
        c = self._collecte("", MEMBRE, date(2026, 3, 14), membre_defunt_id=self.kossi.id)
        self.assertEqual(c.nom_defunt, "Kossi Ayité")
        k = membre_service.get_membre(self.conn, self.kossi.id)
        self.assertEqual((k.statut, k.date_deces), ("decede", date(2026, 3, 14)))
        actions = [e["action"] for e in audit.list_entries(self.conn, limit=3)]
        self.assertIn(Action.MEMBRE_DECES, actions)
        self.assertIn(Action.DECES_AJOUT, actions)

    def test_membre_deja_decede_meme_date_acceptee_autre_date_refusee(self):
        membre_service.declare_deceased(self.conn, self.sec, self.kossi.id, date(2026, 3, 14), today=TODAY)
        membre_service.declare_deceased(self.conn, self.sec, self.yawo.id, date(2026, 3, 14), today=TODAY)
        with self.assertRaises(DecesError):
            self._collecte("", MEMBRE, date(2026, 3, 15), membre_defunt_id=self.yawo.id)
        c = self._collecte("", MEMBRE, date(2026, 3, 14), membre_defunt_id=self.kossi.id)
        self.assertEqual(c.membre_defunt_id, self.kossi.id)

    def test_une_seule_collecte_par_membre_decede(self):
        self._collecte("", MEMBRE, date(2026, 3, 14), membre_defunt_id=self.kossi.id)
        with self.assertRaises(DecesError):
            self._collecte("", MEMBRE, date(2026, 3, 14), membre_defunt_id=self.kossi.id)

    def test_champs_invalides_rien_n_est_ecrit(self):
        d = date(2026, 3, 1)
        cas = [
            dict(nom="", type=PARENT, date=d),
            dict(nom="X Y", type="voisin", date=d),
            dict(nom="X Y", type=PARENT, date=date(2026, 9, 1)),         # futur
            dict(nom="X Y", type=PARENT, date=date(2020, 1, 1)),         # aucun exercice
            dict(nom="X Y", type=PARENT, date=d, exempt=True),           # exemption sans endeuillé
            dict(nom="", type=MEMBRE, date=d),                           # membre non choisi
            dict(nom="X Y", type=PARENT, date=d, endeuille=999),         # endeuillé introuvable
            dict(nom="", type=MEMBRE, date=d, defunt=self.kossi.id, endeuille=self.abla.id),
            dict(nom="X Y", type=AUTRE, date=d, defunt=self.kossi.id),
        ]
        for c in cas:
            with self.assertRaises(DecesError, msg=str(c)):
                self._collecte(c["nom"], c["type"], c["date"],
                               membre_defunt_id=c.get("defunt"), membre_endeuille_id=c.get("endeuille"),
                               exempter_endeuille=c.get("exempt", False))
        self.assertEqual(svc.list_collectes(self.conn, self.ex.id), [])
        self.assertTrue(membre_service.get_membre(self.conn, self.kossi.id).is_active)

    def test_exercice_cloture(self):
        self.conn.execute("UPDATE exercices SET statut = 'cloture' WHERE id = ?", (self.ex.id,))
        with self.assertRaises(DecesError):
            self._collecte("Mme Lawson", PARENT, date(2025, 12, 10))

    def test_tarif_funeraire_non_defini(self):
        exercice_service.create_exercice(self.conn, self.admin, 2024, 18000, 14000)   # sans tarif funéraire
        with self.assertRaises(DecesError):
            self._collecte("Mme Lawson", PARENT, date(2025, 1, 10))
        self.assertEqual(svc.list_collectes(self.conn, self.ex.id), [])

    def test_tarifs_funeraires_droits_et_validation(self):
        with self.assertRaises(PermissionDenied):
            exercice_service.set_funeral_tarifs(self.conn, self.sec, self.ex.id, 12000, 9000)
        for h, f in ((-1, 8000), (10000, 12.5), (True, 8000)):
            with self.assertRaises(ExerciceError, msg=str((h, f))):
                exercice_service.set_funeral_tarifs(self.conn, self.admin, self.ex.id, h, f)
        exercice_service.set_funeral_tarifs(self.conn, self.admin, self.ex.id, 12000, 9000)
        t = exercice_service.get_funeral_tarifs(self.conn, self.ex.id)
        self.assertEqual((t[Sexe.HOMME], t[Sexe.FEMME]), (12000, 9000))
        self.conn.execute("UPDATE exercices SET statut = 'cloture' WHERE id = ?", (self.ex.id,))
        with self.assertRaises(ExerciceError):
            exercice_service.set_funeral_tarifs(self.conn, self.admin, self.ex.id, 15000, 11000)

    def test_le_type_n_influence_pas_le_montant_et_le_tarif_est_fige(self):
        premiere = self._collecte("Mme Lawson", PARENT, date(2025, 12, 10))
        exercice_service.set_funeral_tarifs(self.conn, self.admin, self.ex.id, 12000, 9000)
        self.assertEqual((premiere.montant_homme, premiere.montant_femme), (10000, 8000))   # inchangée
        beau = self._collecte("M. Dosseh", BEAU_PARENT, date(2026, 5, 2))
        autre = self._collecte("Cousin Ayité", AUTRE, date(2026, 6, 1))
        self.assertEqual((beau.montant_homme, beau.montant_femme), (12000, 9000))
        self.assertEqual((autre.montant_homme, autre.montant_femme), (12000, 9000))

    def test_tableau_de_la_maquette(self):
        self._maquette()
        p = tf.tableau(self.conn, self.ex.id)
        self.assertEqual([c.nom_defunt for c in p.collectes],
                         ["Mme Lawson", "Kossi Ayité", "M. Dosseh", "Mme Tsogbé"])
        g = p.general
        self.assertEqual((p.total, g.du, g.percu, g.dette, g.avance), (5, 122000, 64000, 58000, 0))
        self.assertEqual(g.du - g.percu, g.dette - g.avance)

        par = {l.membre.nom: l.releve for l in p.lignes}
        statuts = lambda nom: [c.status for c in par[nom].cells]
        self.assertEqual(statuts("Yawo Agbodjan"), [PAYE, IMPAYE, IMPAYE, IMPAYE])
        self.assertEqual(statuts("Efua Dosseh"), [PAYE, PAYE, NON_APPLICABLE, PARTIEL])
        self.assertEqual(statuts("Abla Tsogbé"), [PAYE, PAYE, PAYE, NON_APPLICABLE])
        self.assertEqual(statuts("Kossi Ayité"), [PAYE] + [NON_APPLICABLE] * 3)
        self.assertEqual(statuts("Mina Gbedemah"), [NON_APPLICABLE, IMPAYE, IMPAYE, IMPAYE])

        raisons = lambda nom: [c.reason for c in par[nom].cells]
        self.assertEqual(raisons("Efua Dosseh")[2], "exempte")
        self.assertEqual(raisons("Kossi Ayité")[1:], ["defunt", "non_concerne", "non_concerne"])
        self.assertEqual(raisons("Mina Gbedemah")[0], "non_concerne")

        dette = tf.tableau(self.conn, self.ex.id, situation="dette")
        self.assertEqual({l.membre.nom for l in dette.lignes},
                         {"Yawo Agbodjan", "Efua Dosseh", "Mina Gbedemah"})

    def test_imputation_partielle_au_deces_le_plus_ancien(self):
        self._maquette()
        self._pay(self.yawo, 15000)                          # 10 000 + 15 000 = 25 000
        s = svc.releve_funeraire(self.conn, self.yawo.id, self.ex.id)
        self.assertEqual([c.status for c in s.cells], [PAYE, PAYE, PARTIEL, IMPAYE])
        self.assertEqual((s.cells[2].paid, s.cells[2].debt), (5000, 5000))
        self.assertEqual((s.total_due, s.total_paid, s.debt), (40000, 25000, 15000))


if __name__ == "__main__":
    unittest.main()