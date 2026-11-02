"""Dialogue d'ajout de membre."""
from __future__ import annotations

from datetime import date

from PySide6.QtWidgets import QWidget

from app.ui.widgets.dialog import FormDialog
from app.ui.widgets.form import TextInput, SelectInput, DateInput


class AddMemberDialog(FormDialog):
    """Dialogue pour ajouter un nouveau membre."""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Ajouter un membre", parent)
        
        # Nom complet
        self.name_field = TextInput("Nom complet", required=True, placeholder="Ex: Komlan Akakpo")
        self.add_field(self.name_field)
        
        # Sexe
        self.sex_field = SelectInput("Sexe", [("Masculin", "M"), ("Féminin", "F")], required=True)
        self.add_field(self.sex_field)
        
        # Date d'adhésion
        self.adhesion_field = DateInput("Date d'adhésion", required=True)
        self.adhesion_field.set_value(date.today().strftime("%Y-%m-%d"))
        self.add_field(self.adhesion_field)
    
    def get_data(self) -> dict:
        """Retourne les données du formulaire."""
        return {
            "nom": self.name_field.value(),
            "sexe": self.sex_field.value(),
            "date_adhesion": self.adhesion_field.value(),
        }
