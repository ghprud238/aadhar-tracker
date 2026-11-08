# Requirements Traceability Matrix

| Requirement ID | Module / Service | Test IDs | Test Level | Expected Result |
| :--- | :--- | :--- | :--- | :--- |
| **FR-001** (OIDC Auth) | `services/api/routes/auth.py` | `AUTH-001` | Integration / Unit | Session created via PKCE authorization-code flow; HttpOnly cookie set |
| **FR-002** (Personal Workspace) | `services/api/routes/account.py` | `E2E-001` | E2E | Idempotently creates exactly one personal workspace per account |
| **FR-003** (Ownership Enforcement) | `packages/security/authorization.py` | `AZ-001`–`AZ-004` | Security | Access to another tenant/subject resource denied with 404 without disclosure |
| **FR-004** (Versioned Notices) | `services/api/routes/consents.py` | `CON-002` | Unit / Integration | Processing notices stored with immutable version strings |
| **FR-005** (Granular Consent) | `services/api/routes/consents.py` | `CON-004` | Integration | Explicit grant and withdrawal; withdrawal increments authorization version |
| **FR-006** (Add Identifier without Query) | `services/api/routes/identifiers.py` | `ID-001` | Integration | Identifier stored in `pending_verification`; zero external provider queries |
| **FR-007** (Verify Email Before Scan) | `services/api/routes/identifiers.py` | `ID-002` | Integration | One-time challenge token verification transitions identifier to `active` |
| **FR-009** (Asynchronous Initial Scans) | `services/api/routes/monitoring.py` | `E2E-001` | E2E | Scan queued in transactional outbox with 202 Accepted; executed by worker |
| **FR-010** (Coverage Transparency) | `services/api/routes/monitoring.py` | `E2E-003` | API | Transparent matrix showing per-source health, limits, and delays |
| **FR-011** (Distinguish No Match vs Failure) | `packages/provider_adapters/hibp.py` | `HIBP-002` | Contract | 404 from HIBP mapped to `no_match`, not connector failure |
| **FR-012** (Normalize Observations) | `packages/domain/models.py` | `HIBP-001`, `LIC-001` | Contract | Provider records normalized to standard schema contract |
| **FR-013** (Deduplication) | `services/connector_worker/worker.py` | `INC-002` | Integration | Observation and finding deduplication prevents duplicate incidents |
| **FR-014** (Group Findings into Incidents) | `services/connector_worker/worker.py` | `E2E-001` | E2E | Normalized observations grouped by incident grouping key |
| **FR-015** (Explainable Severity) | `packages/domain/scoring.py` | Unit | Unit | Deterministic severity, confidence, and 0-100 priority score with rule versioning |
| **FR-016** (Actionable Remediation) | `services/api/routes/incidents.py` | `E2E-004` | E2E | Protection checklist with `user_reported` provenance |
| **FR-017** (Privacy-Safe Alerts) | `services/notification_worker/worker.py` | Unit | Integration | Alerts contain masked identifiers only; zero leaked passwords or cookies |
| **FR-018** (Pause / Resume Monitoring) | `services/api/routes/identifiers.py` | `E2E-005` | E2E | Pausing stops monitoring without deleting historical records |
| **FR-019** (Export & Deletion Lifecycle) | `services/api/routes/privacy.py` | `E2E-008`, `E2E-011`| E2E | Step-up protected export download and 8-stage account erasure workflow |
| **FR-024** (Subscription Reconciliation) | `services/api/routes/billing.py` | `BILL-001`, `BILL-003`| Unit | Server-side pricing calculation, HMAC signature validation, deduplication |
| **FR-025** (Aadhaar & PAN Guidance) | `services/api/routes/identity_assistance.py`| `E2E-012` | E2E | UIDAI official guidance and user-reported suspicious activity without scraping |
| **FR-026** (False-Match Disputes) | `services/api/routes/incidents.py` | Unit | API | User dispute workflow halts re-alerting with auditable review |
