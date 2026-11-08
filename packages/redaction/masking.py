"""
Masking utilities for privacy-safe display of sensitive identifiers.
Never logs or renders full sensitive values on standard interfaces.
"""
import re


def mask_email(email: str) -> str:
    """Mask email as u***@example.com according to PRD specification."""
    if not email or "@" not in email:
        return "***"
    local, domain = email.strip().split("@", 1)
    if len(local) <= 1:
        masked_local = f"{local}***"
    else:
        masked_local = f"{local[0]}***"
    return f"{masked_local}@{domain.lower()}"


def mask_phone(phone: str) -> str:
    """Mask phone keeping only last 4 digits."""
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) < 4:
        return "****"
    return f"******{digits[-4:]}"


def mask_aadhaar(aadhaar: str) -> str:
    """Mask Aadhaar keeping only last 4 digits: XXXX-XXXX-1234."""
    digits = re.sub(r"\D", "", aadhaar or "")
    if len(digits) < 4:
        return "XXXX-XXXX-XXXX"
    return f"XXXX-XXXX-{digits[-4:]}"


def mask_pan(pan: str) -> str:
    """Mask PAN keeping only last 4 chars: XXXXX1234X."""
    clean = (pan or "").strip().upper()
    if len(clean) != 10:
        return "XXXXXXXXXX"
    return f"XXXXX{clean[5:]}"
