"""
Re-exports synthetic data generator utilities from dummy_data_to_test.generator.
Maintains backward compatibility across packages and tests.
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
    FIRST_NAMES,
    LAST_NAMES,
    CITIES_AND_STATES,
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
    "FIRST_NAMES",
    "LAST_NAMES",
    "CITIES_AND_STATES",
]
