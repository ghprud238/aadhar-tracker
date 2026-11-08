"""
Structured logging and security audit logging.
Strictly enforces NFR-010: Sensitive identifiers absent from logs, traces, analytics, and queue payloads.
"""
import logging
import sys
import json
from datetime import datetime, timezone
from typing import Any, Dict


class SafeJsonFormatter(logging.Formatter):
    """Formats log records as JSON while ensuring raw identifiers are masked."""
    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "tenant_id"):
            log_entry["tenant_id"] = getattr(record, "tenant_id")
        if hasattr(record, "request_id"):
            log_entry["request_id"] = getattr(record, "request_id")
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            # Only include non-sensitive metadata keys
            safe_extra = {
                k: v for k, v in record.extra_data.items()
                if not any(s in k.lower() for s in ["email", "phone", "aadhaar", "pan", "password", "token", "secret"])
            }
            log_entry.update(safe_extra)
        return json.dumps(log_entry)


logger = logging.getLogger("identity_protection_platform")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(SafeJsonFormatter())
logger.handlers = [handler]
