import unittest
from datetime import date

from app.database.connection import get_connection
from app.database.schema import migrate
from app.models.deces import AUTRE
from app.models.sexe import Sexe
from app.models.versement import FUNERAIRE, PARALLELE
from app.repositories import reports, utilisateurs, versements
from app.security import audit
from app.security.audit import Action
from app.security.session import CurrentUser, PermissionDenied, Role, Session
from app.services import (
    amende_service, bilan_service, cloture_service, cotisation_mensuelle as cm, deces_service,
    exercice_service, historique_service, membre_service, parallele_service,
    reglement_service as rs, versement_service,
)
from app.services.reglement_service import ExcedentError, ReglementError
from app.services.versement_service import VersementError

TODAY = date(2026, 8, 31)        # saisie de l'exercice 2025-2026
CLOTURE = date(2026, 9, 1)
DATE26 = date(2026, 10, 5)       # date des paiements dans l'exercice 2026-2027
TODAY26 = date(2026, 10, 20)
ANCIEN = date(2017, 9, 5)


class ReglementServiceTest(unittest.TestCase):
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

        def mk(nom, sexe, adhesion=ANCIEN):
            return membre_service.create_membre(self.conn, self.admin, nom, sexe, adhesion, today=TODAY)

        self.yawo = mk("Yawo Agbodjan", Sexe.HOMME)
        self.efua = mk("Efua Dosseh", Sexe.FEMME)
        self.mina = mk("Mina Gbedemah", Sexe.FEMME, date(2026, 1, 10))
        for nom, d in (("Défunt Un", date(2025, 10, 10)), ("Défunt Deux", date(2025, 12, 10)),
                       ("Défunt Trois", date(2026, 3, 5))):
            deces_service.creer_collecte(self.conn, self.sec, nom, AUTRE, d, today=TODAY)
        versement_service.enregistrer(self.conn, self.sec, self.efua.id, self.ex.id, FUNERAIRE,
                                      8000, date(2026, 2, 1), today=TODAY)
        cot = parallele_service.creer_cotisation(
            self.conn, self.admin, "Projet salle", date(2026, 1, 1), date(2026, 6, 30), 12000, 10000)
        versement_service.enregistrer(self.conn, self.sec, self.efua.id, self.ex.id, PARALLELE,
                                      10000, date(2026, 4, 1), today=TODAY, cotisation_id=cot.id)
        amende_service.creer_amende(self.conn, self.sec, self.yawo.id, "Absence AG", "", 5000,
                                    date(2026, 5, 20), 0, today=TODAY)
        # Arriérés reportés (origine 2025-2026) :
        #   funéraire : Yawo 30 000, Efua 16 000, Mina 8 000 · parallèle : Yawo 12 000, Mina 10 000
        #   amendes : Yawo 5 000
        self.ex26 = cloture_service.cloturer(self.conn, self.admin, self.ex.id, "CLÔTURER", today=CLOTURE).suivant

    def _pay(self, membre, rubrique, montant, **kw):
        kw.setdefault("date_versement", DATE26)
        kw.setdefault("today", TODAY26)
        return rs.enregistrer_paiement(self.conn, self.sec, membre.id, self.ex26.id, rubrique, montant, **kw)

    def _mort(self):
        return deces_service.creer_collecte(self.conn, self.sec, "M. Test", AUTRE, date(2026, 10, 3), today=TODAY26)

    def _arrieres(self, membre, rubrique):
        return rs.arrieres(self.conn, membre.id, self.ex26.id, rubrique)

    def test_arrieres_par_exercice_d_origine(self):
        a = self._arrieres(self.yawo, "funeraire")
        self.assertEqual((a.total, [(e.id, m) for e, m in a.par_origine]), (30000, [(self.ex.id, 30000)]))
        self.assertEqual(self._arrieres(self.efua, "funeraire").total, 16000)
        self.assertEqual(self._arrieres(self.mina, "funeraire").total, 8000)
        self.assertEqual((self._arrieres(self.yawo, "parallele").total, self._arrieres(self.mina, "parallele").total,
                          self._arrieres(self.efua, "parallele").total), (12000, 10000, 0))
        self.assertEqual(self._arrieres(self.yawo, "amende").total, 5000)

    def test_paiement_global_cotisation_en_cours_d_abord_puis_arrieres(self):
        self._mort()
        recu = self._pay(self.yawo, "funeraire", 25000)
        v = recu.ventilation
        self.assertEqual((v.montant, v.courant, v.total_arrieres, v.excedent), (25000, 10000, 15000, 0))
        self.assertEqual([(e.libelle, m) for e, m in v.arrieres], [("2025-2026", 15000)])
        self.assertEqual([(l.nature, l.montant, l.exercice_origine_id) for l in recu.lignes],
                         [("courant", 10000, None), ("arriere", 15000, self.ex.id)])
        self.assertEqual({l.recu for l in recu.lignes}, {recu.numero})
        s = deces_service.releve_funeraire(self.conn, self.yawo.id, self.ex26.id)
        self.assertEqual([c.status for c in s.cells], [cm.PAYE])
        self.assertEqual((s.carried_debt, s.carried_debt_paid, s.carried_debt_left, s.total_debt),
                         (30000, 15000, 15000, 15000))
        self.assertEqual(self._arrieres(self.yawo, "funeraire").total, 15000)
        e = audit.list_entries(self.conn)[0]
        self.assertEqual((e["action"], e["identifiant"]), (Action.REGLEMENT_ARRIERES, "yawa"))
        self.assertIn(f"Reçu n° {recu.numero}", e["detail"])

    def test_arrieres_seulement(self):
        self._mort()
        recu = self._pay(self.yawo, "funeraire", 15000, mode=rs.ARRIERES)
        self.assertEqual([(l.nature, l.montant) for l in recu.lignes], [("arriere", 15000)])
        s = deces_service.releve_funeraire(self.conn, self.yawo.id, self.ex26.id)
        self.assertEqual([c.status for c in s.cells], [cm.IMPAYE])               # la cotisation en cours reste due
        self.assertEqual((s.debt, s.carried_debt_left, s.total_debt), (10000, 15000, 25000))

    def test_sans_cotisation_en_cours_tout_va_aux_arrieres(self):
        recu = self._pay(self.yawo, "funeraire", 30000)                          # aucun décès dans l'exercice
        v = recu.ventilation
        self.assertEqual((v.courant, v.total_arrieres, v.excedent, v.cible), (0, 30000, 0, None))
        self.assertEqual([(l.nature, l.montant) for l in recu.lignes], [("arriere", 30000)])
        self.assertEqual(self._arrieres(self.yawo, "funeraire").total, 0)
        s = deces_service.releve_funeraire(self.conn, self.yawo.id, self.ex26.id)
        self.assertEqual((s.cells, s.total_debt), ((), 0))

    def test_excedent_demande_une_confirmation_puis_devient_une_avance(self):
        self._mort()
        with self.assertRaises(ExcedentError) as ctx:
            self._pay(self.yawo, "funeraire", 50000)
        self.assertEqual(ctx.exception.excedent, 10000)
        self.assertEqual(versements.list_for_member(self.conn, self.yawo.id, exercice_id=self.ex26.id), [])
        recu = self._pay(self.yawo, "funeraire", 50000, confirmer_excedent=True)
        self.assertEqual([(l.nature, l.montant) for l in recu.lignes], [("courant", 20000), ("arriere", 30000)])
        s = deces_service.releve_funeraire(self.conn, self.yawo.id, self.ex26.id)
        self.assertEqual((s.advance, s.total_debt), (10000, 0))
        self.assertEqual(self._arrieres(self.yawo, "funeraire").total, 0)

    def test_parallele_global_et_arrieres_seulement(self):
        cot = parallele_service.creer_cotisation(
            self.conn, self.admin, "Fête de rentrée", date(2026, 9, 1), date(2026, 10, 31), 12000, 10000)
        with self.assertRaises(ReglementError):                                  # global : il faut choisir la cotisation
            self._pay(self.yawo, "parallele", 20000)
        recu = self._pay(self.yawo, "parallele", 20000, cotisation_id=cot.id)
        self.assertEqual((recu.ventilation.courant, recu.ventilation.total_arrieres), (12000, 8000))
        courant, arriere = recu.lignes
        self.assertEqual((courant.nature, courant.montant, courant.cotisation_parallele_id), ("courant", 12000, cot.id))
        self.assertEqual((arriere.nature, arriere.montant, arriere.exercice_origine_id, arriere.cotisation_parallele_id),
                         ("arriere", 8000, self.ex.id, None))
        s = parallele_service.releve_parallele(self.conn, self.yawo.id, cot.id)
        self.assertEqual((s.status, s.debt), (cm.PAYE, 0))
        self.assertEqual(self._arrieres(self.yawo, "parallele").total, 4000)
        self._pay(self.yawo, "parallele", 4000, mode=rs.ARRIERES)                # sans cotisation choisie
        self.assertEqual(self._arrieres(self.yawo, "parallele").total, 0)

    def test_arrieres_d_amendes(self):
        recu = self._pay(self.yawo, "amende", 3000)                              # les amendes : arriérés seulement
        self.assertEqual((recu.ventilation.courant, recu.ventilation.total_arrieres), (0, 3000))
        self.assertEqual([(l.rubrique, l.nature) for l in recu.lignes], [("amende", "arriere")])
        self.assertEqual(self._arrieres(self.yawo, "amende").total, 2000)
        with self.assertRaises(ReglementError):
            self._pay(self.yawo, "amende", 3000)                                 # dépasse le reste
        self._pay(self.yawo, "amende", 2000)
        self.assertEqual(self._arrieres(self.yawo, "amende").total, 0)

    def test_l_exercice_cloture_n_est_jamais_modifie(self):
        def photo(b):
            return (b.total_entrees, b.solde, [(l.rubrique, l.percu, l.dettes, l.avances) for l in b.lignes])

        avant = photo(bilan_service.calculer(self.conn, self.ex.id))
        self._pay(self.yawo, "funeraire", 30000)
        self.assertEqual(photo(bilan_service.calculer(self.conn, self.ex.id)), avant)
        with self.assertRaises(ReglementError):
            rs.enregistrer_paiement(self.conn, self.sec, self.yawo.id, self.ex.id, "funeraire", 1000,
                                    today=TODAY26)
        b = bilan_service.calculer(self.conn, self.ex26.id)                      # l'argent compte dans l'exercice en cours
        f = b.ligne("funeraire")
        self.assertEqual((f.dette_reportee, f.percu, f.manque, f.dettes), (54000, 30000, 24000, 24000))
        self.assertEqual(b.total_entrees, 30000)
        for ligne in b.lignes:
            if ligne.du is not None:
                self.assertEqual(ligne.manque, ligne.dettes - ligne.avances, ligne.rubrique)

    def test_validations_rien_n_est_ecrit(self):
        for montant in (0, -1, 12.5, True):
            with self.assertRaises(ReglementError, msg=repr(montant)):
                self._pay(self.yawo, "funeraire", montant)
        with self.assertRaises(ReglementError):
            self._pay(self.yawo, "mensuelle", 1000)
        with self.assertRaises(ReglementError):
            self._pay(self.yawo, "autre", 1000)
        with self.assertRaises(ReglementError):
            self._pay(self.yawo, "funeraire", 1000, mode="x")
        with self.assertRaises(ReglementError):
            self._pay(self.mina, "funeraire", 9000, mode=rs.ARRIERES)            # dépasse les 8 000 d'arriérés
        with self.assertRaises(ReglementError):
            self._pay(self.efua, "parallele", 1000, mode=rs.ARRIERES)            # aucun arriéré parallèle
        with self.assertRaises(ReglementError):
            self._pay(self.yawo, "funeraire", 1000, date_versement=date(2026, 11, 1))   # futur
        with self.assertRaises(ReglementError):
            self._pay(self.mina, "funeraire", 1000, date_versement=date(2026, 1, 1))    # avant l'adhésion
        with self.assertRaises(ReglementError):
            rs.enregistrer_paiement(self.conn, self.sec, 999, self.ex26.id, "funeraire", 1000, today=TODAY26)
        for membre in (self.yawo, self.mina, self.efua):
            self.assertEqual(versements.list_for_member(self.conn, membre.id, exercice_id=self.ex26.id), [])

    def test_un_reglement_d_arrieres_ne_se_modifie_pas_et_seul_l_administrateur_le_supprime(self):
        self._mort()
        recu = self._pay(self.yawo, "funeraire", 25000)
        arriere = next(l for l in recu.lignes if l.nature == "arriere")
        with self.assertRaises(VersementError):
            versement_service.modifier(self.conn, self.admin, arriere.id, 1000, DATE26, today=TODAY26)
        with self.assertRaises(PermissionDenied):
            versement_service.supprimer(self.conn, self.sec, arriere.id)
        versement_service.supprimer(self.conn, self.admin, arriere.id)
        self.assertEqual(self._arrieres(self.yawo, "funeraire").total, 30000)

    def test_l_historique_distingue_les_arrieres_du_courant(self):
        self._mort()
        recu = self._pay(self.yawo, "funeraire", 25000)
        p = historique_service.lister(self.conn, exercice_id=self.ex26.id)
        self.assertEqual((p.total, p.entrees), (2, 25000))
        par_nature = {l.nature: l for l in p.lignes}
        self.assertEqual(par_nature["courant"].periode, "Exercice 2026-2027")
        self.assertEqual((par_nature["arriere"].periode, par_nature["arriere"].libelle, par_nature["arriere"].montant),
                         ("Arriérés de 2025-2026", "Arriérés — cotisation funéraire", 15000))
        self.assertEqual({l.recu for l in p.lignes}, {recu.numero})
        arrieres = historique_service.lister(self.conn, exercice_id=self.ex26.id, nature="arriere")
        self.assertEqual((arrieres.total, arrieres.entrees), (1, 15000))
        with self.assertRaises(historique_service.HistoriqueError):
            historique_service.lister(self.conn, nature="autre")

    def test_la_cloture_suivante_conserve_l_annee_d_origine(self):
        self._mort()
        self._pay(self.yawo, "funeraire", 25000)                                 # reste 15 000 d'arriérés pour Yawo
        res = cloture_service.cloturer(self.conn, self.admin, self.ex26.id, "CLÔTURER", today=date(2027, 9, 1))
        lignes = reports.list_for_cible(self.conn, res.suivant.id)
        par = {}
        for l in lignes:
            if l.type == "dette":
                par[(l.rubrique, l.exercice_origine_id)] = par.get((l.rubrique, l.exercice_origine_id), 0) + l.montant
        # funéraire : arriérés d'origine 2025 (15 000 + 16 000 + 8 000) ; dettes nées en 2026 (Efua 8 000 + Mina 8 000)
        self.assertEqual(par[("funeraire", self.ex.id)], 39000)
        self.assertEqual(par[("funeraire", self.ex26.id)], 16000)
        self.assertEqual(par[("parallele", self.ex.id)], 22000)                  # non réglés : ils restent « de 2025-2026 »
        self.assertEqual(par[("amende", self.ex.id)], 5000)
        self.assertNotIn(("parallele", self.ex26.id), par)


if __name__ == "__main__":
    unittest.main()