"""Barre latérale de navigation (13 entrées, rôle administrateur ou secrétaire)."""
from __future__ import annotations

from collections.abc import Collection
from functools import partial

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget, QFrame

from app.ui import icons
from app.ui.navigation import NAV_ITEMS, NavEntry
from app.ui.theme.tokens import Color, Layout
from app.ui.widgets.base import ClickableFrame, make_label, set_property


class NavItem(ClickableFrame):
    """Une entrée de la barre latérale : icône, libellé, état actif."""

    def __init__(self, entry: NavEntry, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.entry = entry
        self.setProperty("role", "nav")
        self.setFixedHeight(Layout.NAV_ITEM_HEIGHT)
        self.setAccessibleName(entry.label)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(12)
        self._icon = QLabel()
        self._icon.setFixedSize(Layout.ICON_SIZE, Layout.ICON_SIZE)
        layout.addWidget(self._icon)
        layout.addWidget(QLabel(entry.label), 1)
        self.set_active(False)

    @property
    def active(self) -> bool:
        return bool(self.property("active"))

    def set_active(self, active: bool) -> None:
        couleur = Color.WHITE if active else Color.SIDEBAR_ICON
        self._icon.setPixmap(icons.icon(self.entry.icon, couleur, Layout.ICON_SIZE).pixmap(
            Layout.ICON_SIZE, Layout.ICON_SIZE))
        set_property(self, "active", active, tree=True)


class Sidebar(QFrame):
    """Barre latérale marine. Signal `navigate(clé de page)` au clic sur une entrée."""

    navigate = Signal(str)

    def __init__(self, *, brand_name: str, brand_sub: str, brand_initials: str, footer: str,
                 items: tuple[NavEntry, ...] = NAV_ITEMS, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(Layout.SIDEBAR_WIDTH)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 20, 14, 16)
        layout.setSpacing(4)

        marque = QHBoxLayout()
        marque.setContentsMargins(6, 0, 0, 0)
        marque.setSpacing(10)
        pastille = QLabel(brand_initials)
        pastille.setObjectName("BrandMark")
        pastille.setFixedSize(Layout.AVATAR_SIZE, Layout.AVATAR_SIZE)
        pastille.setAlignment(Qt.AlignmentFlag.AlignCenter)
        textes = QVBoxLayout()
        textes.setSpacing(0)
        nom = QLabel(brand_name)
        nom.setObjectName("SidebarBrand")
        sous = QLabel(brand_sub)
        sous.setObjectName("SidebarBrandSub")
        textes.addWidget(nom)
        textes.addWidget(sous)
        marque.addWidget(pastille)
        marque.addLayout(textes, 1)
        layout.addLayout(marque)
        layout.addSpacing(14)

        self._items: dict[str, NavItem] = {}
        for entree in items:
            element = NavItem(entree)
            element.clicked.connect(partial(self._on_clicked, entree.key))
            layout.addWidget(element)
            self._items[entree.key] = element
        layout.addStretch(1)
        pied = QLabel(footer)
        pied.setObjectName("SidebarFooter")
        layout.addWidget(pied)
        self._active: str | None = None

    @property
    def active_key(self) -> str | None:
        return self._active

    def item(self, key: str) -> NavItem:
        return self._items[key]

    def set_active(self, key: str) -> None:
        if key not in self._items:
            raise KeyError(key)
        self._active = key
        for cle, element in self._items.items():
            element.set_active(cle == key)

    def set_allowed(self, keys: Collection[str] | None) -> None:
        """None : tout afficher. Sinon, masque les entrées dont la clé n'est pas autorisée
        (confort d'affichage : les services refusent de toute façon une action interdite)."""
        for cle, element in self._items.items():
            element.setVisible(keys is None or cle in keys)

    def _on_clicked(self, key: str) -> None:
        self.set_active(key)
        self.navigate.emit(key)