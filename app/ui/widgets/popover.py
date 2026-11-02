"""Popover : petite fenêtre flottante ancrée à un widget (notifications, exercice, menu utilisateur)."""
from __future__ import annotations

from collections.abc import Callable
from functools import partial

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QHideEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.ui import icons
from app.ui.theme import apply_shadow
from app.ui.theme.tokens import Color, Shadow
from app.ui.widgets.base import ClickableFrame, make_label
from app.ui.widgets.card import Separator

_MARGIN = 20      # marge transparente autour du panneau : la place de l'ombre


class Popover(QFrame):
    """Fenêtre sans cadre qui se ferme au clic à l'extérieur (comportement Qt.Popup)."""

    dismissed = Signal()

    def __init__(self, parent: QWidget | None = None, *, width: int = 320) -> None:
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint
                         | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(width + 2 * _MARGIN)
        externe = QVBoxLayout(self)
        externe.setContentsMargins(_MARGIN, _MARGIN, _MARGIN, _MARGIN)
        self.panel = QFrame()
        self.panel.setObjectName("Popover")
        apply_shadow(self.panel, Shadow.POPOVER)
        externe.addWidget(self.panel)
        self.body = QVBoxLayout(self.panel)
        self.body.setContentsMargins(8, 8, 8, 8)
        self.body.setSpacing(2)
        self._items: list[ClickableFrame] = []

    def items(self) -> list[ClickableFrame]:
        return list(self._items)

    def item_count(self) -> int:
        return len(self._items)

    def add_header(self, title: str, subtitle: str = "") -> None:
        bloc = QWidget()
        colonne = QVBoxLayout(bloc)
        colonne.setContentsMargins(10, 8, 10, 8)
        colonne.setSpacing(2)
        colonne.addWidget(make_label(title, "popover-header"))
        if subtitle:
            colonne.addWidget(make_label(subtitle, "popover-text"))
        self.body.addWidget(bloc)

    def add_separator(self) -> None:
        self.body.addSpacing(4)
        self.body.addWidget(Separator())
        self.body.addSpacing(4)

    def add_empty(self, text: str) -> None:
        etiquette = make_label(text, "popover-text", wrap=True)
        etiquette.setContentsMargins(10, 12, 10, 12)
        self.body.addWidget(etiquette)

    def add_item(self, title: str, subtitle: str = "", *, icon_name: str | None = None,
                 tone: str | None = None, checked: bool = False,
                 on_click: Callable[[], None] | None = None) -> ClickableFrame:
        """Ligne cliquable. `tone="danger"` pour une action destructive (rouge). Le popover se ferme
        avant l'appel de `on_click`."""
        item = ClickableFrame()
        item.setProperty("role", "popover-item")
        if tone:
            item.setProperty("tone", tone)
        item.setAccessibleName(title)
        ligne = QHBoxLayout(item)
        ligne.setContentsMargins(10, 8, 10, 8)
        ligne.setSpacing(10)
        if icon_name:
            icone = QLabel()
            icone.setFixedSize(18, 18)
            couleur = Color.DANGER_600 if tone == "danger" else Color.NAVY_700
            icone.setPixmap(icons.icon(icon_name, couleur, 18).pixmap(18, 18))
            ligne.addWidget(icone, 0, Qt.AlignmentFlag.AlignVCenter)
        textes = QVBoxLayout()
        textes.setSpacing(2)
        textes.addWidget(make_label(title, "popover-title", wrap=True))
        if subtitle:
            textes.addWidget(make_label(subtitle, "popover-text", wrap=True))
        ligne.addLayout(textes, 1)
        if checked:
            coche = QLabel()
            coche.setFixedSize(18, 18)
            coche.setPixmap(icons.icon("check", Color.NAVY_700, 18).pixmap(18, 18))
            ligne.addWidget(coche)
        item.clicked.connect(partial(self._activate, on_click))
        self.body.addWidget(item)
        self._items.append(item)
        return item

    def _activate(self, callback: Callable[[], None] | None) -> None:
        self.close()
        if callback is not None:
            callback()

    def popup_below(self, anchor: QWidget, *, align: str = "right") -> None:
        """Ouvre le popover sous `anchor`, bord droit (ou gauche) aligné sur lui."""
        layout = self.layout()
        layout.activate()
        self.adjustSize()
        bas_gauche = anchor.mapToGlobal(QPoint(0, anchor.height()))
        if align == "right":
            x = bas_gauche.x() + anchor.width() - self.width() + _MARGIN
        else:
            x = bas_gauche.x() - _MARGIN
        self.move(x, bas_gauche.y() + 4 - _MARGIN)
        self.show()

    def hideEvent(self, event: QHideEvent) -> None:
        self.dismissed.emit()
        super().hideEvent(event)