"""Dialogue d'enregistrement de versement."""
from __future__ import annotations

from datetime import date

from PySide6.QtWidgets import QWidget

from app.ui.widgets.dialog import FormDialog
from app.ui.widgets.form import TextInput, NumberInput, DateInput, SelectInput


class AddPaymentDialog(FormDialog):
    """Dialogue pour enregistrer un versement."""
    
    def __init__(self, member_name: str, member_id: int, parent: QWidget | None = None) -> None:
        super().__init__(f"Versement - {member_name}", parent)
        self.member_id = member_id
        
        # Type de versement
        self.type_field = SelectInput("Type", [
            ("Cotisation mensuelle", "mensuelle"),
            ("Cotisation funéraire", "funeraire"),
            ("Cotisation parallèle", "parallele"),
        ], required=True)
        self.add_field(self.type_field)
        
        # Montant
        self.amount_field = NumberInput("Montant (FCFA)", required=True, min_value=100)
        self.add_field(self.amount_field)
        
        # Date
        self.date_field = DateInput("Date du versement", required=True)
        self.date_field.set_value(date.today().strftime("%Y-%m-%d"))
        self.add_field(self.date_field)
        
        # Note
        self.note_field = TextInput("Note", placeholder="Optionnel")
        self.add_field(self.note_field)
    
    def get_data(self) -> dict:
        return {
            "membre_id": self.member_id,
            "rubrique": self.type_field.value(),
            "montant": int(self.amount_field.value()),
            "date_versement": self.date_field.value(),
            "note": self.note_field.value(),
        }
