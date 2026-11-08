# Comprehensive Test Plan

## Test Strategy & Execution Architecture

As mandated by Section 12 ("Comprehensive Test Program") of the PRD:

1. **Unit Testing**:
   - `packages/security/crypto.py`: AES-256-GCM envelope encryption, blind indexing, verification challenge hashing, constant-time comparison.
   - `packages/redaction/`: Masking utilities, HTML sanitization via bleach, secret redaction filter.
   - `packages/domain/scoring.py`: Severity, confidence, and bounded priority score calculations.
   - `services/api/routes/billing.py`: Pricing enforcement, webhook signature verification, and deduplication.

2. **Property-Based Testing (Hypothesis)**:
   - Invariants: Masked email format invariant, envelope encryption roundtrip invariant, regex redaction invariant never exposing plaintext passwords.

3. **Database & Integration Testing**:
   - Verification challenge issuance and completion lifecycle (`ID-001`, `ID-002`).
   - Consent withdrawal race condition and immediate query cancellation (`CON-001`, `CON-004`).

4. **Security & Isolation Testing**:
   - Multi-tenant boundary checks (`AZ-001` through `AZ-020`): Cross-tenant reading, scanning, export, and deletion attempts must fail closed with 404 without disclosure.
   - Step-up authentication enforcement (`AUTH-014`).
   - XSS sanitization in untrusted breach descriptions and user inputs (`SEC-003`, `SEC-004`).

5. **Provider Contract Testing**:
   - Have I Been Pwned (`HIBP-001` through `HIBP-015`): Test account matching, 404 handling, HTML sanitization, attribution.
   - Flare Systems (`LIC-001` through `LIC-016`): Bearer token caching, refresh locking, darkweb event ingestion, and deletion receipts.

6. **End-to-End User Journeys**:
   - `E2E-001`: Complete onboarding -> consent -> email verification -> asynchronous scan -> incident detection -> remediation checklist.
   - `E2E-012`: Aadhaar resident guidance -> official portal links -> user confirmation logging.

### Execution Command
```bash
uv run pytest -v
```
