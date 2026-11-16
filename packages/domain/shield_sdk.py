"""
Suraksha Shield Backend Python SDK
Client library for Bank Core Banking Systems (CBS), Payment Gateways, and NBFC microservices.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from packages.domain.verhoeff import validate_aadhaar, validate_pan
from packages.redaction.masking import mask_aadhaar, mask_pan
from packages.domain.scam_radar import ScamRadarEngine
from packages.domain.schemas import ScamAnalysisDTO


class SurakshaShieldBackendSDK:
    """
    Enterprise Fraud Prevention & Identity Protection SDK for Server-Side Banking Systems.
    """

    def __init__(self, api_key: str, tenant_id: str, bank_identifier: str = "GENERIC_BANK"):
        self.api_key = api_key
        self.tenant_id = tenant_id
        self.bank_identifier = bank_identifier
        self._calls_count = 0

    def evaluate_transaction_message(self, message_text: str, sender_header: str = "") -> ScamAnalysisDTO:
        """
        Scans SMS, WhatsApp, or customer communication text for Digital Arrest or APK trojans.
        """
        self._calls_count += 1
        return ScamRadarEngine.analyze_message(message_text, sender_header=sender_header)

    def validate_kyc_document(self, doc_type: str, raw_value: str) -> Dict[str, Any]:
        """
        Validates mathematical integrity and returns safe zero-plaintext masked identifiers.
        """
        self._calls_count += 1
        clean = raw_value.replace(" ", "").replace("-", "").strip().upper()

        if doc_type.lower() == "aadhaar":
            is_valid, err_msg, masked = validate_aadhaar(clean)
            return {
                "document_type": "aadhaar",
                "is_valid": is_valid,
                "masked_identifier": masked if is_valid else mask_aadhaar(clean),
                "validation_error": err_msg if not is_valid else None,
                "verified_at": datetime.now(timezone.utc).isoformat()
            }

        if doc_type.lower() == "pan":
            is_valid, err_msg, masked = validate_pan(clean)
            entity_types = {
                "P": "Individual Resident",
                "C": "Company",
                "H": "HUF",
                "F": "Partnership / LLP",
                "T": "Trust",
                "G": "Government Entity"
            }
            entity_code = clean[3] if len(clean) >= 4 else "?"
            return {
                "document_type": "pan",
                "is_valid": is_valid,
                "entity_type": entity_types.get(entity_code, "Other Entity"),
                "masked_identifier": masked if is_valid else mask_pan(clean),
                "validation_error": err_msg if not is_valid else None,
                "verified_at": datetime.now(timezone.utc).isoformat()
            }

        return {
            "document_type": doc_type,
            "is_valid": len(clean) >= 5,
            "masked_identifier": f"***{clean[-4:]}" if len(clean) >= 4 else "****",
            "validation_error": None,
            "verified_at": datetime.now(timezone.utc).isoformat()
        }

    def get_sdk_status(self) -> Dict[str, Any]:
        return {
            "bank_identifier": self.bank_identifier,
            "tenant_id": self.tenant_id,
            "calls_evaluated": self._calls_count,
            "status": "active",
            "sdk_version": "1.0.0"
        }
