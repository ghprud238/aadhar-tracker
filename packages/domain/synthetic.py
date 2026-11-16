"""
Re-exports synthetic data generator utilities from dummy_data_to_test.generator.
Maintains backward compatibility across packages and tests while providing
the full multi-document, scam, QR, and breach synthetic dataset suite.
"""
from dummy_data_to_test.generator import (
    generate_synthetic_aadhaar,
    generate_synthetic_pan,
    generate_synthetic_vid,
    generate_synthetic_driving_license,
    generate_synthetic_voter_id,
    generate_synthetic_passport,
    generate_synthetic_bank_account,
    generate_synthetic_vehicle_rc,
    generate_synthetic_telecom_sims,
    generate_synthetic_credit_profile,
    generate_synthetic_resident_profile,
    generate_synthetic_breach_dump,
    generate_synthetic_whatsapp_conversations,
    generate_synthetic_scam_corpus,
    generate_synthetic_qr_pass_corpus,
    generate_complete_test_fixture_bundle,
    BREACH_TEMPLATES,
    FIRST_NAMES,
    LAST_NAMES,
    CITIES_AND_STATES,
    INDIAN_BANKS,
)

__all__ = [
    "generate_synthetic_aadhaar",
    "generate_synthetic_pan",
    "generate_synthetic_vid",
    "generate_synthetic_driving_license",
    "generate_synthetic_voter_id",
    "generate_synthetic_passport",
    "generate_synthetic_bank_account",
    "generate_synthetic_vehicle_rc",
    "generate_synthetic_telecom_sims",
    "generate_synthetic_credit_profile",
    "generate_synthetic_resident_profile",
    "generate_synthetic_breach_dump",
    "generate_synthetic_whatsapp_conversations",
    "generate_synthetic_scam_corpus",
    "generate_synthetic_qr_pass_corpus",
    "generate_complete_test_fixture_bundle",
    "BREACH_TEMPLATES",
    "FIRST_NAMES",
    "LAST_NAMES",
    "CITIES_AND_STATES",
    "INDIAN_BANKS",
]
