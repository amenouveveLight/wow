"""Fenêtre principale : écran de connexion, puis coquille de l'application."""
from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QStackedWidget

from app.config import APP_NAME
from app.ui.mock import data
from app.ui.mock.dashboard import MockDashboard
from app.ui.mock.dashboard_extras import AvecDonneesDemo
from app.ui.mock.members import MockMembers
from app.ui.mock.monthly import MockMonthly
from app.ui.mock.funeral import MockFuneral
from app.ui.mock.parallel import MockParallel
from app.ui.mock.fines import MockFines
from app.ui.mock.expenses import MockExpenses
from app.ui.mock.leftovers import MockLeftovers
from app.ui.mock.balance import MockBalance
from app.ui.mock.reports import MockReports
from app.ui.navigation import Page
from app.ui.ports import AuthPort, DashboardPort, UserInfo
from app.ui.ports_members import MembersPort
from app.ui.ports_monthly import MonthlyPort
from app.ui.ports_funeral import FuneralPort
from app.ui.ports_parallel import ParallelPort
from app.ui.ports_fines import FinesPort
from app.ui.ports_expenses import ExpensesPort
from app.ui.ports_leftovers import LeftoversPort
from app.ui.ports_balance import BalancePort
from app.ui.ports_reports import ReportsPort
from app.ui.presenters.dashboard import DashboardPresenter
from app.ui.presenters.login import LoginPresenter
from app.ui.presenters.members import MembersPresenter
from app.ui.presenters.monthly import MonthlyPresenter
from app.ui.presenters.funeral import FuneralPresenter
from app.ui.presenters.parallel import ParallelPresenter
from app.ui.presenters.fines import FinesPresenter
from app.ui.presenters.expenses import ExpensesPresenter
from app.ui.presenters.leftovers import LeftoversPresenter
from app.ui.presenters.balance import BalancePresenter
from app.ui.presenters.reports import ReportsPresenter
from app.ui.presenters.backups import BackupsPresenter
from app.ui.presenters.audit import AuditPresenter
from app.ui.presenters.settings import SettingsPresenter
from app.ui.theme.tokens import Layout
from app.ui.views.dashboard import DashboardView
from app.ui.views.login import LoginView
from app.ui.views.members import MembersView
from app.ui.views.monthly import MonthlyView
from app.ui.views.funeral import FuneralView
from app.ui.views.parallel import ParallelView
from app.ui.views.fines import FinesView
from app.ui.views.expenses import ExpensesView
from app.ui.views.leftovers import LeftoversView
from app.ui.views.balance import BalanceView
from app.ui.views.reports import ReportsView
from app.ui.views.backups import BackupsView
from app.ui.views.audit import AuditView
from app.ui.views.settings import SettingsView
from app.ui.views.shell import Shell
from app.ui.widgets.banner import Toast

_DIALOGUES = "La boîte de dialogue arrive à l'étape des dialogues."


class MainWindow(QMainWindow):
    """Une seule fenêtre : un QStackedWidget [connexion, coquille]. La barre de titre est celle de Windows."""

    def __init__(self, auth: AuthPort, dashboard: DashboardPort | None = None,
                 members: MembersPort | None = None, monthly: MonthlyPort | None = None,
                 funeral: FuneralPort | None = None, parallel: ParallelPort | None = None,
                 fines: FinesPort | None = None, expenses: ExpensesPort | None = None,
                 leftovers: LeftoversPort | None = None, balance: BalancePort | None = None,
                 reports: ReportsPort | None = None) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(*Layout.MIN_WINDOW)
        self.resize(1360, 860)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.login_view = LoginView(brand_name=data.BRAND_NAME, brand_initials=data.BRAND_INITIALS,
                                    tagline=data.LOGIN_TAGLINE, features=data.LOGIN_FEATURES,
                                    footer=data.LOGIN_FOOTER)
        self.shell = Shell(association_name=data.ASSOCIATION_NAME, brand_name=data.BRAND_NAME,
                           brand_sub=data.BRAND_SUB, brand_initials=data.BRAND_INITIALS,
                           footer=data.SIDEBAR_FOOTER)
        self.shell.set_exercises(list(data.EXERCISES))
        self.shell.set_notifications(list(data.NOTIFICATIONS))
        self.shell.statusbar.set_database(True, "Base de données locale : connectée")
        self.shell.statusbar.set_last_backup(data.LAST_BACKUP)
        self.shell.statusbar.set_notice(data.DEMO_NOTICE)
        self.stack.addWidget(self.login_view)
        self.stack.addWidget(self.shell)
        self.toast = Toast(self.stack)

        # Tableau de bord (AvecDonneesDemo complète graphique, opérations et dettes tant que le mock ne le fait pas)
        self.dashboard_view = DashboardView()
        self.shell.set_page(Page.DASHBOARD, self.dashboard_view)
        port = AvecDonneesDemo(dashboard or MockDashboard())
        self.dashboard_presenter = DashboardPresenter(self.dashboard_view, port, self)

        # Membres
        self.members_view = MembersView()
        self.shell.set_page(Page.MEMBERS, self.members_view)
        self.members_presenter = MembersPresenter(self.members_view, members or MockMembers(), self)

        # Cotisations mensuelles
        self.monthly_view = MonthlyView()
        self.shell.set_page(Page.MONTHLY, self.monthly_view)
        self.monthly_presenter = MonthlyPresenter(self.monthly_view, monthly or MockMonthly(), self)

        # Cotisations funéraires
        self.funeral_view = FuneralView()
        self.shell.set_page(Page.FUNERAL, self.funeral_view)
        self.funeral_presenter = FuneralPresenter(self.funeral_view, funeral or MockFuneral(), self)

        # Cotisations parallèles
        self.parallel_view = ParallelView()
        self.shell.set_page(Page.PARALLEL, self.parallel_view)
        self.parallel_presenter = ParallelPresenter(self.parallel_view, parallel or MockParallel(), self)

        # Amendes
        self.fines_view = FinesView()
        self.shell.set_page(Page.FINES, self.fines_view)
        self.fines_presenter = FinesPresenter(self.fines_view, fines or MockFines(), self)

        # Dépenses
        self.expenses_view = ExpensesView()
        self.shell.set_page(Page.EXPENSES, self.expenses_view)
        self.expenses_presenter = ExpensesPresenter(self.expenses_view, expenses or MockExpenses(), self)

        # Reliquats
        self.leftovers_view = LeftoversView()
        self.shell.set_page(Page.LEFTOVERS, self.leftovers_view)
        self.leftovers_presenter = LeftoversPresenter(self.leftovers_view, leftovers or MockLeftovers(), self)

        # Bilan financier
        self.balance_view = BalanceView()
        self.shell.set_page(Page.BALANCE, self.balance_view)
        self.balance_presenter = BalancePresenter(self.balance_view, balance or MockBalance(), self)

        # Rapports et exports
        self.reports_view = ReportsView()
        self.shell.set_page(Page.REPORTS, self.reports_view)
        self.reports_presenter = ReportsPresenter(self.reports_view, reports or MockReports(), self)

        # Sauvegardes
        self.backups_view = BackupsView()
        self.shell.set_page(Page.BACKUPS, self.backups_view)
        self.backups_presenter = BackupsPresenter(self.backups_view, reports or MockReports(), self)

        # Journal d'audit
        self.audit_view = AuditView()
        self.shell.set_page(Page.AUDIT, self.audit_view)
        self.audit_presenter = AuditPresenter(self.audit_view, reports or MockReports(), self)

        # Paramètres
        self.settings_view = SettingsView()
        self.shell.set_page(Page.SETTINGS, self.settings_view)
        self.settings_presenter = SettingsPresenter(self.settings_view, self)

        self.login_presenter = LoginPresenter(self.login_view, auth, self)
        self.login_presenter.authenticated.connect(self._on_authenticated)
        self.shell.logout_requested.connect(self._on_logout)
        self.shell.password_requested.connect(lambda: self._bientot("Changement de mot de passe", _DIALOGUES))
        self.shell.exercise_selected.connect(self.dashboard_presenter.show_exercise)
        self.shell.exercise_selected.connect(self.members_presenter.show_exercise)
        self.shell.exercise_selected.connect(self.monthly_presenter.show_exercise)
        self.shell.exercise_selected.connect(self.funeral_presenter.show_exercise)
        self.shell.exercise_selected.connect(self.parallel_presenter.show_exercise)
        self.shell.exercise_selected.connect(self.fines_presenter.show_exercise)
        self.shell.exercise_selected.connect(self.expenses_presenter.show_exercise)
        self.shell.exercise_selected.connect(self.leftovers_presenter.show_exercise)
        self.shell.exercise_selected.connect(self.balance_presenter.show_exercise)
        self.shell.exercise_selected.connect(self.reports_presenter.show_exercise)
        self.shell.exercise_selected.connect(self.backups_presenter.show_exercise)
        self.shell.exercise_selected.connect(self.audit_presenter.show_exercise)
        self.shell.exercise_selected.connect(lambda libelle: self.toast.popup(
            "success", f"Exercice {libelle} sélectionné", "Aperçu : les données restent fictives."))

        vue = self.dashboard_view
        vue.payment_requested.connect(lambda: self._bientot("Enregistrer un versement", _DIALOGUES))
        vue.expense_requested.connect(lambda: self._bientot("Nouvelle dépense", _DIALOGUES))
        vue.member_requested.connect(lambda: self.shell.show_page(Page.MEMBERS))
        vue.collecte_requested.connect(lambda: self._bientot("Nouvelle collecte", _DIALOGUES))
        vue.export_requested.connect(lambda: self._bientot(
            "Exporter le bilan", "L'écran « Rapports et exports » arrive plus tard."))
        vue.backup_requested.connect(lambda: self._bientot(
            "Sauvegarder", "L'écran « Sauvegardes » arrive plus tard."))

        membres = self.members_view
        membres.export_requested.connect(lambda: self._bientot(
            "Exporter les membres", "L'écran « Rapports et exports » arrive plus tard."))
        membres.add_requested.connect(lambda: self._bientot("Ajouter un membre", _DIALOGUES))
        membres.member_action_requested.connect(lambda carnet: self._bientot(
            f"Carnet {carnet}", "Le menu d'actions du membre arrive plus tard."))
        self.show_login()

    def _bientot(self, titre: str, texte: str) -> None:
        self.toast.popup("warning", titre, texte)

    def show_login(self) -> None:
        self.login_view.reset()
        self.stack.setCurrentWidget(self.login_view)
        self.login_view.focus_identifier()

    def _on_authenticated(self, user: UserInfo) -> None:
        self.shell.start(user)
        self.dashboard_presenter.show_exercise(self.shell.current_exercise_label)
        self.members_presenter.show_exercise(self.shell.current_exercise_label)
        self.monthly_presenter.show_exercise(self.shell.current_exercise_label)
        self.funeral_presenter.show_exercise(self.shell.current_exercise_label)
        self.parallel_presenter.show_exercise(self.shell.current_exercise_label)
        self.fines_presenter.show_exercise(self.shell.current_exercise_label)
        self.expenses_presenter.show_exercise(self.shell.current_exercise_label)
        self.leftovers_presenter.show_exercise(self.shell.current_exercise_label)
        self.balance_presenter.show_exercise(self.shell.current_exercise_label)
        self.reports_presenter.show_exercise(self.shell.current_exercise_label)
        self.backups_presenter.show_exercise(self.shell.current_exercise_label)
        self.audit_presenter.show_exercise(self.shell.current_exercise_label)
        self.settings_presenter.show()
        self.stack.setCurrentWidget(self.shell)
        self.toast.popup("success", f"Bienvenue, {user.full_name}", user.role_label)

    def _on_logout(self) -> None:
        self.shell.close_popover()
        self.show_login()
