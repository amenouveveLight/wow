import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")      # tests sans écran

from PySide6.QtWidgets import QApplication

from app.ui import icons, paths
from app.ui.theme import apply_theme, tokens
from app.ui.theme.stylesheet import build


class ThemeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_les_couleurs_sont_des_codes_hexadecimaux(self):
        for nom, valeur in tokens.color_items():
            self.assertRegex(valeur, r"^#[0-9A-F]{6}$", nom)
        self.assertEqual(tokens.Color.NAVY_900, "#0B1F3F")

    def test_la_feuille_de_style_est_complete(self):
        qss = build()
        self.assertNotRegex(qss, r"@[a-z]")                          # aucun jeton non remplacé
        self.assertEqual(qss.count("{"), qss.count("}"))
        self.assertIn(tokens.Color.NAVY_900, qss)
        self.assertIn('QPushButton[variant="primary"]:hover', qss)

    def test_toutes_les_icones_se_chargent(self):
        fichiers = sorted(paths.ICONS_DIR.glob("*.svg"))
        self.assertGreaterEqual(len(fichiers), 25, "Lancez : python scripts\\generate_icons.py")
        for fichier in fichiers:
            image = icons.icon(fichier.stem, "#0B1F3F", 18).pixmap(18, 18)
            self.assertFalse(image.isNull(), fichier.stem)

    def test_l_apercu_du_theme_se_construit(self):
        from app.ui.views.theme_preview import ThemePreview
        apply_theme(self.app)
        fenetre = ThemePreview()
        self.assertTrue(fenetre.windowTitle())


if __name__ == "__main__":
    unittest.main()