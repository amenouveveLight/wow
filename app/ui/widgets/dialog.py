"""Boîtes de dialogue modales pour les formulaires."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QLabel, QPushButton,
                               QVBoxLayout, QWidget)

from app.ui.theme.tokens import Color, Layout
from app.ui.widgets.base import make_label
from app.ui.widgets.button import AppButton, Variant


class FormDialog(QDialog):
    """Dialogue de formulaire générique."""
    
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*Layout.PAGE_MARGINS)
        layout.setSpacing(Layout.SECTION_GAP)
        
        # Container pour le formulaire
        self.form_container = QWidget()
        self.form_layout = QVBoxLayout(self.form_container)
        self.form_layout.setSpacing(12)
        layout.addWidget(self.form_container)
        
        # Boutons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
        self._fields = []
    
    def add_field(self, field: QWidget) -> None:
        """Ajoute un champ au formulaire."""
        self.form_layout.addWidget(field)
        self._fields.append(field)
    
    def validate(self) -> bool:
        """Valide tous les champs requis."""
        for field in self._fields:
            if hasattr(field, 'is_valid') and not field.is_valid():
                if hasattr(field, 'mark_invalid'):
                    field.mark_invalid(True)
                return False
        return True
    
    def accept(self) -> None:
        """Accepte le dialogue après validation."""
        if self.validate():
            super().accept()
