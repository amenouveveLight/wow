import unittest
from datetime import date

from app.database.connection import get_connection
from app.database.schema import migrate
from app.models.deces import BEAU_PARENT, MEMBRE, PARENT
from app.models.sexe import Sexe
from app.models.versement import FUNERAIRE, MENSUELLE, PARALLELE
from app.repositories import exercices, reports, utilisateurs
from app.security import audit
from app.security.audit import Action
from app.security.session import CurrentUser, PermissionDenied, Role, Session
from app.services import (
    amende_service, cloture_service as svc, deces_service, depense_service, exercice_service,
    membre_service, parallele_service, versement_service,
)
from app.services.cloture_service import AVANCE, DETTE, SOLDE, ClotureError
from app.services.versement_service import VersementError

TODAY = date(2026, 8, 31)         # date de saisie du scénario (dernier jour de l'exercice)
CLOTURE = date(2026, 9, 1)        # le lendemain : l'exercice est terminé


class ClotureServiceTest(unittest.TestCase):
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

    def _pay(self, membre, montant, rubrique, d=date(2026, 2, 1), cotisation=None):
        versement_service.enregistrer(
            self.conn, self.sec, membre.id, self.ex.id, rubrique, montant, d, today=TODAY,
            cotisation_id=cotisation.id if cotisation else None)

    def _scenario(self):
        for membre, montant in ((self.yawo, 131000), (self.efua, 150000),
                                (self.abla, 180000), (self.kossi, 126000)):
            self._pay(membre, montant, MENSUELLE)
        c = lambda *a, **k: deces_service.creer_collecte(self.conn, self.sec, *a, today=TODAY, **k)
        c("Mme Lawson", PARENT, date(2025, 12, 10))
        c("", MEMBRE, date(2026, 3, 14), membre_defunt_id=self.kossi.id)
        c("M. Dosseh", BEAU_PARENT, date(2026, 5, 2), membre_endeuille_id=self.efua.id, exempter_endeuille=True)
        c("Mme Tsogbé", PARENT, date(2026, 6, 20), membre_endeuille_id=self.abla.id, exempter_endeuille=True)
        for membre, montant in ((self.yawo, 10000), (self.efua, 20000),
                                (self.abla, 24000), (self.kossi, 10000)):
            self._pay(membre, montant, FUNERAIRE)
        cot = parallele_service.creer_cotisation(
            self.conn, self.admin, "Projet salle des fêtes", date(2026, 1, 1), date(2026, 6, 30), 12000, 10000)
        for membre, montant in ((self.yawo, 12000), (self.abla, 10000), (self.efua, 6000)):
            self._pay(membre, montant, PARALLELE, date(2026, 4, 1), cot)
        a = lambda membre, nom, attendu, collecte, d: amende_service.creer_amende(
            self.conn, self.sec, membre.id, nom, "", attendu, d, collecte, today=TODAY)
        a(self.yawo, "Absence AG", 5000, 0, date(2026, 5, 20))
        a(self.efua, "Retard", 2000, 2000, date(2026, 4, 10))
        a(self.yawo, "Retard", 2000, 1000, date(2026, 6, 15))
        for libelle, bene, prevu, depense, d in (
                ("Achat de chaises", "Ets Kokou", 120000, 105000, date(2026, 6, 16)),
                ("Location salle assemblée", "Salle Le Baobab", 150000, 150000, date(2026, 6, 2)),
                ("Aide funérailles — Kossi Ayité", "Famille Ayité", 300000, 255000, date(2026, 5, 20)),
                ("Sonorisation fête", "Studio Éclair", 200000, 200000, date(2026, 4, 12)),
                ("Tenues de l’association", "Atelier Mawu", 450000, 390000, date(2026, 3, 3)),
                ("Frais de gestion", None, 80000, 80000, date(2026, 2, 10))):
            depense_service.enregistrer_depense(self.conn, self.sec, libelle, depense, bene, prevu, d, today=TODAY)

    def test_apercu_de_la_maquette(self):
        self._scenario()
        a = svc.apercu(self.conn, self.admin, self.ex.id, today=CLOTURE)
        self.assertIsNone(a.blocage)
        self.assertEqual((a.suivant_libelle, a.suivant_existe), ("2026-2027", False))
        self.assertEqual((a.total_dettes, a.total_avances, a.solde), (305000, 12000, -378000))
        self.assertEqual((a.total(DETTE, "mensuelle"), a.total(DETTE, "funeraire"),
                          a.total(DETTE, "parallele"), a.total(DETTE, "amende")),
                         (215000, 58000, 26000, 6000))
        self.assertEqual((a.membres_en_dette, a.membres_en_avance, len(a.lignes)), (4, 1, 11))
        par_membre = {}
        for l in a.lignes:
            if l.type == DETTE:
                par_membre[l.membre.nom] = par_membre.get(l.membre.nom, 0) + l.montant
        self.assertEqual(par_membre, {"Yawo Agbodjan": 121000, "Efua Dosseh": 26000,
                                      "Mina Gbedemah": 146000, "Kossi Ayité": 12000})
        avance = [l for l in a.lignes if l.type == AVANCE]
        self.assertEqual([(l.membre.nom, l.rubrique, l.montant) for l in avance],
                         [("Abla Tsogbé", "mensuelle", 12000)])

    def test_cloture_complete_avec_confirmation(self):
        self._scenario()
        with self.assertRaises(ClotureError):
            svc.cloturer(self.conn, self.admin, self.ex.id, "oui", today=CLOTURE)
        self.assertTrue(exercices.get(self.conn, self.ex.id).is_open)
        self.assertIsNone(exercices.get_by_libelle(self.conn, "2026-2027"))        # rien n'a été créé

        res = svc.cloturer(self.conn, self.admin, self.ex.id, " clôturer ", today=CLOTURE)
        self.assertEqual((res.exercice.statut, res.exercice.date_cloture), ("cloture", "2026-09-01"))
        self.assertEqual((res.suivant.libelle, res.suivant.is_open), ("2026-2027", True))
        self.assertEqual((res.solde, res.total_dettes, res.total_avances, res.lignes_reportees),
                         (-378000, 305000, 12000, 12))
        self.assertEqual(exercice_service.get_tarifs(self.conn, res.suivant.id),
                         {Sexe.HOMME: 18000, Sexe.FEMME: 14000})
        self.assertEqual(exercice_service.get_funeral_tarifs(self.conn, res.suivant.id),
                         {Sexe.HOMME: 10000, Sexe.FEMME: 8000})

        lignes = reports.list_for_cible(self.conn, res.suivant.id)
        self.assertEqual(len(lignes), 12)
        self.assertEqual(reports.totals_by_type(self.conn, res.suivant.id),
                         {"dette": 305000, "avance": 12000, "solde": -378000})
        solde = [l for l in lignes if l.type == SOLDE]
        self.assertEqual((len(solde), solde[0].membre_id, solde[0].rubrique, solde[0].montant,
                          solde[0].exercice_source_id), (1, None, None, -378000, self.ex.id))
        e = audit.list_entries(self.conn)[0]
        self.assertEqual((e["action"], e["objet"], e["identifiant"]), (Action.CLOTURE, "Exercice 2025-2026", "ama"))
        self.assertIn("2026-2027", e["detail"])

    def test_apres_la_cloture_plus_rien_ne_change(self):
        self._scenario()
        svc.cloturer(self.conn, self.admin, self.ex.id, "CLÔTURER", today=CLOTURE)
        with self.assertRaises(VersementError):
            versement_service.enregistrer(self.conn, self.sec, self.yawo.id, self.ex.id, MENSUELLE,
                                          1000, date(2026, 5, 1), today=TODAY)
        with self.assertRaises(ClotureError):
            svc.cloturer(self.conn, self.admin, self.ex.id, "CLÔTURER", today=CLOTURE)
        self.assertIn("déjà clôturé", svc.apercu(self.conn, self.admin, self.ex.id, today=CLOTURE).blocage)

    def test_pas_de_cloture_avant_la_fin_de_l_exercice(self):
        a = svc.apercu(self.conn, self.admin, self.ex.id, today=date(2026, 8, 31))
        self.assertIn("31/08/2026", a.blocage)
        with self.assertRaises(ClotureError):
            svc.cloturer(self.conn, self.admin, self.ex.id, "CLÔTURER", today=date(2026, 8, 31))
        self.assertTrue(exercices.get(self.conn, self.ex.id).is_open)
        self.assertIsNone(exercices.get_by_libelle(self.conn, "2026-2027"))

    def test_administrateur_seulement(self):
        with self.assertRaises(PermissionDenied):
            svc.apercu(self.conn, self.sec, self.ex.id, today=CLOTURE)
        with self.assertRaises(PermissionDenied):
            svc.cloturer(self.conn, self.sec, self.ex.id, "CLÔTURER", today=CLOTURE)
        with self.assertRaises(ClotureError):
            svc.cloturer(self.conn, self.admin, 999, "CLÔTURER", today=CLOTURE)

    def test_les_exercices_se_cloturent_dans_l_ordre(self):
        ex24 = exercice_service.create_exercice(self.conn, self.admin, 2024, 18000, 14000)
        a = svc.apercu(self.conn, self.admin, self.ex.id, today=CLOTURE)
        self.assertIn("2024-2025", a.blocage)
        with self.assertRaises(ClotureError):
            svc.cloturer(self.conn, self.admin, self.ex.id, "CLÔTURER", today=CLOTURE)

        res = svc.cloturer(self.conn, self.admin, ex24.id, "CLÔTURER", today=CLOTURE)
        self.assertEqual(res.suivant.id, self.ex.id)                       # reports dans l'exercice déjà créé
        self.assertTrue(exercices.get(self.conn, self.ex.id).is_open)
        self.assertGreater(len(reports.list_for_cible(self.conn, self.ex.id)), 0)
        self.assertEqual(exercice_service.get_tarifs(self.conn, self.ex.id),
                         {Sexe.HOMME: 18000, Sexe.FEMME: 14000})           # montants inchangés

        res2 = svc.cloturer(self.conn, self.admin, self.ex.id, "CLÔTURER", today=CLOTURE)
        self.assertEqual(res2.suivant.libelle, "2026-2027")

    def test_l_exercice_suivant_deja_cloture_bloque(self):
        ex26 = exercice_service.create_exercice(self.conn, self.admin, 2026, 18000, 14000)
        self.conn.execute("UPDATE exercices SET statut = 'cloture' WHERE id = ?", (ex26.id,))
        a = svc.apercu(self.conn, self.admin, self.ex.id, today=CLOTURE)
        self.assertTrue(a.suivant_existe)
        self.assertIn("2026-2027", a.blocage)
        with self.assertRaises(ClotureError):
            svc.cloturer(self.conn, self.admin, self.ex.id, "CLÔTURER", today=CLOTURE)
        self.assertTrue(exercices.get(self.conn, self.ex.id).is_open)


if __name__ == "__main__":
    unittest.main()