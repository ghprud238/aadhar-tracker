"""
Verhoeff checksum algorithm and India identity (Aadhaar & PAN) format validation.
UIDAI officially utilizes the Verhoeff dihedral D5 group algorithm for 12-digit Aadhaar numbers.
"""
import re
from typing import Dict, List, Optional, Tuple

# Verhoeff algorithm multiplication table (d)
_VERHOEFF_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]

# Verhoeff algorithm permutation table (p)
_VERHOEFF_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]

# Verhoeff algorithm inverse table (inv)
_VERHOEFF_INV = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]

# Official PAN regex pattern: 5 uppercase letters, 4 digits, 1 uppercase letter
_PAN_REGEX = re.compile(r"\b([A-Z]{5}[0-9]{4}[A-Z]{1})\b")

# Aadhaar extraction regex pattern (matches 12 digits with optional spaces or hyphens)
_AADHAAR_REGEX = re.compile(r"\b([2-9][0-9]{3}[-\s]?[0-9]{4}[-\s]?[0-9]{4})\b")


def validate_verhoeff(num_str: str) -> bool:
    """
    Validates a number string using the Verhoeff checksum algorithm.
    Returns True if the check digit is valid (c == 0).
    """
    clean_digits = "".join(filter(str.isdigit, num_str))
    if not clean_digits:
        return False

    c = 0
    reversed_digits = clean_digits[::-1]
    for i, char in enumerate(reversed_digits):
        val = int(char)
        c = _VERHOEFF_D[c][_VERHOEFF_P[i % 8][val]]
    return c == 0


def generate_verhoeff_checksum(num_str: str) -> str:
    """
    Generates the Verhoeff check digit for an 11-digit or N-digit prefix.
    """
    clean_digits = "".join(filter(str.isdigit, num_str))
    c = 0
    reversed_digits = clean_digits[::-1]
    for i, char in enumerate(reversed_digits):
        val = int(char)
        c = _VERHOEFF_D[c][_VERHOEFF_P[(i + 1) % 8][val]]
    return str(_VERHOEFF_INV[c])


def validate_aadhaar(aadhaar_raw: str) -> Tuple[bool, str, str]:
    """
    Validates an Aadhaar number according to UIDAI structural rules:
    1. Exactly 12 digits.
    2. Does not start with 0 or 1.
    3. Satisfies the Verhoeff checksum algorithm.

    Returns:
        (is_valid: bool, error_message: str, masked_aadhaar: str)
    """
    clean = "".join(filter(str.isdigit, aadhaar_raw))
    if len(clean) != 12:
        return False, f"Aadhaar must be exactly 12 digits (found {len(clean)})", ""

    if clean[0] in ("0", "1"):
        return False, "Aadhaar number cannot start with 0 or 1", ""

    if not validate_verhoeff(clean):
        return False, "Invalid Aadhaar number (Verhoeff checksum verification failed)", ""

    masked = f"XXXX-XXXX-{clean[-4:]}"
    return True, "", masked


def validate_pan(pan_raw: str) -> Tuple[bool, str, str]:
    """
    Validates a Permanent Account Number (PAN) format:
    1. Exactly 10 characters: 5 uppercase letters, 4 digits, 1 uppercase letter.
    2. Fourth character indicates taxpayer status (P=Individual, C=Company, etc.).

    Returns:
        (is_valid: bool, error_message: str, masked_pan: str)
    """
    clean = pan_raw.strip().upper()
    if len(clean) != 10:
        return False, f"PAN must be exactly 10 characters (found {len(clean)})", ""

    if not _PAN_REGEX.match(clean):
        return False, "Invalid PAN format. Standard format is 5 letters, 4 digits, 1 letter (e.g. ABCDE1234F)", ""

    masked = f"{clean[:2]}***{clean[5:7]}*{clean[-1]}"
    return True, "", masked


def detect_identifiers_in_text(text: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Deep scan inspection of unencrypted text (e.g. WhatsApp message, email draft, chat logs)
    to detect unmasked Aadhaar or PAN numbers.

    Returns detected findings with masked representation, type, and start/end positions.
    """
    findings: Dict[str, List[Dict[str, str]]] = {
        "aadhaar": [],
        "pan": [],
    }

    if not text:
        return findings

    # 1. Search for potential Aadhaar numbers
    for match in _AADHAAR_REGEX.finditer(text):
        raw_val = match.group(1)
        is_valid, _, masked = validate_aadhaar(raw_val)
        if is_valid:
            findings["aadhaar"].append({
                "raw_match": raw_val,
                "masked": masked,
                "start": str(match.start()),
                "end": str(match.end()),
                "alert": "Unmasked Aadhaar number detected"
            })

    # 2. Search for potential PAN numbers
    for match in _PAN_REGEX.finditer(text.upper()):
        raw_val = match.group(1)
        is_valid, _, masked = validate_pan(raw_val)
        if is_valid:
            findings["pan"].append({
                "raw_match": raw_val,
                "masked": masked,
                "start": str(match.start()),
                "end": str(match.end()),
                "alert": "Unmasked PAN number detected"
            })

    return findings


# Pre-computed valid UIDAI test sandbox Aadhaar numbers for developer testing
CANARY_TEST_PRESETS = [
    {
        "id": "aadhaar_sandbox_1",
        "type": "aadhaar",
        "label": "UIDAI Sandbox Test Identity #1 (Standard)",
        "identifier": "9999 4105 7058",
        "masked": "XXXX-XXXX-7058",
        "description": "Standard UIDAI dummy resident with biometric auth enabled"
    },
    {
        "id": "aadhaar_sandbox_2",
        "type": "aadhaar",
        "label": "UIDAI Sandbox Test Identity #2 (Dark Web Leak)",
        "identifier": "9999 0000 0016",
        "masked": "XXXX-XXXX-0016",
        "description": "UIDAI test identity with simulated dark-web forum dump exposure"
    },
    {
        "id": "aadhaar_sandbox_3",
        "type": "aadhaar",
        "label": "UIDAI Sandbox Test Identity #3 (WhatsApp Sharing)",
        "identifier": "2345 6789 0124",
        "masked": "XXXX-XXXX-0124",
        "description": "Test resident with simulated unmasked WhatsApp chat forward"
    },
    {
        "id": "aadhaar_sandbox_4",
        "type": "aadhaar",
        "label": "UIDAI Sandbox Test Identity #4 (Infostealer Log)",
        "identifier": "5432 1098 7652",
        "masked": "XXXX-XXXX-7652",
        "description": "Test resident with compromised browser auto-fill credentials"
    },
    {
        "id": "pan_sandbox_1",
        "type": "pan",
        "label": "Income Tax Test PAN #1 (Banking Leak)",
        "identifier": "ABCDE1234F",
        "masked": "AB***12*F",
        "description": "Test individual PAN for financial breach simulation"
    },
    {
        "id": "pan_sandbox_2",
        "type": "pan",
        "label": "Income Tax Test PAN #2 (Credit Card Dump)",
        "identifier": "XYZPK9876M",
        "masked": "XY***98*M",
        "description": "Test salaried taxpayer PAN for dark web credit card dump test"
    }
]
