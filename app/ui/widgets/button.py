"""Boutons de la maquette : principal, secondaire, danger, lien, et bouton d'icône."""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QPushButton, QWidget

from app.ui import icons
from app.ui.theme.tokens import Color, Layout
from app.ui.widgets.base import set_property


class Variant:
    PRIMARY = "primary"
    SECONDARY = "secondary"
    DANGER = "danger"
    LINK = "link"
    ALL = (PRIMARY, SECONDARY, DANGER, LINK)


_ICON_COLORS = {
    Variant.PRIMARY: Color.WHITE,
    Variant.DANGER: Color.WHITE,
    Variant.SECONDARY: Color.NAVY_900,
    Variant.LINK: Color.NAVY_700,
}


class AppButton(QPushButton):
    """Bouton à 4 variantes. États (repos, survol, appuyé, désactivé, focus) gérés par styles.qss."""

    def __init__(self, text: str = "", variant: str = Variant.SECONDARY,
                 icon_name: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self._icon_name = icon_name
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.set_variant(variant)

    @property
    def variant(self) -> str:
        return str(self.property("variant"))

    def set_variant(self, variant: str) -> None:
        if variant not in Variant.ALL:
            raise ValueError(f"Variante de bouton inconnue : {variant}")
        set_property(self, "variant", variant)
        if variant == Variant.LINK:
            self.setMinimumHeight(0)
            self.setMaximumHeight(16777215)
        else:
            self.setFixedHeight(Layout.CONTROL_HEIGHT)
        self._refresh_icon()

    def set_icon_name(self, icon_name: str | None) -> None:
        self._icon_name = icon_name
        self._refresh_icon()

    def _refresh_icon(self) -> None:
        if self._icon_name:
            self.setIcon(icons.icon(self._icon_name, _ICON_COLORS[self.variant], 16))
            self.setIconSize(QSize(16, 16))


class IconButton(QPushButton):
    """Bouton carré à icône seule (ex. cloche des notifications)."""

    def __init__(self, icon_name: str, tooltip: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("role", "icon-button")
        self.setFixedSize(Layout.CONTROL_HEIGHT, Layout.CONTROL_HEIGHT)
        self.setIcon(icons.icon(icon_name, Color.NAVY_900, Layout.ICON_SIZE))
        self.setIconSize(QSize(Layout.ICON_SIZE, Layout.ICON_SIZE))
        self.setToolTip(tooltip)
        self.setAccessibleName(tooltip or icon_name)
        self.setCursor(Qt.CursorShape.PointingHandCursor)