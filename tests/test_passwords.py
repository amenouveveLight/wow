import unittest

from app.security.passwords import (
    PasswordPolicyError,
    hash_password,
    needs_rehash,
    validate_policy,
    verify_password,
)


class PasswordsTest(unittest.TestCase):
    def test_bon_mot_de_passe(self):
        h = hash_password("Secret2026")
        self.assertTrue(verify_password("Secret2026", h))

    def test_mauvais_mot_de_passe(self):
        h = hash_password("Secret2026")
        self.assertFalse(verify_password("secret2026", h))

    def test_deux_hashes_differents_pour_le_meme_mot_de_passe(self):
        self.assertNotEqual(hash_password("Secret2026"), hash_password("Secret2026"))

    def test_hash_illisible_refuse_sans_planter(self):
        self.assertFalse(verify_password("x", "n'importe quoi"))

    def test_politique(self):
        validate_policy("Secret2026")
        for mauvais in ("court1", "uniquementdeslettres", "12345678"):
            with self.assertRaises(PasswordPolicyError):
                validate_policy(mauvais)

    def test_rehash(self):
        self.assertFalse(needs_rehash(hash_password("Secret2026")))
        self.assertTrue(needs_rehash("pbkdf2_sha256$1000$aa$bb"))


if __name__ == "__main__":
    unittest.main()