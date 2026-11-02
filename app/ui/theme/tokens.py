"""Design system de la maquette Figma « Gestion d'association » (constantes).

Source de vérité UNIQUE : styles.qss est un modèle dont les jetons @nom sont remplacés
par les valeurs d'ici (voir stylesheet.py). Les valeurs viennent de la page
« Système de design » du fichier Figma ; celles marquées « extension » complètent la
maquette (états non dessinés) et sont à valider visuellement.
"""
from __future__ import annotations

from typing import Final, NamedTuple


class Color:
    # Marque
    NAVY_900: Final = "#0B1F3F"
    NAVY_700: Final = "#14305C"
    NAVY_100: Final = "#DCE4F0"
    NAVY_50: Final = "#EEF2F8"
    # Fonds, bordures, textes
    BG_APP: Final = "#F6F5F1"
    BG_SURFACE: Final = "#FFFFFF"
    BORDER: Final = "#E2E4EA"
    GRAY_100: Final = "#F0F1F4"
    GRAY_500: Final = "#6B7280"
    GRAY_900: Final = "#111827"
    WHITE: Final = "#FFFFFF"
    # Sémantique financière
    SUCCESS_600: Final = "#1E8E5A"
    SUCCESS_50: Final = "#E3F4EB"
    DANGER_600: Final = "#C62F2F"
    DANGER_50: Final = "#FBE6E6"
    WARNING_600: Final = "#C9731A"
    WARNING_50: Final = "#FDEFDD"
    # Boutons : états du composant « Bouton » de la maquette
    BTN_PRIMARY_HOVER: Final = "#14305C"
    BTN_PRIMARY_PRESSED: Final = "#07142B"
    BTN_PRIMARY_DISABLED: Final = "#919AA8"
    BTN_DANGER_HOVER: Final = "#A92626"
    BTN_DANGER_PRESSED: Final = "#8F1F1F"
    BTN_DANGER_DISABLED: Final = "#E5A1A1"
    BTN_DISABLED_TEXT: Final = "#919AA8"
    # Barre latérale
    SIDEBAR_ICON: Final = "#B8C6E0"
    # Extensions (non dessinées dans la maquette)
    NAV_HOVER: Final = "#102B52"
    BORDER_STRONG: Final = "#C9CED8"
    FOCUS_RING: Final = "#3B6FD4"


class Font:
    FAMILY: Final = "Inter"
    FALLBACKS: Final = ("Segoe UI", "Arial")
    QSS_STACK: Final = '"Inter", "Segoe UI", Arial, sans-serif'


class FontSize:
    """Tailles en pixels."""
    DISPLAY: Final = 32        # titre de la page de connexion
    TITLE: Final = 24          # titre de page
    STAT: Final = 22           # montant d'une carte statistique
    MODAL_TITLE: Final = 18
    CARD_TITLE: Final = 16
    BODY: Final = 14
    CELL: Final = 13           # cellules de tableau
    CAPTION: Final = 12        # légendes, en-têtes de colonnes
    SMALL: Final = 11


class Radius:
    CONTROL: Final = 8         # boutons, champs, éléments de menu
    BANNER: Final = 10
    CARD: Final = 12
    MODAL: Final = 14
    PILL: Final = 999


class Space:
    XS: Final = 4
    SM: Final = 8
    MD: Final = 12
    LG: Final = 16
    XL: Final = 20
    XXL: Final = 24
    PAGE: Final = 28


class Layout:
    DESIGN_WIDTH: Final = 1440
    MIN_WINDOW: Final = (1100, 680)
    SIDEBAR_WIDTH: Final = 248
    TOPBAR_HEIGHT: Final = 60
    STATUSBAR_HEIGHT: Final = 28
    PAGE_MARGINS: Final = (28, 24, 28, 28)       # gauche, haut, droite, bas
    SECTION_GAP: Final = 20
    CARD_GAP: Final = 16
    CARD_PADDING: Final = 20
    CONTROL_HEIGHT: Final = 36
    INPUT_HEIGHT: Final = 38
    TABLE_ROW_HEIGHT: Final = 40
    TABLE_HEADER_HEIGHT: Final = 40
    NAV_ITEM_HEIGHT: Final = 40
    ICON_SIZE: Final = 18
    AVATAR_SIZE: Final = 32
    LOGIN_BRAND_WIDTH: Final = 640
    LOGIN_CARD_WIDTH: Final = 420
    MODAL_FORM_WIDTH: Final = 580
    MODAL_WIDE_WIDTH: Final = 640
    MODAL_CONFIRM_WIDTH: Final = 520


class ShadowSpec(NamedTuple):
    blur: int
    dx: int
    dy: int
    rgba: tuple[int, int, int, int]


class Shadow:
    """Qt n'a pas de box-shadow en QSS : ces valeurs alimentent QGraphicsDropShadowEffect."""
    CARD: Final = ShadowSpec(8, 0, 1, (10, 31, 64, 15))
    POPOVER: Final = ShadowSpec(24, 0, 8, (10, 31, 64, 46))
    MODAL: Final = ShadowSpec(32, 0, 12, (10, 31, 64, 64))


OVERLAY_RGBA: Final = (11, 31, 63, 140)      # voile derrière les modales (navy 900 à 55 %)


def _constants(cls: type) -> dict[str, object]:
    return {k: v for k, v in vars(cls).items() if k.isupper()}


def color_items() -> list[tuple[str, str]]:
    """Toutes les couleurs, dans l'ordre de déclaration (aperçu du thème, tests)."""
    return [(k, str(v)) for k, v in _constants(Color).items()]


def mapping() -> dict[str, str]:
    """Jetons utilisables dans styles.qss : @navy_900, @fs_body, @radius_card, @font_family…"""
    result: dict[str, str] = {"font_family": Font.QSS_STACK}
    result.update({k.lower(): str(v) for k, v in _constants(Color).items()})
    result.update({f"fs_{k.lower()}": f"{v}px" for k, v in _constants(FontSize).items()})
    result.update({f"radius_{k.lower()}": f"{v}px" for k, v in _constants(Radius).items()})
    return result