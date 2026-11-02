import unittest
from datetime import date

from app.database.connection import get_connection
from app.database.schema import migrate
from app.models.deces import BEAU_PARENT, MEMBRE, PARENT
from app.models.sexe import Sexe
from app.models.versement import FUNERAIRE, MENSUELLE, PARALLELE
from app.repositories import exercices, utilisateurs
from app.security.session import CurrentUser, PermissionDenied, Role, Session
from app.services import (
    amende_service, bilan_service, deces_service, depense_service, exercice_service,
    membre_service, parallele_service, versement_service,
)
from app.services.bilan_service import BilanError

TODAY = date(2026, 8, 31)

DEPENSES = [   # libellé, bénéficiaire, prévu, dépensé, date
    ("Achat de chaises", "Ets Kokou", 120000, 105000, date(2026, 6, 16)),
    ("Location salle assemblée", "Salle Le Baobab", 150000, 150000, date(2026, 6, 2)),
    ("Aide funérailles — Kossi Ayité", "Famille Ayité", 300000, 255000, date(2026, 5, 20)),
    ("Sonorisation fête", "Studio Éclair", 200000, 200000, date(2026, 4, 12)),
    ("Tenues de l’association", "Atelier Mawu", 450000, 390000, date(2026, 3, 3)),
    ("Frais de gestion", None, 80000, 80000, date(2026, 2, 10)),
]


class BilanServiceTest(unittest.TestCase):
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

        for libelle, bene, prevu, depense, d in DEPENSES:
            depense_service.enregistrer_depense(self.conn, self.sec, libelle, depense, bene, prevu, d, today=TODAY)

    def test_bilan_de_la_maquette(self):
        self._scenario()
        b = bilan_service.calculer(self.conn, self.ex.id)
        self.assertEqual([l.rubrique for l in b.lignes],
                         ["mensuelle", "funeraire", "parallele", "reliquats", "amendes"])
        valeurs = lambda r: (b.ligne(r).du, b.ligne(r).percu, b.ligne(r).manque,
                             b.ligne(r).dettes, b.ligne(r).avances)
        self.assertEqual(valeurs("mensuelle"), (790000, 587000, 203000, 215000, 12000))
        self.assertEqual(valeurs("funeraire"), (122000, 64000, 58000, 58000, 0))
        self.assertEqual(valeurs("parallele"), (54000, 28000, 26000, 26000, 0))
        self.assertEqual(valeurs("reliquats"), (None, 120000, None, 0, 0))
        self.assertEqual(valeurs("amendes"), (9000, 3000, 6000, 6000, 0))

        self.assertEqual(b.total_entrees, 802000)          # 587 000 + 64 000 + 28 000 + 120 000 + 3 000
        self.assertEqual((b.total_du, b.total_manque), (975000, 293000))
        self.assertEqual((b.total_dettes, b.total_avances), (305000, 12000))
        self.assertEqual((b.depenses, b.depenses_prevues), (1180000, 1300000))
        self.assertEqual(b.solde, -378000)                  # entrées − dépenses
        self.assertEqual(b.solde, b.total_entrees - b.depenses)

    def test_manque_egal_dettes_moins_avances(self):
        self._scenario()
        b = bilan_service.calculer(self.conn, self.ex.id)
        for ligne in b.lignes:
            if ligne.du is not None:
                self.assertEqual(ligne.manque, ligne.dettes - ligne.avances, ligne.rubrique)
        self.assertEqual(b.total_manque, b.total_dettes - b.total_avances)

    def test_exercice_sans_aucune_operation(self):
        b = bilan_service.calculer(self.conn, self.ex.id)
        self.assertEqual((b.total_entrees, b.depenses, b.solde), (0, 0, 0))
        mensuelle = b.ligne("mensuelle")
        self.assertEqual((mensuelle.du, mensuelle.percu, mensuelle.manque), (880000, 0, 880000))
        self.assertEqual((b.ligne("funeraire").du, b.ligne("parallele").du, b.ligne("amendes").du), (0, 0, 0))

    def test_les_depenses_font_baisser_le_solde(self):
        self._pay(self.yawo, 216000, MENSUELLE)
        avant = bilan_service.calculer(self.conn, self.ex.id)
        depense_service.enregistrer_depense(self.conn, self.sec, "Achat", 50000, None, None,
                                            date(2026, 6, 1), today=TODAY)
        apres = bilan_service.calculer(self.conn, self.ex.id)
        self.assertEqual((avant.solde, apres.solde), (216000, 166000))

    def test_droits_administrateur_seulement(self):
        with self.assertRaises(PermissionDenied):
            bilan_service.consulter(self.conn, self.sec, self.ex.id)
        self.assertEqual(bilan_service.consulter(self.conn, self.admin, self.ex.id).exercice.id, self.ex.id)

    def test_exercice_introuvable_et_montant_mensuel_manquant(self):
        with self.assertRaises(BilanError):
            bilan_service.calculer(self.conn, 999)
        sans_tarif = exercices.create(self.conn, "2024-2025", date(2024, 9, 1), date(2025, 8, 31))
        with self.assertRaises(BilanError):
            bilan_service.calculer(self.conn, sans_tarif)


if __name__ == "__main__":
    unittest.main()