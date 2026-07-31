"""
Utilitaires de génération de QR Codes pour CHERE.
Utilise la bibliothèque qrcode + Pillow (PIL).
"""
from io import BytesIO
from functools import lru_cache
from flask import request, url_for, current_app
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import SquareModuleDrawer, RoundedModuleDrawer
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H


CHERE_PRIMARY = "#1E40AF"  # Bleu CHERE, à ajuster au palette si besoin
CHERE_DARK = "#0F172A"
CHERE_LIGHT = "#FFFFFF"


def _make_qr_image(
    data: str,
    size: int = 256,
    box_size: int = 10,
    border: int = 2,
    error_correction=ERROR_CORRECT_M,
    dark_color: str = CHERE_DARK,
    light_color: str = CHERE_LIGHT,
    rounded: bool = True,
) -> "PIL.Image.Image":
    """Génère une image Pillow d'un QR Code.

    Args:
        data: Le contenu à encoder (URL, texte, etc.)
        size: Taille finale max du côté en px (juste pour référence, qrcode utilise box_size)
        box_size: Taille d'un module QR en pixels
        border: Epaisseur de la bordure en modules (min 4 selon spec QR, ici 2 ok pour UI)
        error_correction: Niveau de correction d'erreur (L/M/Q/H)
        dark_color: Couleur des modules
        light_color: Couleur de fond
        rounded: Arrondit les modules pour un style moderne
    """
    from PIL import Image  # lazy import

    qr = qrcode.QRCode(
        version=None,
        error_correction=error_correction,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    drawer = RoundedModuleDrawer() if rounded else SquareModuleDrawer()
    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=drawer,
        fill_color=dark_color,
        back_color=light_color,
    ).convert("RGBA")

    # Redimensionne proprement vers la taille demandée
    if size and (img.size[0] != size or img.size[1] != size):
        img = img.resize((size, size), Image.LANCZOS)
    return img


def image_to_png_bytes(img) -> bytes:
    """Convertit une image Pillow en PNG (bytes)."""
    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def generate_qr_png_bytes(data: str, **kwargs) -> bytes:
    """Raccourci : retourne les bytes PNG d'un QR Code."""
    img = _make_qr_image(data, **kwargs)
    return image_to_png_bytes(img)


def _public_url_for(endpoint, **values):
    """Construit l'URL publique absolue (pour l'encodage dans le QR)."""
    try:
        return url_for(endpoint, _external=True, **values)
    except Exception:
        # Fallback si _external échoue (contexte incomplet)
        base = request.url_root.rstrip("/") if request else ""
        path = url_for(endpoint, **values)
        return f"{base}{path}"


def qr_for_events_list(size: int = 256):
    """QR pour la page de liste des événements."""
    return generate_qr_png_bytes(_public_url_for("events.index"), size=size)


def qr_for_event_detail(slug: str, size: int = 256):
    """QR pour la page détail d'un événement."""
    return generate_qr_png_bytes(
        _public_url_for("events.event_detail", slug=slug),
        size=size,
        error_correction=ERROR_CORRECT_Q,
    )
