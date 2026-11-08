"""
Sanitization utilities to process untrusted provider content and strip sensitive secrets.
"""
import re
import bleach

ALLOWED_TAGS = ["b", "i", "strong", "em", "p", "br", "ul", "ol", "li", "code"]
ALLOWED_ATTRIBUTES = {}

SENSITIVE_PATTERNS = [
    re.compile(r"(?i)(?:password|passwd|pwd)\s*[:=]\s*([^\s,;]+)"),
    re.compile(r"(?i)(?:session_id|sessionid|connect\.sid)\s*[:=]\s*([^\s,;]+)"),
    re.compile(r"(?i)(?:otp|one[- ]?time[- ]?password)\s*[:=]\s*(\d{6})"),
    re.compile(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b"),  # Aadhaar 12-digit number pattern
]


def sanitize_provider_html(raw_html: str | None) -> str:
    """Sanitize provider HTML, completely stripping scripts, styles, objects, and unsafe links."""
    if not raw_html:
        return ""
    # Strip script and style blocks completely including inner contents
    no_scripts = re.sub(r"(?is)<script.*?>.*?</script>", "", raw_html)
    no_styles = re.sub(r"(?is)<style.*?>.*?</style>", "", no_scripts)
    cleaned = bleach.clean(
        no_styles,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )
    return cleaned.strip()


def sanitize_to_plain_text(raw_html: str | None) -> str:
    """Strip all HTML tags to produce safe, plain text."""
    if not raw_html:
        return ""
    text_only = bleach.clean(raw_html, tags=[], strip=True)
    # Collapse multiple whitespace
    return re.sub(r"\s+", " ", text_only).strip()


def redact_sensitive_secrets(text: str | None) -> str:
    """Scan and redact leaked credentials, session cookies, and 12-digit numbers."""
    if not text:
        return ""
    result = text
    # Mask passwords
    result = re.sub(r"(?i)(password|passwd|pwd)(\s*[:=]\s*)([^\s,;]+)", r"\1\2[REDACTED_PASSWORD]", result)
    # Mask session tokens
    result = re.sub(r"(?i)(session_id|sessionid|bearer|token)(\s*[:=]\s*)([^\s,;]+)", r"\1\2[REDACTED_TOKEN]", result)
    # Mask Aadhaar numbers
    result = re.sub(r"\b(\d{4})[ -]?(\d{4})[ -]?(\d{4})\b", r"XXXX-XXXX-\3", result)
    # Mask OTPs
    result = re.sub(r"(?i)(otp\s*[:=]?\s*)(\d{4,6})", r"\1[REDACTED_OTP]", result)
    return result
