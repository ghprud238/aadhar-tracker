# Production Launch Acceptance Checklist

Reference: PRD Page 75-76.

## 1. Product Readiness
- [x] Core onboarding works (OIDC PKCE flow, session establishment).
- [x] Identifier verification works (single-use token digest, 10-minute expiry).
- [x] Initial monitoring works (asynchronous scan via transactional outbox).
- [x] Partial coverage is correctly displayed (Coverage Transparency Matrix).
- [x] Incident explanations are understandable (independent severity and confidence).
- [x] Remediation wording is accurate (`user_reported` provenance).
- [x] Cancellation and deletion are accessible (self-service DPDP center).
- [x] Unsupported features are not advertised (no scraping, no universal dark-web claim).

## 2. Provider Readiness
- [x] Provider capability registry implemented with contractual constraints (`ADR-013`).
- [x] HIBP contract tests passing (including k-anonymity SHA-1 prefixing & rate limit backoff).
- [x] Flare reference connector implemented (anti-stampede token lock, cursor pagination).
- [x] Deletion receipt workflows distinguish `requested` from `confirmed`.
- [x] Operator kill-switch endpoints implemented (`POST /internal/connectors/{id}/disable`).

## 3. Security Readiness
- [x] Threat model reviewed and documented (`docs/threat-model.md`).
- [x] Tenant-isolation evidence verified (`AZ-001`, `AZ-002`, `AZ-003`).
- [x] Sensitive values absent from traces, logs, and queue payloads (`NFR-010`).
- [x] Step-up authentication enforced for high-privilege operations.
- [x] Stored XSS and provider HTML injection prevented via bleach and script stripping.

## 4. Privacy Readiness
- [x] Published processing notice v1.0 seeded and version-bound (`FR-004`).
- [x] Consent withdrawal immediately invalidates leases and increments authorization version (`CON-004`).
- [x] 8-stage account erasure workflow verified (`PRI-009`–`PRI-012`).
- [x] Short-lived, authorized data export downloads tested.
- [x] Aadhaar & PAN guidance strictly separated from automated scraping.

## 5. Operational Readiness
- [x] Transactional outbox with idempotent worker execution verified.
- [x] Process liveness and readiness health checks implemented.
- [x] Operational runbooks created (`docs/runbooks/`).
- [x] Metrics telemetry registry tracking operational and security events.
