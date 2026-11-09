# Identity Protection Platform (Aadhaar & Identity Tracker)

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests Passing](https://img.shields.io/badge/tests-34%2F34%20passing-brightgreen.svg)](tests/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Security Zero-Plaintext](https://img.shields.io/badge/security-Zero--Plaintext%20Credentials-success.svg)](docs/threat-model.md)

Production-grade, consent-first identity protection platform with verified email exposure monitoring, breach intelligence, licensed dark-web monitoring capabilities, actionable alerts, and India-specific Aadhaar/PAN protective assistance.

---

## Key Principles & Guardrails

1. **Consent-First & Verified Identifiers**: No external intelligence provider is ever queried for an unverified or unauthorized identifier.
2. **PostgreSQL RLS Defense-in-Depth**: Multi-tenant isolation enforced at application level and database row-level security.
3. **Strict Credential & PII Minimization**: Never stores plaintext passwords, session cookies, auth tokens, raw biometrics, or Aadhaar OTPs. Never scrapes government portals.
4. **India-Specific Protection Guidance**: Official Aadhaar/PAN protective workflows (UIDAI biometric lock guide, virtual ID generation, official auth history checking, user-reported concerns) with clear distinctions between official guidance and verified provider feeds.
5. **Transactional Outbox & Idempotent Asynchronous Processing**: Background workers communicate via a durable transactional outbox and strict lease/fencing tokens.

---

## Repository Structure

```
.
├── AGENTS.md                  # Project rules & non-negotiable invariants
├── docs/                      # PRD, Architecture, Threat Model, Policies & Runbooks
│   ├── prd.md
│   ├── architecture.md
│   ├── threat-model.md
│   ├── data-classification.md
│   ├── retention-policy.md
│   ├── provider-capabilities.md
│   ├── test-plan.md
│   ├── traceability.md
│   ├── decisions/             # Architecture Decision Records (ADR-001 to ADR-015)
│   └── runbooks/              # Operational runbooks (outage, key rotation, deletion, etc.)
├── contracts/                 # OpenAPI specification and Event Schemas
│   ├── openapi.yaml
│   ├── events/
│   └── provider-fixtures/
├── packages/                  # Reusable domain, adapters, security, and redaction logic
│   ├── domain/                # Entities, states, scoring, and normalization models
│   ├── provider_adapters/     # HIBP & Flare connectors with capability registries
│   ├── security/              # Cryptographic envelope vault, blind indexing, and sessions
│   ├── redaction/             # Masking and PII sanitization filters
│   └── observability/         # Audit events, metrics, and structured logging
├── services/                  # Micro-modular services and background workers
│   ├── api/                   # FastAPI Business API + BFF session endpoints
│   ├── connector_worker/      # Scheduled & on-demand provider scanning worker
│   ├── notification_worker/   # Privacy-safe alert dispatcher
│   └── privacy_worker/        # Account deletion & data export lifecycle worker
├── apps/
│   ├── web/                   # Responsive web app + PWA with accessible UI & Hindi i18n
│   ├── mobile/                # React Native / Expo cross-platform mobile app (iOS & Android)
│   └── wearable/              # Smartwatch companion client (Wear OS Tile & watchOS Glance)
├── tests/                     # Unit, property, integration, contract, security, and E2E tests
└── infrastructure/            # Docker compose & configuration
```

---

## Client Applications

The platform provides unified multi-surface clients connected to the core engine:

| Client Surface | Technology Stack | Features | Access / Run Command |
| :--- | :--- | :--- | :--- |
| **Web Client** | Modern Vanilla JS + PWA Service Worker + CSS Tokens | 10 PRD views, English/Hindi i18n, offline caching, accessible high-contrast navigation | Served at `http://localhost:8000/` |
| **Mobile Client** | React Native 0.74 + Expo 51 + TypeScript | Bottom tab navigation, Face ID/Fingerprint app lock, step-up elevation, scan trigger, dispute modal | `cd apps/mobile && npx expo start` |
| **Wearable Client** | Smartwatch 360x360 AMOLED UI + Haptic Feedback | 1-second Shield Glance dial, urgent breach card with haptic buzz, 1-tap "Lock Biometrics" quick action, AOD ambient mode | Served at `http://localhost:8000/wearable` |

---

## Quickstart

### Prerequisites
- Python 3.11+
- `uv` package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Node.js 18+ (tested on Node v24.15)

### Setup & Installation
```bash
# Clone and enter the repository
cd /Users/dpcubed/projects/aadhar-tracker

# Install virtualenv and all dependencies
uv sync

# Run the test suite (34 tests passing 100%)
uv run pytest -v
```

### Running the API & Client Frontends
```bash
# Start the FastAPI server (serves API, Web App, and Wearable Simulator)
uv run uvicorn services.api.main:app --host 0.0.0.0 --port 8000 --reload
```
Once running:
- **Web App:** Open `http://localhost:8000/` in any browser or install as a PWA on mobile.
- **Wearable Client:** Open `http://localhost:8000/wearable` to interact with the 360x360 smartwatch companion and simulate Wear OS/watchOS tiles.
- **API Documentation:** Interactive OpenAPI Swagger UI is available at `http://localhost:8000/docs`.

### Running the Mobile Client (Expo)
```bash
cd apps/mobile
npm install
npx expo start
```
From the Expo terminal, press `i` to open the iOS simulator, `a` for Android emulator, or `w` for Web.

