# Provider Capabilities & Contract Registry

## 1. Registry Architecture

Each external connector maintains an explicit capability manifest describing verified API capabilities, contract approval status, and display policy constraints.

```json
{
  "provider": "hibp",
  "environment": "production",
  "contract_status": "approved",
  "capabilities": {
    "email_breach_lookup": true,
    "email_darkweb_mentions": false,
    "phone_lookup": false,
    "domain_monitoring": false,
    "pan_lookup": false,
    "aadhaar_lookup": false,
    "persistent_identifier_registration": false,
    "provider_deletion": false
  },
  "display_policy": {
    "allow_raw_secrets": false,
    "allow_full_documents": false,
    "allow_redacted_excerpt": false
  }
}
```

```json
{
  "provider": "flare",
  "environment": "production",
  "contract_status": "approved",
  "capabilities": {
    "email_breach_lookup": true,
    "email_darkweb_mentions": true,
    "phone_lookup": false,
    "domain_monitoring": false,
    "pan_lookup": false,
    "aadhaar_lookup": false,
    "persistent_identifier_registration": true,
    "provider_deletion": true
  },
  "display_policy": {
    "allow_raw_secrets": false,
    "allow_full_documents": false,
    "allow_redacted_excerpt": true
  }
}
```

---

## 2. Invariants
- If a connector is disabled via kill switch (`/internal/connectors/{id}/disable`), all scheduled and queued scans against that provider must gracefully skip with status `contract_disabled` or `unavailable`.
- Connectors never fall back silently to an unapproved provider.
