# Data Classification & Retention Policy

## 1. Data Classification

- **Public / Unclassified**: Public landing page text, published processing notices, plan descriptions, official UIDAI / ITD educational guides.
- **Restricted Internal**: Masked identifiers (`u***@example.com`), user profile preferences, incident summaries, audit logs.
- **Confidential / PII**: Encrypted identifier values (AES-256-GCM envelope encryption), user emails, support correspondence.
- **Strictly Prohibited Material**: Leaked plaintext passwords, decrypted session cookies, raw biometrics, Aadhaar OTPs, unredacted third-party PII. (Automatically filtered and rejected upon provider ingestion).

---

## 2. Retention Schedules

| Data Category | Proposed Retention Schedule | Deletion Trigger / Mechanism |
| :--- | :--- | :--- |
| **Verification Challenges** | 10 minutes | Expired automatically; digest deleted immediately upon completion or expiry |
| **Active Findings & Incidents** | Lifetime of account | Periodic minimization; deleted upon account deletion |
| **Redacted Excerpts / Evidence** | 30 days max (or provider limit) | Purged by automated background privacy job |
| **Generated User Exports** | 24 hours | Short-lived signed download token; purged afterwards |
| **Account Active Data** | Lifetime of active account | 8-step deletion workflow initiated upon user request |
| **Backups** | 35-day rolling snapshot | Overwritten by lifecycle policy; tombstoned prior to restore serving |
| **Payment Records** | Statutory retention (e.g. 7 years) | Legal compliance requirement; isolated from active identity graph |
| **Audit Events** | 180 days standard security retention | Immutable append-only log |
