import unittest
from unittest.mock import patch

from app.database.connection import get_connection
from app.database.schema import migrate
from app.repositories import utilisateurs
from app.security import audit
from app.security.audit import Action
from app.security.session import PermissionDenied, Role, Session
from app.services import auth_service as auth
from app.services import user_service as svc
from app.services.auth_service import AccountDisabled, InvalidCredentials
from app.services.user_service import UserError


class UserServiceTest(unittest.TestCase):
    def setUp(self):
        patcher = patch("app.security.passwords.ITERATIONS", 1000)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.conn = get_connection(":memory:")
        self.addCleanup(self.conn.close)
        migrate(self.conn)
        auth.create_first_admin(self.conn, "ama", "Ama Kpodar", "Secret2026")
        self.admin = Session()
        auth.login(self.conn, self.admin, "ama", "Secret2026")

    def _secretaire(self, ident="yawa", nom="Yawa Dovi", pwd="Secret2026"):
        return svc.creer_secretaire(self.conn, self.admin, ident, nom, pwd)

    def _session(self, ident, pwd="Secret2026"):
        session = Session()
        auth.login(self.conn, session, ident, pwd)
        return session

    def test_creation_normalisee_journalisee_et_connexion_possible(self):
        u = self._secretaire(" YAWA ", "  Yawa   Dovi ")
        self.assertEqual((u.identifiant, u.nom_complet, u.role, u.actif), ("yawa", "Yawa Dovi", Role.SECRETAIRE, True))
        e = audit.list_entries(self.conn)[0]
        self.assertEqual((e["action"], e["objet"], e["identifiant"]), (Action.UTILISATEUR_AJOUT, "yawa", "ama"))
        self.assertNotIn("Secret2026", e["detail"])
        self.assertEqual(self._session("Yawa").user.role, Role.SECRETAIRE)       # insensible à la casse

    def test_validations_rien_n_est_cree(self):
        cas = [("ab", "Yawa Dovi", "Secret2026"), ("YAWA D", "Yawa Dovi", "Secret2026"),
               ("yawa", " ", "Secret2026"), ("yawa", "Yawa Dovi", "court1"),
               ("yawa", "Yawa Dovi", "uniquementdeslettres"), ("ama", "Autre Ama", "Secret2026")]
        for ident, nom, pwd in cas:
            with self.assertRaises(UserError, msg=str((ident, nom, pwd))):
                svc.creer_secretaire(self.conn, self.admin, ident, nom, pwd)
        self.assertEqual(len(svc.list_users(self.conn, self.admin)), 1)           # seulement l'administrateur
        self._secretaire()
        with self.assertRaises(UserError):
            self._secretaire("YAWA", "Autre Personne")                            # doublon, casse ignorée

    def test_trois_secretaires_actifs_au_maximum(self):
        comptes = [self._secretaire(f"secretaire{i}", f"Secrétaire Numéro{i}") for i in range(3)]
        with self.assertRaises(UserError):
            self._secretaire("secretaire4", "Quatrième Secrétaire")
        svc.set_actif(self.conn, self.admin, comptes[0].id, False)
        quatrieme = self._secretaire("secretaire4", "Quatrième Secrétaire")        # une place s'est libérée
        with self.assertRaises(UserError):
            svc.set_actif(self.conn, self.admin, comptes[0].id, True)              # plus de place
        svc.set_actif(self.conn, self.admin, quatrieme.id, False)
        self.assertTrue(svc.set_actif(self.conn, self.admin, comptes[0].id, True).actif)

    def test_administrateur_seulement(self):
        u = self._secretaire()
        sec = self._session("yawa")
        with self.assertRaises(PermissionDenied):
            svc.creer_secretaire(self.conn, sec, "autre", "Autre Compte", "Secret2026")
        with self.assertRaises(PermissionDenied):
            svc.reinitialiser_mot_de_passe(self.conn, sec, u.id, "Nouveau2026")
        with self.assertRaises(PermissionDenied):
            svc.set_actif(self.conn, sec, u.id, False)
        with self.assertRaises(PermissionDenied):
            svc.list_users(self.conn, sec)

    def test_reinitialisation_par_l_administrateur_deverrouille(self):
        u = self._secretaire()
        utilisateurs.record_failure(self.conn, u.id, 0, "2099-01-01 00:00:00")      # compte verrouillé
        svc.reinitialiser_mot_de_passe(self.conn, self.admin, u.id, "Nouveau2026")
        self.assertIsNone(utilisateurs.get_by_id(self.conn, u.id).verrouille_jusqua)
        with self.assertRaises(InvalidCredentials):
            auth.login(self.conn, Session(), "yawa", "Secret2026")
        self.assertTrue(self._session("yawa", "Nouveau2026").is_authenticated)
        e = audit.list_entries(self.conn, action=Action.UTILISATEUR_MODIF)[0]
        self.assertNotIn("Nouveau2026", e["detail"])
        with self.assertRaises(UserError):
            svc.reinitialiser_mot_de_passe(self.conn, self.admin, u.id, "faible")
        with self.assertRaises(UserError):
            svc.reinitialiser_mot_de_passe(self.conn, self.admin, 999, "Nouveau2026")

    def test_changement_de_son_propre_mot_de_passe(self):
        self._secretaire()
        sec = self._session("yawa")
        with self.assertRaises(UserError):
            svc.changer_mon_mot_de_passe(self.conn, sec, "mauvais", "Nouveau2026")
        with self.assertRaises(UserError):
            svc.changer_mon_mot_de_passe(self.conn, sec, "Secret2026", "Secret2026")
        with self.assertRaises(UserError):
            svc.changer_mon_mot_de_passe(self.conn, sec, "Secret2026", "faible")
        svc.changer_mon_mot_de_passe(self.conn, sec, "Secret2026", "Nouveau2026")
        self.assertTrue(self._session("yawa", "Nouveau2026").is_authenticated)
        with self.assertRaises(InvalidCredentials):
            auth.login(self.conn, Session(), "yawa", "Secret2026")

    def test_administrateur_non_desactivable_et_compte_desactive_bloque(self):
        admin_id = self.admin.user.id
        with self.assertRaises(UserError):
            svc.set_actif(self.conn, self.admin, admin_id, False)
        u = self._secretaire()
        with self.assertRaises(UserError):
            svc.set_actif(self.conn, self.admin, u.id, True)                       # déjà actif
        svc.set_actif(self.conn, self.admin, u.id, False)
        with self.assertRaises(AccountDisabled):
            auth.login(self.conn, Session(), "yawa", "Secret2026")
        self.assertEqual(audit.list_entries(self.conn)[1]["detail"], "Compte désactivé")


if __name__ == "__main__":
    unittest.main()