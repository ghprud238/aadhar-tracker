# Master End-to-End Dataflows: User ➔ Backend ➔ User

This document specifies the complete end-to-end technical dataflow and state machine transitions across all micro-modular subsystems of the Suraksha platform.

---

## 1. Complete System Architecture Dataflow

```mermaid
flowchart TD
    subgraph ClientLayer["1. Client Tier (User Interaction)"]
        WebPWA["Web PWA (Desktop/Mobile)<br/>Hindi & English i18n • Service Worker"]
        MobileApp["Cross-Platform Mobile App<br/>React Native • Expo 51 • Biometric Lock"]
        Wearable["Smartwatch Companion<br/>Wear OS • watchOS • 360x360 AMOLED"]
        WhatsAppUser["WhatsApp User / Group<br/>Direct Messages & Forwarded Chats"]
    end

    subgraph GatewayLayer["2. Ingress & Security Gateway"]
        ReverseProxy["Cloud Reverse Proxy / TLS 1.3"]
        FastAPIBFF["FastAPI Gateway & BFF (Port 8000)"]
        RateLimitMW["Sliding-Window Rate Limiter<br/>(5 OTP attempts / 15 mins)"]
        IdempotencyMW["Idempotency Key Middleware<br/>(X-Idempotent-Replay Protection)"]
        SessionMW["Same-Origin BFF Session Guard<br/>(HttpOnly SameSite=Strict Cookies)"]
    end

    subgraph ValidationVault["3. Validation & Cryptographic Vault"]
        VerhoeffEngine["Verhoeff Dihedral D5 Checksum Engine<br/>packages/domain/verhoeff.py"]
        PANValidator["PAN Syntax & Taxpayer Code Validator"]
        EnvelopeVault["AES-256-GCM Envelope Encryption Vault<br/>(DEK encrypted under master KEK)"]
        BlindIndexer["HMAC-SHA256 Blind Indexer<br/>(Tenant-scoped exact searchability)"]
    end

    subgraph CoreDomain["4. Core Engine & Providers"]
        OutboxDispatcher["Transactional Outbox Dispatcher<br/>(Durable lease tokens & DLQ)"]
        ConnectorWorker["Connector Worker<br/>(Scheduled & On-demand CTI Sweeps)"]
        CircuitBreaker["Provider Circuit Breakers<br/>(CLOSED ⇄ OPEN ⇄ HALF_OPEN)"]
        ScoringEngine["Risk Scoring Matrix<br/>(Severity, Confidence, Freshness, Coverage)"]
        PrivacyWorker["Privacy Worker (DPDP Act)<br/>(JSON Data Export & Multi-step Erasure)"]
    end

    subgraph StorageLayer["5. Persistence & Observability Tier"]
        PostgresRLS[("PostgreSQL 16 (Row-Level Security)<br/>Strict tenant_user_id boundary isolation")]
        RedisStore[("Redis 7<br/>Lease tokens • Rate quotas • In-flight keys")]
        PrometheusMetrics["Prometheus Exporter (/metrics)"]
        KubernetesProbes["Kubernetes Probes (/livez, /readyz)"]
    end

    subgraph ExternalFeeds["6. External Threat Intelligence"]
        FlareAPI["Flare Systems API<br/>(Stealer logs, dark web forums, Telegram)"]
        HIBPAPI["HaveIBeenPwned API<br/>(Corporate & telecom database breaches)"]
    end

    subgraph NotificationLayer["7. Real-Time Alert Dispatch"]
        WhatsAppDispatch["Automated WhatsApp Advisory<br/>(Meta Cloud API Webhook)"]
        PushDispatch["Mobile Push Notification Service<br/>(FCM & APNs via Expo)"]
        WearableHaptics["Smartwatch Haptic Alert & Glance API<br/>(/companion/glance)"]
    end

    ClientLayer --> ReverseProxy
    ReverseProxy --> FastAPIBFF
    FastAPIBFF --> RateLimitMW --> IdempotencyMW --> SessionMW

    SessionMW --> VerhoeffEngine & PANValidator
    VerhoeffEngine & PANValidator --> EnvelopeVault --> BlindIndexer

    SessionMW --> ScoringEngine
    SessionMW --> OutboxDispatcher

    OutboxDispatcher --> PostgresRLS
    OutboxDispatcher --> ConnectorWorker & PrivacyWorker
    ConnectorWorker --> CircuitBreaker
    CircuitBreaker --> ExternalFeeds

    FastAPIBFF --> PostgresRLS
    FastAPIBFF --> RedisStore
    FastAPIBFF --> PrometheusMetrics & KubernetesProbes

    OutboxDispatcher --> NotificationLayer
    NotificationLayer --> ClientLayer
```

---

## 2. State Machine: Identity & Incident Lifecycle

### A. Identifier Verification Lifecycle (`FR-007`)
```
[Unverified / Draft]
         │
         ▼  (User requests verification)
[Verification Pending]  ──(5 attempts exceeded)──>  [Verification Locked]
         │
         ▼  (Correct 6-digit challenge token submitted)
[Verified & Active]
         │
         ├─────────────────────────────────────────┐
         ▼ (User pauses monitoring)                 ▼ (Consent withdrawn)
   [Monitoring Paused]                     [Withdrawn & Purged]
```

### B. Incident Severity & Resolution Lifecycle (`FR-014`, `FR-016`)
```
[External Observation Ingested]
         │
         ▼  (Deduplication against grouping_key)
    [New Incident]  ──(Priority 80-100: Critical / High)
         │
         ├─────────────────────────────────────────┐
         ▼ (User views & acknowledges)              ▼ (User disputes match)
  [In Progress]                             [Dispute Under Review]
         │                                         │
         ▼ (All remediation tasks checked)         ▼ (Verified false-positive)
   [Remediated]                               [Dismissed]
```

---

## 3. Storage Invariants & Security Matrix

| Data Element | In-Flight Protection | At-Rest Protection | Display Rules | Retention Policy |
| :--- | :--- | :--- | :--- | :--- |
| **12-Digit Aadhaar** | TLS 1.3 / In-Memory only | **AES-256-GCM Envelope** + HMAC Blind Index | **Masked Only** (`XXXX-XXXX-1234`) | Erased upon account deletion or consent revocation |
| **10-Character PAN** | TLS 1.3 / In-Memory only | **AES-256-GCM Envelope** + HMAC Blind Index | **Masked Only** (`AB***12*F`) | Erased upon account deletion or consent revocation |
| **Plaintext Passwords** | **Never stored** | **Discarded immediately** | `credential_material_present=True` | Never written to database |
| **Session Cookies / Tokens** | HttpOnly SameSite=Strict | Server-side Redis session store | Never exposed to client JS | 24-hour rolling expiry |
| **Audit Logs** | Immutable Append-Only | PostgreSQL write-only table | Operator metadata view only | 180-day retention per CERT-In directive |
