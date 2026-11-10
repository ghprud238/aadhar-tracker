"""
Synthetic test data generator package for Indian Identity Protection Platform (Suraksha).
Provides utilities to create valid synthetic Aadhaar, PAN, VID, resident profiles,
dark-web breach catalog dumps, and WhatsApp DLP samples.
"""
from dummy_data_to_test.generator import (
    generate_synthetic_aadhaar,
    generate_synthetic_pan,
    generate_synthetic_vid,
    generate_synthetic_resident_profile,
    generate_synthetic_breach_dump,
    generate_synthetic_whatsapp_conversations,
    generate_complete_test_fixture_bundle,
    BREACH_TEMPLATES,
)

__all__ = [
    "generate_synthetic_aadhaar",
    "generate_synthetic_pan",
    "generate_synthetic_vid",
    "generate_synthetic_resident_profile",
    "generate_synthetic_breach_dump",
    "generate_synthetic_whatsapp_conversations",
    "generate_complete_test_fixture_bundle",
    "BREACH_TEMPLATES",
]
