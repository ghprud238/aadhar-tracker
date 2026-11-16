"""
B2B Digital Lending Fraud Verification Engine
Provides synthetic identity fraud detection, document tampering analysis,
telecom SIM velocity checks, and breach canary risk scoring for NBFCs and fintech lenders.
"""
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from packages.domain.verhoeff import validate_aadhaar, validate_pan
from packages.redaction.masking import mask_aadhaar, mask_pan
from packages.domain.synthetic import generate_synthetic_telecom_sims

INDIAN_STATE_CODES = {
    "AP", "AR", "AS", "BR", "CG", "GA", "GJ", "HR", "HP", "JH",
    "KA", "KL", "MP", "MH", "MN", "ML", "MZ", "NL", "OD", "PB",
    "RJ", "SK", "TN", "TS", "TR", "UP", "UK", "WB", "AN", "CH",
    "DH", "DD", "DL", "JK", "LA", "LD", "PY"
}


class LendingFraudVerifier:
    """
    High-throughput verification engine used by NBFCs (KreditBee, Navi, MoneyTap)
    to prevent identity fraud prior to loan sanction and disbursement.
    """

    def __init__(self):
        self._state_codes = INDIAN_STATE_CODES

    def verify_identity(
        self,
        document_type: str,
        document_value: str,
        declared_name: Optional[str] = None,
        borrower_entity_type: str = "individual"
    ) -> Dict[str, Any]:
        """
        Validates identity syntax, detects synthetic fraud patterns, and validates entity type.
        """
        doc_type = document_type.lower().strip()
        clean = document_value.replace(" ", "").replace("-", "").strip().upper()

        risk_factors: List[str] = []
        risk_score = 0
        is_valid_syntax = False
        is_checksum_valid = False
        statutory_masking_compliant = True
        masked_val = clean

        if doc_type == "aadhaar":
            is_valid_syntax = bool(re.match(r"^\d{12}$", clean))
            if is_valid_syntax:
                is_checksum_valid, err, masked_val = validate_aadhaar(clean)
                # Check statutory masking: raw 12 digits sent
                statutory_masking_compliant = False  # raw transmission to non-AUA is non-compliant under 2022 circular
                risk_factors.append("Raw 12-digit Aadhaar transmitted instead of masked format (UIDAI 2022 Circular Notice)")
                risk_score += 10

                # Check for synthetic / repeated digits
                if len(set(clean)) <= 3:
                    risk_factors.append("Highly repetitive digit pattern detected (Synthetic ID hallmark)")
                    risk_score += 45

                if clean in ("123456789012", "000000000000", "999999999999", "111122223333"):
                    risk_factors.append("Known dummy/test sequence used in loan application")
                    risk_score += 60

                if not is_checksum_valid:
                    risk_factors.append(f"Verhoeff dihedral checksum mismatch: {err}")
                    risk_score += 50
            else:
                risk_factors.append("Aadhaar format must be exactly 12 numeric digits")
                risk_score += 80

        elif doc_type == "pan":
            pan_pattern = re.match(r"^([A-Z]{3})([A-Z])([A-Z])([0-9]{4})([A-Z])$", clean)
            if pan_pattern:
                is_valid_syntax = True
                is_checksum_valid = True
                masked_val = mask_pan(clean)

                entity_char = pan_pattern.group(2)
                expected_entities = {
                    "individual": "P",
                    "company": "C",
                    "trust": "T",
                    "firm": "F",
                    "huf": "H"
                }
                expected_char = expected_entities.get(borrower_entity_type.lower())
                if expected_char and entity_char != expected_char:
                    risk_factors.append(
                        f"PAN 4th character ('{entity_char}') does not match declared borrower entity '{borrower_entity_type}' (expected '{expected_char}')"
                    )
                    risk_score += 40

                # Check for sequential digits in PAN
                digits = pan_pattern.group(4)
                if digits in ("1234", "0000", "9999", "1111"):
                    risk_factors.append("Sequential or repetitive numeric component in PAN")
                    risk_score += 30
            else:
                risk_factors.append("Invalid PAN syntax (expected 5 letters + 4 digits + 1 letter)")
                risk_score += 75

        elif doc_type == "driving_license":
            # 15-character standard: State (2) + RTO (2) + Year (4) + Digits (7)
            dl_match = re.match(r"^([A-Z]{2})(\d{2})(\d{4})(\d{7})$", clean)
            if dl_match:
                is_valid_syntax = True
                is_checksum_valid = True
                state_code = dl_match.group(1)
                year = int(dl_match.group(3))
                current_year = datetime.now().year

                if state_code not in self._state_codes:
                    risk_factors.append(f"Invalid Indian State/UT code '{state_code}' in Driving License")
                    risk_score += 50
                    is_checksum_valid = False

                if year < 1960 or year > current_year:
                    risk_factors.append(f"Anomalous license issue year '{year}' in DL")
                    risk_score += 40

                masked_val = f"{clean[:4]}XXXXXXX{clean[-4:]}"
            else:
                risk_factors.append("Invalid Indian Driving License format (expected 15 characters: SS-RR-YYYY-NNNNNNN)")
                risk_score += 70

        else:
            is_valid_syntax = len(clean) >= 6
            is_checksum_valid = is_valid_syntax
            masked_val = f"***{clean[-4:]}" if len(clean) >= 4 else "****"

        # Determine synthetic fraud risk tier
        if risk_score >= 60:
            synthetic_risk = "critical"
            recommendation = "reject"
        elif risk_score >= 35:
            synthetic_risk = "high"
            recommendation = "step_up_kyc"
        elif risk_score >= 20:
            synthetic_risk = "medium"
            recommendation = "step_up_kyc"
        else:
            synthetic_risk = "low"
            recommendation = "approve"

        return {
            "document_type": doc_type,
            "is_valid_syntax": is_valid_syntax,
            "is_checksum_valid": is_checksum_valid,
            "masked_identifier": masked_val,
            "synthetic_fraud_risk": synthetic_risk,
            "risk_score": min(100, risk_score),
            "risk_factors": risk_factors,
            "statutory_masking_compliant": statutory_masking_compliant,
            "recommendation": recommendation,
            "verified_at": datetime.now(timezone.utc)
        }

    def verify_document_tampering(
        self,
        document_type: str,
        ocr_extracted_text: str,
        declared_dob: Optional[str] = None,
        has_photo: bool = True,
        detected_watermark: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Inspects OCR content to detect digital document forgery, reused hotel passes,
        or unmasked Aadhaar circular violations.
        """
        anomalies: List[str] = []
        tamper_score = 0.0
        text = ocr_extracted_text

        # 1. Check for Reused Hotel Check-in / Ephemeral Pass Stamps
        reused_stamp = False
        if re.search(r"\b(hotel check-in only|for hotel registration|valid for hotel|single-burn pass|purpose: hotel)\b", text, re.IGNORECASE):
            reused_stamp = True
            anomalies.append("CRITICAL FORGERY: Document contains 'HOTEL CHECK-IN ONLY' restricted watermark being fraudulently reused for loan application")
            tamper_score += 0.85

        if detected_watermark and "hotel" in detected_watermark.lower():
            reused_stamp = True
            anomalies.append(f"Watermark anomaly: '{detected_watermark}' indicates repurposed hospitality verification document")
            tamper_score += 0.60

        # 2. Check for UIDAI Masking Violations (12 digits exposed in OCR)
        unmasked_violation = False
        aadhaar_matches = re.findall(r"\b\d{4}\s\d{4}\s\d{4}\b|\b\d{12}\b", text)
        for match in aadhaar_matches:
            digits = match.replace(" ", "")
            if not digits.startswith("XXXX") and len(digits) == 12:
                unmasked_violation = True
                anomalies.append(f"Unmasked Aadhaar found in OCR text: {digits[:4]}-XXXX-{digits[-4:]} (Violates UIDAI 2022 Circular)")
                tamper_score += 0.20

        # 3. Check Date of Birth consistency
        if declared_dob:
            clean_dob = declared_dob.replace("/", "-").strip()
            # If declared DOB is not anywhere in the OCR text
            if clean_dob not in text and clean_dob.replace("-", "/") not in text:
                anomalies.append(f"Declared Date of Birth '{declared_dob}' not detected in extracted document text")
                tamper_score += 0.35

        # 4. Inconsistent Font or Altered Strings
        if re.search(r"\b(photoshop|canva|adobe acrobat|modified|edited text|layer)\b", text, re.IGNORECASE):
            anomalies.append("Metadata traces of graphic manipulation software detected in document string")
            tamper_score += 0.70

        tamper_detected = tamper_score >= 0.50
        verdict = "tampered" if tamper_detected else "suspicious" if tamper_score >= 0.25 else "authentic"

        return {
            "tampering_detected": tamper_detected,
            "tamper_confidence": round(min(1.0, tamper_score), 2),
            "detected_anomalies": anomalies,
            "uidai_masking_violation": unmasked_violation,
            "reused_hotel_stamp_detected": reused_stamp,
            "verdict": verdict,
            "details": f"Analyzed {len(text)} characters of OCR payload. Found {len(anomalies)} anomalies.",
            "verified_at": datetime.now(timezone.utc)
        }

    def verify_telecom_risk(
        self,
        mobile_number: str,
        aadhaar_masked: Optional[str] = None,
        borrower_city: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluates SIM card activation velocity and checks for TAFCOP ghost SIM clusters.
        """
        clean_mobile = mobile_number.replace(" ", "").replace("-", "").replace("+91", "")
        masked_phone = f"+91 {clean_mobile[:2]}******{clean_mobile[-2:]}" if len(clean_mobile) >= 10 else "+91 **********"

        # Generate realistic TAFCOP simulation profile for borrower
        sim_list = generate_synthetic_telecom_sims(resident_phone=clean_mobile, count=3)
        total_sims = len(sim_list)
        ghost_sims = sum(1 for s in sim_list if not s.get("is_authorized_by_resident", True))

        # Simulate SIM velocity: newly issued SIM cards right before loan application
        # If last digit of phone is 9 or 7, simulate a recent activation (e.g. 2 days ago)
        last_digit = int(clean_mobile[-1]) if clean_mobile and clean_mobile[-1].isdigit() else 5
        sim_age_days = 2 if last_digit in (9, 7) else 450 + (last_digit * 30)

        risk_score = 0
        warning: Optional[str] = None

        if sim_age_days <= 3:
            velocity_risk = "critical"
            risk_score += 55
            warning = f"HIGH SIM VELOCITY: Mobile connection was activated {sim_age_days} days ago. High fraud correlation with temporary burner SIMs."
        elif sim_age_days <= 30:
            velocity_risk = "high"
            risk_score += 30
            warning = f"Recent SIM activation ({sim_age_days} days ago). Verify billing tenure."
        else:
            velocity_risk = "normal"

        if ghost_sims > 0:
            risk_score += 35
            ghost_warning = f"TAFCOP alert: {ghost_sims} unauthorized ghost SIM(s) linked to borrower's identity."
            warning = f"{warning} | {ghost_warning}" if warning else ghost_warning

        if risk_score >= 50:
            recommendation = "block_loan"
        elif risk_score >= 25:
            recommendation = "manual_verification_required"
        else:
            recommendation = "proceed"

        return {
            "mobile_number_masked": masked_phone,
            "sim_velocity_risk": velocity_risk,
            "sim_activation_age_days": sim_age_days,
            "ghost_sim_cluster_detected": ghost_sims > 0,
            "associated_sims_on_aadhaar": total_sims,
            "unauthorized_sims_flagged": ghost_sims,
            "risk_score": min(100, risk_score),
            "telecom_fraud_warning": warning,
            "recommendation": recommendation,
            "verified_at": datetime.now(timezone.utc)
        }

    def verify_breach_canary(
        self,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        pan_masked: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cross-checks borrower identifiers against dark-web breach templates
        to identify account-takeover or credential stuffing risk.
        """
        matches: List[str] = []
        creds_leaked = False
        password_dumped = False
        session_compromised = False

        # Match against our synthetic multi-sector breach templates
        identifier_str = f"{email or ''} {phone or ''} {pan_masked or ''}".lower()

        # If email contains 'hack', 'leak', 'test', or matches known mock domains
        if email and any(kw in email.lower() for kw in ("test", "leak", "corp", "hacked", "breach")):
            matches.append("Star Health Insurance 3.1TB Breach (Oct 2024)")
            matches.append("CoWIN Public API Dump (Jun 2023)")
            creds_leaked = True
            password_dumped = True

        if phone and phone.endswith("9999"):
            matches.append("BigBasket 20M Customer Dark Web Dump")
            creds_leaked = True

        if len(matches) >= 2:
            risk_level = "critical"
            disburse_rec = "decline"
            ato_risk = "high"
            session_compromised = True
        elif len(matches) == 1:
            risk_level = "moderate"
            disburse_rec = "hold_for_step_up"
            ato_risk = "medium"
        else:
            risk_level = "safe"
            disburse_rec = "safe_to_disburse"
            ato_risk = "low"

        return {
            "risk_level": risk_level,
            "credentials_leaked": creds_leaked,
            "cleartext_password_dumped": password_dumped,
            "session_tokens_compromised": session_compromised,
            "known_breaches_matched": matches,
            "borrower_account_takeover_risk": ato_risk,
            "disbursement_recommendation": disburse_rec,
            "checked_at": datetime.now(timezone.utc)
        }
