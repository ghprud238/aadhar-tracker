# Identity Protection Platform — Product Requirements Document

**Version:** 1.0 | **Date:** 8 November 2026
**Document Status:** Implementation specification
**Original Authoritative PDF:** [`identity_protection_completion_PRD.pdf`](identity_protection_completion_PRD.pdf)

---

## 1. Executive Summary & Objective

The Identity Protection Platform is a launch-oriented, privacy-first identity protection platform with a Python backend, verified-identity monitoring, breach intelligence, licensed dark-web monitoring, actionable alerts, and an India-specific Aadhaar/PAN protective assistance layer.

### Core Promise
Monitor verified identities against supported sources, explain detected exposures, and guide users through protective actions.

### Non-Promises
- No complete visibility into all corners of the dark web.
- No detection of every single compromised credential in existence.
- No universal tracking of Aadhaar or PAN usage across financial or government institutions.
- No proof that a leaked password is still valid.
- No removal of information from hostile underground infrastructure.
- No government affiliation or unsanctioned access.
- "No matches" never means "safe" — it means no matches were found in supported sources.

---

## 2. Terminology & Core Invariants

- **Tenant**: Security and billing boundary (one personal workspace per consumer account at initial launch).
- **Subject**: The person whose information is being monitored.
- **Identifier**: Monitoring target (e.g., email address).
- **Verification**: Evidence of control over an identifier (e.g. single-use token sent to email).
- **Authorization**: Permission and lawful basis to monitor the identifier.
- **Source Record**: Provider-origin record describing an observation.
- **Finding**: Normalized exposure associated with an authorized subject.
- **Incident**: User-facing grouping of related findings.
- **Alert**: Privacy-safe notification generated from an incident or meaningful update.
- **Evidence**: Minimized, permitted context supporting a finding (redacted excerpts).
- **Coverage**: The enabled source capabilities applicable to an identifier.
- **Freshness**: How recently a source was successfully checked.
- **Remediation**: Protective action and user-reported completion state.

**Core Invariant**: Verification, authorization, consent, subscription entitlement, and provider eligibility are separate checks. Passing one does not automatically satisfy the others.

---

## 3. Requirements Catalog

### Functional Requirements (P0 / P1)
- `FR-001`: Authenticate through managed OIDC identity provider (PKCE authorization-code flow).
- `FR-002`: Create one personal workspace per account.
- `FR-003`: Enforce ownership and tenant boundary on every resource access.
- `FR-004`: Store versioned processing notices.
- `FR-005`: Record granular consent grants and withdrawals with version tracking.
- `FR-006`: Add an email without immediately querying intelligence providers.
- `FR-007`: Verify email control before initiating any monitoring.
- `FR-008`: Prevent public identifier enumeration.
- `FR-009`: Run asynchronous initial scans upon verified authorization.
- `FR-010`: Display source-specific scan results and transparent coverage status.
- `FR-011`: Distinguish "no matches found" from "failed/delayed check".
- `FR-012`: Normalize provider records into vendor-neutral findings.
- `FR-013`: Deduplicate repeated observations and provider re-indexes.
- `FR-014`: Group findings into actionable user incidents.
- `FR-015`: Show explainable, independent severity and confidence dimensions.
- `FR-016`: Generate actionable remediation checklists.
- `FR-017`: Send privacy-safe email and in-app alerts (no raw credentials in emails).
- `FR-018`: Support pause, resume, and withdrawal of monitoring.
- `FR-019`: Support GDPR/DPDP data export and multi-step account deletion.
- `FR-020`: Show connector health and coverage limitations.
- `FR-021`: Provide metadata-only, time-limited support access.
- `FR-022`: Maintain immutable security audit records.
- `FR-023`: Support provider feature flags, rate-limits, and circuit breakers.
- `FR-024`: Support subscription lifecycle, webhook signing, and reconciliation.
- `FR-025`: Provide Aadhaar/PAN assistance without unsupported government claims.
- `FR-026`: Support user disputes and false-match review.

### Non-Functional Requirements
- `NFR-001`: Monthly application availability target: 99.9%.
- `NFR-002`: Ordinary authenticated reads: p95 under 500 ms.
- `NFR-003`: Durable scan submission: p95 under 1 second.
- `NFR-004`: Newly accepted high-severity findings enter alert queue within 60 seconds.
- `NFR-008`: Zero known cross-tenant access defects at release.
- `NFR-009`: Zero critical or high exploitable security findings at release.
- `NFR-010`: Sensitive identifiers absent from logs, traces, analytics, and queue payloads.
- `NFR-012`: Provider outages do not break authentication, consent withdrawal, or deletion.
- `NFR-013`: No production fallback to mock intelligence.
- `NFR-014`: No background monitoring after authorization becomes invalid.
- `NFR-015`: Every user-facing risk decision is attributable to a rules version.
