"""
Service d'envoi SMS et WhatsApp pour les invitations aux événements CHERE.

Fournit:
- Simulation d'envoi SMS (intégrable avec Twilio, Africa's Talking, etc.)
- Génération de liens WhatsApp (wa.me) pour les diffusions manuelles
- Normalisation des numéros de téléphone (format Rwanda +250 par défaut)
"""
import os
import logging
from datetime import datetime
from urllib.parse import quote
from app.extensions import db
from app.models import EventSmsRecipient

logger = logging.getLogger(__name__)

# Configuration depuis les variables d'environnement
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
AT_USERNAME = os.getenv("AT_USERNAME")
AT_API_KEY = os.getenv("AT_API_KEY")
AT_SHORTCODE = os.getenv("AT_SHORTCODE", "CHERE")

DEFAULT_SENDER_NAME = "CHERE"
ENABLE_LIVE_SMS = os.getenv("ENABLE_LIVE_SMS", "false").lower() == "true"


def normalize_phone_number(phone: str) -> str | None:
    """Normalise un numéro de téléphone au format international sans '+'.

    Exemples:
      +250 7xx xxx xxx -> 2507xxxxxxxxx
      07xx xxx xxx    -> 2507xxxxxxxxx
      7xx xxx xxx     -> 2507xxxxxxxxx
    """
    if not phone:
        return None
    digits = "".join(c for c in phone if c.isdigit())
    if not digits:
        return None
    if digits.startswith("0") and len(digits) == 10:
        return "250" + digits[1:]
    if digits.startswith("250") and len(digits) == 12:
        return digits
    if len(digits) == 9:
        return "250" + digits
    if len(digits) >= 10:
        return digits
    return None


def format_phone_display(phone: str) -> str:
    """Affiche un numéro sous forme lisible: +250 7xx xxx xxx."""
    normalized = normalize_phone_number(phone)
    if not normalized:
        return phone or ""
    if normalized.startswith("250") and len(normalized) == 12:
        return f"+250 {normalized[3:6]} {normalized[6:9]} {normalized[9:]}"
    return f"+{normalized}"


def build_whatsapp_link(phone: str, message: str) -> str:
    """Génère un lien wa.me pré-rempli pour un envoi manuel WhatsApp."""
    normalized = normalize_phone_number(phone)
    if not normalized:
        return ""
    encoded_msg = quote(message)
    return f"https://wa.me/{normalized}?text={encoded_msg}"


class SmsService:
    """Service central d'envoi SMS & WhatsApp avec simulation pour le développement."""

    def __init__(self):
        self.live_enabled = ENABLE_LIVE_SMS
        self.sender = DEFAULT_SENDER_NAME
        self._twilio_client = None
        self._at_client = None

    # -- Twilio lazy-load --
    @property
    def twilio_client(self):
        if self._twilio_client is None and TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
            try:
                from twilio.rest import Client
                self._twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            except ImportError:
                logger.warning("Twilio package not installed, falling back to simulation.")
                self._twilio_client = False
        return self._twilio_client or None

    # -- Méthode principale d'envoi --
    def send_sms(self, to_phone: str, message: str, sender: str | None = None) -> dict:
        """Envoie un SMS. En dev: simule + log. En prod: appelle Twilio/Africa's Talking.

        Retourne: {success: bool, reference: str, error: str|None, simulated: bool}
        """
        normalized = normalize_phone_number(to_phone)
        if not normalized:
            return {"success": False, "error": "Numéro invalide", "simulated": False, "reference": None}

        if self.live_enabled and self.twilio_client:
            try:
                msg = self.twilio_client.messages.create(
                    body=message,
                    from_=TWILIO_PHONE_NUMBER or sender or self.sender,
                    to=f"+{normalized}",
                )
                return {
                    "success": True,
                    "reference": msg.sid,
                    "error": None,
                    "simulated": False,
                }
            except Exception as e:
                logger.error("Twilio SMS error for %s: %s", normalized, e)
                return {"success": False, "error": str(e), "simulated": False, "reference": None}

        # Mode simulation
        ref = f"SIM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{normalized[-6:]}"
        logger.info(
            "[SMS SIMULATED] to=%s length=%d reference=%s\nMessage: %s",
            format_phone_display(normalized), len(message), ref, message,
        )
        return {
            "success": True,
            "reference": ref,
            "error": None,
            "simulated": True,
        }

    def send_whatsapp_via_link(self, to_phone: str, message: str) -> dict:
        """Ne 'envoie' pas techniquement, mais génère le lien wa.me et le logue."""
        link = build_whatsapp_link(to_phone, message)
        normalized = normalize_phone_number(to_phone)
        ref = f"WALINK-{normalized}-{datetime.utcnow().strftime('%H%M%S')}" if normalized else None
        logger.info(
            "[WHATSAPP LINK] %s -> %s\nMessage preview: %s",
            format_phone_display(to_phone), link, message[:80] + ("..." if len(message) > 80 else ""),
        )
        return {
            "success": bool(link),
            "reference": ref,
            "whatsapp_link": link,
            "error": None if link else "Numéro invalide",
            "simulated": True,
        }

    def send_broadcast_recipient(self, recipient: EventSmsRecipient, message: str) -> EventSmsRecipient:
        """Envoie un message à un destinataire unique et met à jour son statut."""
        now = datetime.utcnow()
        phone = recipient.phone_number
        try:
            if recipient.channel == "whatsapp":
                result = self.send_whatsapp_via_link(phone, message)
            else:
                result = self.send_sms(phone, message)

            if result.get("success"):
                recipient.status = "sent"
                recipient.provider_reference = result.get("reference")
                recipient.sent_at = now
            else:
                recipient.status = "failed"
                recipient.error_message = result.get("error") or "Échec inconnu"
        except Exception as e:
            logger.exception("Erreur envoi pour %s: %s", phone, e)
            recipient.status = "failed"
            recipient.error_message = str(e)
        return recipient


sms_service = SmsService()
