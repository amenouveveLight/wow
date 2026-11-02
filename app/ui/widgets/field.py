"""Champ de formulaire : libellé, contrôle, aide ou message d'erreur."""
from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget

from app.ui.widgets.base import make_label, repolish, set_property


class FormField(QWidget):
    """Associe un contrôle (QLineEdit, QComboBox…) à son libellé et à un message d'erreur.
    L'état d'erreur est la propriété dynamique `error` du contrôle, stylée par styles.qss."""

    def __init__(self, label: str, widget: QWidget, *, hint: str | None = None,
                 required: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.widget = widget
        self._hint = hint
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self._label = make_label(f"{label} *" if required else label, "field-label")
        self._message = make_label("", "caption", wrap=True)
        for element in (self._label, widget, self._message):
            layout.addWidget(element)
        self.set_error(None)

    @property
    def has_error(self) -> bool:
        return bool(self.widget.property("error"))

    def set_error(self, message: str | None) -> None:
        """Affiche (ou efface avec None) le message d'erreur sous le champ."""
        en_erreur = bool(message)
        set_property(self.widget, "error", en_erreur)
        self._message.setProperty("role", "field-error" if en_erreur else "caption")
        repolish(self._message)
        texte = message if en_erreur else (self._hint or "")
        self._message.setText(texte)
        self._message.setVisible(bool(texte))

    def mark_invalid(self, invalid: bool) -> None:
        """Bordure rouge sans message (ex. identifiants refusés : le message est dans un bandeau)."""
        set_property(self.widget, "error", invalid)