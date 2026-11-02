"""Barre supérieure : association, exercice, notifications, utilisateur connecté."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.ui import icons
from app.ui.theme.tokens import Color, Layout
from app.ui.widgets.base import ClickableFrame
from app.ui.widgets.button import IconButton


def _icone(nom: str, couleur: str, taille: int) -> QLabel:
    etiquette = QLabel()
    etiquette.setFixedSize(taille, taille)
    etiquette.setPixmap(icons.icon(nom, couleur, taille).pixmap(taille, taille))
    return etiquette


class TopBar(QFrame):
    """Émet des signaux avec le widget d'ancrage ; la vue ouvre le popover correspondant."""

    exercise_requested = Signal(QWidget)
    notifications_requested = Signal(QWidget)
    user_requested = Signal(QWidget)

    def __init__(self, association_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("TopBar")
        self.setFixedHeight(Layout.TOPBAR_HEIGHT)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 0, 28, 0)
        layout.setSpacing(16)

        nom = QLabel(association_name)
        nom.setObjectName("AssociationName")
        layout.addWidget(nom)
        layout.addStretch(1)

        self.exercise_select = ClickableFrame()
        self.exercise_select.setObjectName("ExerciseSelect")
        self.exercise_select.setAccessibleName("Choisir l'exercice")
        ligne = QHBoxLayout(self.exercise_select)
        ligne.setContentsMargins(12, 8, 10, 8)
        ligne.setSpacing(8)
        self._exercise_text = QLabel("")
        ligne.addWidget(_icone("calendar", Color.NAVY_700, 16))
        ligne.addWidget(self._exercise_text)
        ligne.addWidget(_icone("chevron-down", Color.NAVY_700, 16))
        layout.addWidget(self.exercise_select)

        self.bell_button = IconButton("bell", "Notifications")
        layout.addWidget(self.bell_button)

        self.user_chip = ClickableFrame()
        self.user_chip.setObjectName("UserChip")
        self.user_chip.setAccessibleName("Menu utilisateur")
        chip = QHBoxLayout(self.user_chip)
        chip.setContentsMargins(0, 0, 0, 0)
        chip.setSpacing(10)
        self._avatar = QLabel("")
        self._avatar.setObjectName("Avatar")
        self._avatar.setFixedSize(Layout.AVATAR_SIZE, Layout.AVATAR_SIZE)
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        textes = QVBoxLayout()
        textes.setSpacing(0)
        self._user_name = QLabel("")
        self._user_name.setObjectName("UserName")
        self._user_role = QLabel("")
        self._user_role.setObjectName("UserRole")
        textes.addWidget(self._user_name)
        textes.addWidget(self._user_role)
        chip.addWidget(self._avatar)
        chip.addLayout(textes)
        layout.addWidget(self.user_chip)

        self.exercise_select.clicked.connect(lambda: self.exercise_requested.emit(self.exercise_select))
        self.bell_button.clicked.connect(lambda: self.notifications_requested.emit(self.bell_button))
        self.user_chip.clicked.connect(lambda: self.user_requested.emit(self.user_chip))

    def set_exercise(self, text: str) -> None:
        self._exercise_text.setText(text)

    def set_user(self, name: str, role_label: str) -> None:
        initiales = "".join(mot[0] for mot in name.split()[:2]).upper() or "?"
        self._avatar.setText(initiales)
        self._user_name.setText(name)
        self._user_role.setText(role_label)