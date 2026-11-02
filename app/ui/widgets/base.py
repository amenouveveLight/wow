"""Utilitaires communs : style dynamique, étiquettes, zone cliquable."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QMouseEvent
from PySide6.QtWidgets import QFrame, QLabel, QWidget


def repolish(widget: QWidget) -> None:
    """Réapplique le QSS après un changement de propriété dynamique."""
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


def repolish_tree(widget: QWidget) -> None:
    """Idem pour le widget et ses enfants (quand le style des enfants dépend du parent)."""
    repolish(widget)
    for enfant in widget.findChildren(QWidget):
        repolish(enfant)


def set_property(widget: QWidget, name: str, value: object, *, tree: bool = False) -> None:
    """Change une propriété dynamique, et ne réapplique le style que si elle a changé."""
    if widget.property(name) == value:
        return
    widget.setProperty(name, value)
    (repolish_tree if tree else repolish)(widget)


def make_label(text: str = "", role: str | None = None, *, wrap: bool = False,
               **properties: object) -> QLabel:
    """Étiquette stylée par son `role` (voir styles.qss)."""
    etiquette = QLabel(text)
    if role:
        etiquette.setProperty("role", role)
    for nom, valeur in properties.items():
        etiquette.setProperty(nom, valeur)
    etiquette.setWordWrap(wrap)
    return etiquette


class ClickableFrame(QFrame):
    """Zone cliquable et accessible au clavier (Entrée ou Espace)."""

    clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.clicked.emit()
        else:
            super().keyPressEvent(event)