"""
Service d'intégration MoMo (Mobile Money) — MTN Rwanda Collections API.
"""
import os
import re
import uuid
import requests
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class MoMoPaymentService:

    @property
    def base_url(self) -> str:
        return os.getenv("MOMO_API_URL", "https://api.sandbox.mtn.co.rw/collection/v1_0")

    @property
    def token_url(self) -> str:
        # Token endpoint is one level up from the collection resource
        base = os.getenv("MOMO_API_URL", "https://api.sandbox.mtn.co.rw/collection/v1_0")
        return base.replace("/v1_0", "") + "/token/"

    @property
    def api_user(self) -> str:
        return os.getenv("MOMO_PRIMARY_KEY", "")

    @property
    def api_key(self) -> str:
        return os.getenv("MOMO_SECONDARY_KEY", "")

    @property
    def subscription_key(self) -> str:
        return os.getenv("MOMO_SUBSCRIPTION_KEY", "")

    @property
    def target_environment(self) -> str:
        return os.getenv("MOMO_TARGET_ENVIRONMENT", "sandbox")

    @property
    def merchant_number(self) -> str:
        """Your MoMo merchant/payee number that receives the money."""
        return os.getenv("MOMO_MERCHANT_NUMBER", "")

    # ------------------------------------------------------------------
    # OAuth2 token
    # ------------------------------------------------------------------

    def get_access_token(self) -> str:
        """
        Fetches a Bearer access token using Basic Auth (API User + API Key).
        Returns the token string or raises on failure.
        """
        response = requests.post(
            self.token_url,
            auth=(self.api_user, self.api_key),
            headers={
                "Ocp-Apim-Subscription-Key": self.subscription_key,
            },
            timeout=15,
        )
        response.raise_for_status()
        return response.json()["access_token"]

    # ------------------------------------------------------------------
    # Phone helpers
    # ------------------------------------------------------------------

    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """
        Validates a Rwanda MoMo number.
        Accepted formats: 250XXXXXXXXX, +250XXXXXXXXX, 07XXXXXXXX, 06XXXXXXXX
        """
        cleaned = phone.replace(" ", "").replace("-", "")
        pattern = r'^(\+?250)?[76]\d{8}$|^0[76]\d{8}$'
        return bool(re.match(pattern, cleaned))

    @staticmethod
    def normalize_phone_number(phone: str) -> str:
        """Normalises to 250XXXXXXXXX format required by MoMo API."""
        phone = phone.replace(" ", "").replace("-", "").replace("+", "")
        if phone.startswith("0"):
            phone = "250" + phone[1:]
        if not phone.startswith("250"):
            phone = "250" + phone
        return phone

    # ------------------------------------------------------------------
    # Collections
    # ------------------------------------------------------------------

    def request_to_pay(
        self,
        amount: float,
        phone_number: str,
        external_id: str,
        payer_message: str = "Paiement événement CHERE",
        payee_note: str = "Inscription événement",
    ) -> Dict:
        """
        Initiates a Request-to-Pay (debit push) to the customer's wallet.

        - payer  = customer phone (money leaves their wallet)
        - payee  = merchant number (money arrives here)
        """
        if not self.validate_phone_number(phone_number):
            return {
                "success": False,
                "error": "Numéro de téléphone invalide",
                "phone_format": "Format requis: 250xxxxxxxxx ou 07xxxxxxxx",
            }

        phone_number = self.normalize_phone_number(phone_number)
        reference_id = str(uuid.uuid4())

        try:
            token = self.get_access_token()
        except Exception as e:
            logger.error(f"MoMo token error: {e}")
            return {"success": False, "error": "Impossible d'obtenir le token MoMo", "details": str(e)}

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "X-Reference-Id": reference_id,
            "X-Target-Environment": self.target_environment,
            "Ocp-Apim-Subscription-Key": self.subscription_key,
        }

        payload = {
            "amount": str(int(amount)),   # MoMo expects integer string for RWF
            "currency": "RWF",
            "externalId": external_id,
            "payer": {                    # who is PAYING (customer)
                "partyIdType": "MSISDN",
                "partyId": phone_number,
            },
            "payerMessage": payer_message,
            "payeeNote": payee_note,
        }

        # Only add payee if a merchant number is configured
        if self.merchant_number:
            payload["payee"] = {
                "partyIdType": "MSISDN",
                "partyId": self.normalize_phone_number(self.merchant_number),
            }

        try:
            logger.info(f"MoMo RequestToPay — {amount} RWF from {phone_number}")
            response = requests.post(
                f"{self.base_url}/requesttopay",
                json=payload,
                headers=headers,
                timeout=30,
            )

            if response.status_code in (200, 202):
                return {
                    "success": True,
                    "reference_id": reference_id,
                    "external_id": external_id,
                    "message": "Demande de paiement initiée. Vérifiez votre téléphone.",
                }

            logger.error(f"MoMo API {response.status_code}: {response.text}")
            return {
                "success": False,
                "error": "Erreur lors de la demande de paiement",
                "details": response.text or "Pas de détails",
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"MoMo request exception: {e}")
            return {"success": False, "error": "Impossible de contacter le service MoMo", "details": str(e)}

    def get_transaction_status(self, reference_id: str) -> Dict:
        """Checks the status of a RequestToPay transaction."""
        try:
            token = self.get_access_token()
        except Exception as e:
            return {"success": False, "error": "Impossible d'obtenir le token MoMo", "details": str(e)}

        headers = {
            "Authorization": f"Bearer {token}",
            "X-Target-Environment": self.target_environment,
            "Ocp-Apim-Subscription-Key": self.subscription_key,
        }

        try:
            response = requests.get(
                f"{self.base_url}/requesttopay/{reference_id}",
                headers=headers,
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "status": data.get("status"),  # PENDING | SUCCESSFUL | FAILED
                    "data": data,
                }

            logger.error(f"MoMo status check {response.status_code}")
            return {"success": False, "error": "Impossible de vérifier le statut"}

        except Exception as e:
            logger.error(f"MoMo status exception: {e}")
            return {"success": False, "error": str(e)}

    def handle_payment_callback(self, callback_data: Dict) -> Dict:
        """Handles incoming MoMo webhook callbacks."""
        reference_id = callback_data.get("referenceId")
        status = callback_data.get("status")
        logger.info(f"MoMo Callback — ref: {reference_id}, status: {status}")
        return {"success": True, "message": "Callback reçu et traité"}


# Singleton
momo_service = MoMoPaymentService()
