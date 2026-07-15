"""
Service d'intégration MoMo (Mobile Money).
Gère les appels API, les webhooks et les confirmations de paiement.
"""
import os
import requests
import json
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class MoMoPaymentService:
    """Service pour gérer les paiements MoMo."""
    
    # Configuration MoMo API
    BASE_URL = os.getenv("MOMO_API_URL", "https://api.sandbox.mtn.co.rw/collection/v1_0")
    PRIMARY_KEY = os.getenv("MOMO_PRIMARY_KEY", "")
    SECONDARY_KEY = os.getenv("MOMO_SECONDARY_KEY", "")
    ACCOUNT_HOLDER = os.getenv("MOMO_ACCOUNT_HOLDER", "CHERE")
    
    # Subscription/API Key info
    SUBSCRIPTION_KEY = os.getenv("MOMO_SUBSCRIPTION_KEY", "")
    TARGET_ENVIRONMENT = os.getenv("MOMO_TARGET_ENVIRONMENT", "sandbox")  # sandbox | production
    
    HEADERS = {
        "Content-Type": "application/json",
        "X-Reference-Id": None,  # Will be set per request
        "X-Target-Environment": TARGET_ENVIRONMENT
    }

    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """
        Valide un numéro de téléphone Rwanda (MoMo).
        Formats acceptés: 250XXXXXXXXX, 07XXXXXXXX, 06XXXXXXXX
        """
        import re
        pattern = r'^(250|\\+250)?\s*7\d{8}$|^(250|\\+250)?\s*6\d{8}$|^07\d{8}$|^06\d{8}$'
        return bool(re.match(pattern, phone.replace(" ", "")))

    @staticmethod
    def normalize_phone_number(phone: str) -> str:
        """
        Normalise un numéro de téléphone au format MoMo: 250XXXXXXXXX
        """
        # Remove all spaces and special characters
        phone = phone.replace(" ", "").replace("-", "").replace("+", "")
        
        # If starts with 0, replace with 250
        if phone.startswith("0"):
            phone = "250" + phone[1:]
        
        # If doesn't start with 250, add it
        if not phone.startswith("250"):
            phone = "250" + phone
        
        return phone

    def request_to_pay(
        self,
        amount: float,
        phone_number: str,
        external_id: str,
        payer_message: str = "Paiement événement CHERE",
        payee_note: str = "Inscription événement"
    ) -> Dict:
        """
        Initie une demande de paiement MoMo.
        
        Args:
            amount: Montant en RWF
            phone_number: Numéro MoMo du payeur
            external_id: ID unique de la transaction (ex: txn_12345)
            payer_message: Message pour le payeur
            payee_note: Note interne
        
        Returns:
            Dict avec status, reference_id et message
        """
        try:
            # Valider le numéro
            if not self.validate_phone_number(phone_number):
                return {
                    "success": False,
                    "error": "Numéro de téléphone invalide",
                    "phone_format": "Format requis: 250xxxxxxxxx ou 07xxxxxxxx"
                }

            phone_number = self.normalize_phone_number(phone_number)
            
            # Générer une référence unique
            import uuid
            reference_id = str(uuid.uuid4())
            
            # Construire la requête
            url = f"{self.BASE_URL}/requesttopay"
            headers = self.HEADERS.copy()
            headers["X-Reference-Id"] = reference_id
            headers["Authorization"] = f"Bearer {self.PRIMARY_KEY}"
            headers["Ocp-Apim-Subscription-Key"] = self.SUBSCRIPTION_KEY
            
            payload = {
                "amount": str(amount),
                "currency": "RWF",
                "externalId": external_id,
                "payee": {
                    "partyIdType": "MSISDN",
                    "partyId": phone_number
                },
                "payer": {
                    "partyIdType": "MSISDN",
                    "partyId": phone_number
                },
                "payerMessage": payer_message,
                "payeeNote": payee_note
            }
            
            logger.info(f"MoMo Request to Pay - Amount: {amount} RWF, Phone: {phone_number}")
            
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code in [200, 202]:
                return {
                    "success": True,
                    "reference_id": reference_id,
                    "external_id": external_id,
                    "message": "Demande de paiement initiée. Vérifiez votre téléphone."
                }
            else:
                logger.error(f"MoMo API Error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": "Erreur lors de la demande de paiement",
                    "details": response.text if response.text else "Pas de détails"
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"MoMo Request Exception: {str(e)}")
            return {
                "success": False,
                "error": "Impossible de contacter le service MoMo",
                "details": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error in request_to_pay: {str(e)}")
            return {
                "success": False,
                "error": "Erreur interne du serveur",
                "details": str(e)
            }

    def get_transaction_status(self, reference_id: str) -> Dict:
        """
        Vérifie le statut d'une transaction MoMo.
        
        Args:
            reference_id: ID de référence MoMo
        
        Returns:
            Dict avec status et détails
        """
        try:
            url = f"{self.BASE_URL}/requesttopay/{reference_id}"
            headers = self.HEADERS.copy()
            headers["Authorization"] = f"Bearer {self.PRIMARY_KEY}"
            headers["Ocp-Apim-Subscription-Key"] = self.SUBSCRIPTION_KEY
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "status": data.get("status"),  # PENDING, SUCCESSFUL, FAILED
                    "data": data
                }
            else:
                logger.error(f"MoMo Status Check Error: {response.status_code}")
                return {
                    "success": False,
                    "error": "Impossible de vérifier le statut"
                }
                
        except Exception as e:
            logger.error(f"Error checking transaction status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def handle_payment_callback(self, callback_data: Dict) -> Dict:
        """
        Gère les callbacks webhook de MoMo.
        
        Args:
            callback_data: Données du webhook MoMo
        
        Returns:
            Dict avec réponse de confirmation
        """
        try:
            reference_id = callback_data.get("referenceId")
            status = callback_data.get("status")  # SUCCESSFUL, FAILED, etc.
            
            logger.info(f"MoMo Callback - Reference: {reference_id}, Status: {status}")
            
            # Vous implémenterez la logique métier ici
            # (mise à jour de la transaction, confirmation de l'inscription, etc.)
            
            return {
                "success": True,
                "message": "Callback reçu et traité"
            }
            
        except Exception as e:
            logger.error(f"Error handling MoMo callback: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


# Instance singleton
momo_service = MoMoPaymentService()
