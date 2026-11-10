# Dummy Data to Test (`dummy_data_to_test`)

This directory houses the synthetic data generation engine, database seeder, and pre-exported test fixtures for the **Suraksha Identity Protection Platform**.

All data produced by this suite uses **mathematically valid algorithm generators** (such as the official UIDAI Verhoeff Dihedral $D_5$ algorithm over the reserved `9999...` developer test prefix) and synthetic personas. **Zero real resident PII is ever used.**

---

## 📁 Directory Contents

| File | Purpose |
| :--- | :--- |
| [`generator.py`](file:///Users/dpcubed/projects/aadhar-tracker/dummy_data_to_test/generator.py) | Core generator module producing valid Aadhaar, PAN, VID, resident profiles, breach dumps, and WhatsApp DLP samples. |
| [`seed_db.py`](file:///Users/dpcubed/projects/aadhar-tracker/dummy_data_to_test/seed_db.py) | CLI utility to export test fixtures and seed the local SQLite (`suraksha.db`) or PostgreSQL database with synthetic residents. |
| [`synthetic_bundle.json`](file:///Users/dpcubed/projects/aadhar-tracker/dummy_data_to_test/synthetic_bundle.json) | Complete unified fixture dataset containing identities, dark-web breach catalogs, and DLP chat threads. |
| [`synthetic_identities.json`](file:///Users/dpcubed/projects/aadhar-tracker/dummy_data_to_test/synthetic_identities.json) | Sample dataset of valid synthetic Indian citizen profiles across 12 states. |
| [`synthetic_breach_catalog.json`](file:///Users/dpcubed/projects/aadhar-tracker/dummy_data_to_test/synthetic_breach_catalog.json) | Simulated dark web breach dumps (Telecom KYC leak, Fintech applicant dump, Lumma stealer log bundle). |
| [`synthetic_whatsapp_messages.json`](file:///Users/dpcubed/projects/aadhar-tracker/dummy_data_to_test/synthetic_whatsapp_messages.json) | Realistic multi-turn English and Hinglish WhatsApp chat threads with unmasked IDs for DLP testing. |

---

## 🚀 Quickstart Commands

### 1. Generate & Inspect a Sample Profile in Terminal
```bash
python dummy_data_to_test/generator.py
```

### 2. Export / Refresh JSON Fixtures
```bash
python dummy_data_to_test/seed_db.py --export-fixtures
```

### 3. Seed Local Database with Synthetic Residents & Incidents
```bash
# Seeds local database with 10 synthetic residents, encrypted identifiers, and incidents
python dummy_data_to_test/seed_db.py --seed-db --residents 10
```

---

## 🐍 Python Import Usage

You can import and use the generator functions directly in your tests or scripts:

```python
from dummy_data_to_test.generator import (
    generate_synthetic_aadhaar,
    generate_synthetic_pan,
    generate_synthetic_resident_profile,
    generate_synthetic_breach_dump,
    generate_synthetic_whatsapp_conversations,
)

# 1. Generate a mathematically valid 12-digit Aadhaar number
aadhaar = generate_synthetic_aadhaar(prefix_range="9999", formatted=True)
print(aadhaar) # e.g. "9999 4105 7058"

# 2. Generate a valid 10-character PAN number matching surname
pan = generate_synthetic_pan(last_name="Sharma", entity_type="P")
print(pan) # e.g. "ABCPS1234F"

# 3. Generate a full synthetic citizen profile
profile = generate_synthetic_resident_profile()
print(profile["full_name"], profile["email"], profile["aadhaar_masked"])

# 4. Generate a simulated dark-web breach dump
breach = generate_synthetic_breach_dump(num_records=25)
print(breach["breach_name"], breach["total_records_in_dump"])
```
