# Threat Model & Security Controls

## 1. Threats and Mitigations Matrix

| Threat | Risk Level | Primary Technical Mitigation |
| :--- | :--- | :--- |
| **Checking Another Person's Identifier** | High | Email control verification challenge before any provider lookup (`FR-007`). Rate limits on verification tokens. |
| **Cross-Tenant Unauthorized Access** | Critical | Strict application-layer ownership checks + PostgreSQL Row-Level Security (`RLS`) + composite foreign keys. |
| **Credential / Password Disclosure** | Critical | Zero plaintext password or session token retention. Hash-only comparison for leaked range checks. Redaction pipelines. |
| **Malicious Provider HTML / XSS** | High | Sanitization with Bleach, script stripping, iframe prevention, plain-text fallback rendering. |
| **SSRF via Provider Connectors** | High | Fixed, configuration-controlled provider hostnames (`haveibeenpwned.com`, `api.flare.io`). No user-supplied URLs. |
| **Notification Flooding & Harassment** | Medium | Deduplication of incidents, suppression on routine re-indexes, rate-limiting on outbound alerts. |
| **Forged Payment Webhooks** | High | Raw-body HMAC SHA256 signature verification, replay protection with unique event IDs, authoritative state reconciliation. |
| **Reprocessing After Consent Revocation** | High | Monotonically incrementing authorization version. Pre-query and pre-persist checks against live DB state. |
| **Insider Access / Operator Misuse** | High | Bounded, time-limited, user-approved support grants (`support_access_grants`). Detailed audit log sink. |
| **Aadhaar / PAN Credential Scraping** | Critical | Explicitly prohibited by policy and code architecture. No endpoints accept full Aadhaar or government passwords. |
