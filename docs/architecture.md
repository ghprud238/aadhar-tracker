# Technical Architecture Specification

## 1. High-Level Architecture Overview

The system is constructed as a **modular monolith** for core API handling, paired with isolated background workers for tasks requiring privilege separation, specialized scaling, or asynchronous execution:

- **BFF / Web App**: Same-origin session cookies, PKCE OIDC login, secure HttpOnly tokens. Never exposes provider credentials or bearer tokens to browser local storage.
- **FastAPI Core Business API**: Scoped business operations, validation schemas, ownership enforcement, audit logging.
- **PostgreSQL Database with RLS**: Source of truth with Row-Level Security (`RLS`) enforcing tenant and subject boundary defense-in-depth. Transaction-local variables `app.current_tenant_id` and `app.current_subject_id`.
- **Transactional Outbox**: Business mutations and event intents persist in the same ACID transaction.
- **Connector Worker**: Scheduled and on-demand scanner executing against approved provider APIs (HIBP, Flare) with strict rate-limiting, blind-index lookups, and result normalization.
- **Notification Worker**: Dispatches privacy-safe email and in-app alerts with idempotency keys.
- **Privacy Worker**: Handles GDPR/DPDP export downloads, redactions, and multi-stage account deletions.

---

## 2. Component Boundaries and Privileges

| Component | Allowed Privileges | Forbidden Privileges |
| :--- | :--- | :--- |
| **Web / BFF** | Session operations, business API proxying | Intelligence provider API keys, DB direct access |
| **Business API** | Tenant-scoped CRUD, audit event recording | Raw provider secret keys, arbitrary evidence access |
| **Connector Worker** | Approved provider calls, scoped identifier decryption | Billing mutations, direct user session modification |
| **Notification Worker** | Template rendering, masked alert dispatch | Full raw provider payloads or decrypted credentials |
| **Privacy Worker** | Export assembly, cryptographic deletion sweeps | External internet scanning or provider querying |
| **Support Console** | Read-only metadata for user-approved tickets | Raw identifiers, leaked passwords, payment secrets |

---

## 3. Transactional Outbox & Queue Pattern

```
BEGIN TRANSACTION;
  INSERT/UPDATE business_table (e.g. incident, identifier);
  INSERT INTO outbox_events (event_id, event_type, tenant_id, subject_id, resource_id, payload);
COMMIT;
```

A resilient outbox dispatcher polls committed unhandled events, publishes them to the worker queue, and marks them processed. Workers maintain idempotency tables (`processed_events`) with leasing and fencing tokens.
