"""Contrôle rapide du projet : fichiers présents et complets, syntaxe, imports, icônes, feuille de style.

Usage (depuis la racine du projet) :  python scripts\\verifier.py
À lancer avant les tests : il dit précisément quel fichier est absent, vide, écrasé par un extrait,
incomplet, mal écrit ou impossible à importer.
"""
from __future__ import annotations

import ast
import importlib
import os
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")          # imports de l'interface sans écran
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

TESTS_ATTENDUS = 224

# chemin → marqueur(s) qui doivent figurer dans le fichier (un fichier écrasé ne les contient plus)
ATTENDU: dict[str, str | tuple[str, ...]] = {
    "main.py": ("def main", "MockDashboard", "apply_theme"),
    # ---------- Base de données, sécurité, configuration ----------
    "app/config.py": ("def ensure_directories", "APP_NAME"),
    "app/database/connection.py": "SAVEPOINT",
    "app/database/schema.py": "SCHEMA_V6",
    "app/security/passwords.py": "def hash_password",
    "app/security/session.py": "PAYMENT_EDIT",
    "app/security/audit.py": ("AMENDE_COLLECTE", "REGLEMENT_ARRIERES", "CARNET_FORMAT"),
    # ---------- Modèles ----------
    "app/models/utilisateur.py": "class Utilisateur",
    "app/models/sexe.py": "class Sexe",
    "app/models/exercice.py": "class Exercice",
    "app/models/membre.py": "class Membre",
    "app/models/versement.py": ("NATURE_ARRIERE", "RUBRIQUES_SAISISSABLES"),
    "app/models/deces.py": "class Deces",
    "app/models/cotisation_parallele.py": "class CotisationParallele",
    "app/models/amende.py": "class AmendeLigne",
    "app/models/depense.py": "class ReliquatLigne",
    "app/models/report.py": "exercice_origine_id",
    "app/models/transaction.py": ("class Transaction", "periode"),
    # ---------- Repositories ----------
    "app/repositories/utilisateurs.py": "def get_by_identifiant",
    "app/repositories/parametres.py": "def set_",
    "app/repositories/exercices.py": ("def first_open_before", "def get_funeral_tarifs", "def get_for_date"),
    "app/repositories/membres.py": "concerned",
    "app/repositories/versements.py": ("def arrears_paid_by_origin", "def totals_by_member_parallele", "def next_recu"),
    "app/repositories/deces.py": "def list_for_exercice",
    "app/repositories/cotisations_paralleles.py": "def list_for_exercice",
    "app/repositories/amendes.py": "def totals",
    "app/repositories/depenses.py": "def totals",
    "app/repositories/reliquats.py": "def list_for_exercice",
    "app/repositories/reports.py": ("def by_member_and_origin", "def solde_ouverture"),
    "app/repositories/encaissements_amendes.py": "def total",
    "app/repositories/historique.py": ("def totals", "nature"),
    # ---------- Services (règles de gestion) ----------
    "app/services/calendrier.py": "def exercise_months",
    "app/services/regles.py": "def applicable_months",
    "app/services/auth_service.py": "def login",
    "app/services/exercice_service.py": ("def create_exercice", "def set_funeral_tarifs"),
    "app/services/carnet_service.py": "def allocate",
    "app/services/membre_service.py": "carnet_service.allocate",
    "app/services/cotisation_mensuelle.py": ("carried_debt", "def monthly_statement"),
    "app/services/versement_service.py": ("def enregistrer", "def releve_mensuel", "reports.member_amount", '"arriere"'),
    "app/services/tableau_mensuel.py": ("def tableau", "def concerne", "dette_reportee"),
    "app/services/cotisation_funeraire.py": ("arrears_paid", "class FuneralStatement"),
    "app/services/deces_service.py": ("def creer_collecte", "def list_collectes", "def releve_funeraire"),
    "app/services/tableau_funeraire.py": ("def tableau", "avec_report"),
    "app/services/cotisation_parallele.py": "def build_statement",
    "app/services/parallele_service.py": "def creer_cotisation",
    "app/services/tableau_parallele.py": "class TableauParalleleError",
    "app/services/amende_service.py": ("def collecter", "encaissements_amendes"),
    "app/services/depense_service.py": "def list_reliquats",
    "app/services/affichage.py": "def depuis_ecart",
    "app/services/historique_service.py": "def historique_membre",
    "app/services/bilan_service.py": ("class Bilan", "def calculer", "def consulter", "total_arrears_paid"),
    "app/services/cloture_service.py": ("def cloturer", "_restes_plus_ancien_d_abord"),
    "app/services/reglement_service.py": ("def enregistrer_paiement", "def arrieres"),
    "app/services/user_service.py": "def creer_secretaire",
    "app/services/backup_service.py": "def restaurer",
    # ---------- Interface : socle ----------
    "app/ui/paths.py": "QSS_FILES",
    "app/ui/format.py": "def format_fcfa",
    "app/ui/icons.py": "def icon",
    "app/ui/navigation.py": "def allowed_keys",
    "app/ui/ports.py": ("class AuthPort", "class DashboardPort"),
    "app/ui/main_window.py": ("class MainWindow", "DashboardPresenter"),
    # ---------- Interface : thème ----------
    "app/ui/theme/__init__.py": "def apply_theme",
    "app/ui/theme/tokens.py": ("def mapping", "DISPLAY"),
    "app/ui/theme/stylesheet.py": ("def build", "_COMMENT"),
    "app/ui/theme/fonts.py": "def configure_fonts",
    "app/ui/theme/effects.py": "def apply_shadow",
    "app/ui/theme/styles.qss": "QFrame#Sidebar",
    "app/ui/theme/screens.qss": ("LoginBrand", "grid-head"),
    # ---------- Interface : composants ----------
    "app/ui/widgets/base.py": "class ClickableFrame",
    "app/ui/widgets/button.py": "class AppButton",
    "app/ui/widgets/badge.py": "def status_badge",
    "app/ui/widgets/labels.py": "class SituationLabel",
    "app/ui/widgets/card.py": "class StatCard",
    "app/ui/widgets/field.py": ("class FormField", "def mark_invalid"),
    "app/ui/widgets/banner.py": ("class Banner", "class Toast"),
    "app/ui/widgets/sidebar.py": "class Sidebar",
    "app/ui/widgets/topbar.py": "class TopBar",
    "app/ui/widgets/statusbar.py": "class AppStatusBar",
    "app/ui/widgets/page_header.py": "class PageHeader",
    "app/ui/widgets/popover.py": "class Popover",
    # ---------- Interface : vues et présentateurs ----------
    "app/ui/views/theme_preview.py": "class ThemePreview",
    "app/ui/views/login.py": "class LoginView",
    "app/ui/views/placeholder.py": "class PlaceholderPage",
    "app/ui/views/shell.py": "class Shell",
    "app/ui/views/dashboard.py": "class DashboardView",
    "app/ui/presenters/login.py": "class LoginPresenter",
    "app/ui/presenters/dashboard_model.py": "def build_view_model",
    "app/ui/presenters/dashboard.py": "class DashboardPresenter",
    # ---------- Interface : données factices ----------
    "app/ui/mock/auth.py": "class MockAuth",
    "app/ui/mock/data.py": "NOTIFICATIONS",
    "app/ui/mock/dashboard.py": "class MockDashboard",
    # ---------- Outils ----------
    "scripts/generate_icons.py": "def main",
}

# Fichiers qui peuvent exister (vérifiés s'ils sont là, jamais réclamés)
OPTIONNELS: dict[str, str | tuple[str, ...]] = {
    "app/ui/views/widgets_preview.py": "class WidgetsPreview",
}

TESTS = [
    "test_schema", "test_passwords", "test_session", "test_audit", "test_auth_service",
    "test_connection", "test_exercice_service", "test_membre_service", "test_carnet_service",
    "test_regles", "test_cotisation_mensuelle", "test_versement_service", "test_tableau_mensuel",
    "test_cotisation_funeraire", "test_deces_service", "test_cotisation_parallele",
    "test_parallele_service", "test_amende_service", "test_depense_service",
    "test_bilan_service", "test_cloture_service", "test_user_service", "test_backup_service",
    "test_situation", "test_historique_service", "test_report_integration", "test_reglement_service",
    "test_ui_theme", "test_ui_widgets", "test_ui_login_shell", "test_ui_dashboard",
]
for _nom in TESTS:
    ATTENDU[f"tests/{_nom}.py"] = "unittest"

ICONES_REQUISES = (
    "dashboard", "users", "user", "calendar", "heart", "layers", "alert", "wallet", "coins", "chart",
    "file", "database", "shield", "settings", "bell", "plus", "chevron-down", "chevron-down-gray",
    "check", "info", "lock", "logout", "trash",
)


def etat(chemin: str, marqueurs: str | tuple[str, ...]) -> str:
    """'OK', ou la raison pour laquelle le fichier n'est pas bon."""
    fichier = RACINE / chemin
    if not fichier.exists():
        return "ABSENT (créez-le avec New-Item puis collez le code)"
    if fichier.stat().st_size == 0:
        return "VIDE (collez le code puis Ctrl+S)"
    texte = fichier.read_text(encoding="utf-8", errors="replace")
    if chemin.endswith(".py"):
        if texte.lstrip().startswith(("def ", "class ", "@")):
            return "ÉCRASÉ par un extrait (le fichier commence par une fonction) : recollez le fichier entier"
        try:
            ast.parse(texte, filename=chemin)
        except SyntaxError as exc:
            return f"ERREUR DE SYNTAXE ligne {exc.lineno} : {exc.msg}"
    if isinstance(marqueurs, str):
        marqueurs = (marqueurs,)
    manquants = [m for m in marqueurs if m not in texte]
    if manquants:
        return "INCOMPLET ou ancienne version (manque : " + ", ".join(manquants) + ")"
    return "OK"


def importer(chemin: str) -> str:
    """Importe le module : détecte un import manquant ou un nom introuvable."""
    module = chemin[:-3].replace("/", ".")
    try:
        importlib.import_module(module)
    except Exception as exc:                                     # noqa: BLE001 : on veut tout signaler
        return f"IMPORT IMPOSSIBLE : {type(exc).__name__} : {exc}"
    return "OK"


def verifier_icones() -> str:
    dossier = RACINE / "app" / "ui" / "assets" / "icons"
    if not dossier.is_dir():
        return "dossier app\\ui\\assets\\icons absent : lancez  python scripts\\generate_icons.py"
    manquantes = [nom for nom in ICONES_REQUISES if not (dossier / f"{nom}.svg").exists()]
    if manquantes:
        return "icônes manquantes (" + ", ".join(manquantes) + ") : lancez  python scripts\\generate_icons.py"
    return "OK"


def verifier_feuille_de_style() -> str:
    try:
        from app.ui.theme.stylesheet import build
        qss = build()
    except Exception as exc:                                     # noqa: BLE001
        return f"{type(exc).__name__} : {exc}"
    if qss.count("{") != qss.count("}"):
        return "accolades { } non appariées dans un fichier .qss"
    return "OK"


def main() -> int:
    problemes: list[tuple[str, str]] = []
    valides: list[str] = []

    for chemin, marqueurs in ATTENDU.items():
        resultat = etat(chemin, marqueurs)
        if resultat == "OK":
            valides.append(chemin)
        else:
            problemes.append((chemin, resultat))
    for chemin, marqueurs in OPTIONNELS.items():
        if (RACINE / chemin).exists():
            resultat = etat(chemin, marqueurs)
            if resultat == "OK":
                valides.append(chemin)
            else:
                problemes.append((chemin, resultat))

    resultat_icones = verifier_icones()
    if resultat_icones != "OK":
        problemes.append(("icônes de l'interface", resultat_icones))

    # Imports : seulement pour les fichiers déjà valides (sinon l'erreur serait redondante)
    for chemin in valides:
        if chemin.endswith(".py") and not chemin.startswith(("tests/", "scripts/")):
            resultat = importer(chemin)
            if resultat != "OK":
                problemes.append((chemin, resultat))

    if not any(chemin.endswith(".qss") or chemin.endswith("tokens.py") or chemin.endswith("stylesheet.py")
               for chemin, _ in problemes) and resultat_icones == "OK":
        resultat_style = verifier_feuille_de_style()
        if resultat_style != "OK":
            problemes.append(("feuille de style Qt", resultat_style))

    total = len(ATTENDU)
    if problemes:
        print("À corriger :\n")
        for chemin, raison in problemes:
            print(f"  {chemin:<48} {raison}")
        print(f"\n{len(problemes)} problème(s). Corrigez-les (recollez le fichier ENTIER, Ctrl+S) puis relancez ce script.")
        return 1
    print(f"Les {total} fichiers sont présents et complets, les modules s'importent, "
          "icônes et feuille de style sont valides.")
    print(f"Lancez maintenant :  python -m unittest discover -s tests  (attendu : {TESTS_ATTENDUS} tests, OK)")
    return 0


if __name__ == "__main__":
    sys.exit(main())