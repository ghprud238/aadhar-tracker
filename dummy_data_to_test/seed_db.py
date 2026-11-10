"""
Synthetic database seeder and test fixture exporter for Suraksha Platform.
Can be executed directly from the dummy_data_to_test folder or via python -m.
"""
import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from dummy_data_to_test.generator import (
    generate_complete_test_fixture_bundle,
    generate_synthetic_resident_profile,
    generate_synthetic_breach_dump,
    generate_synthetic_whatsapp_conversations,
    BREACH_TEMPLATES,
)
from packages.security.crypto import vault
from packages.domain.models import (
    User, Tenant, Membership, Subject, Identifier,
    ConsentGrant, ProcessingNotice, Incident, RemediationAction, OutboxEvent
)
from services.api.database import async_session_factory, init_db


THIS_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = ROOT_DIR / "tests" / "fixtures"


def export_fixture_files(bundle: dict, output_dirs: list[Path] = None):
    """Writes formatted synthetic test fixture JSON files for automated tests and dummy folder."""
    if output_dirs is None:
        output_dirs = [THIS_DIR, FIXTURES_DIR]

    for out_dir in output_dirs:
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Complete Bundle
        bundle_path = out_dir / "synthetic_bundle.json"
        with open(bundle_path, "w", encoding="utf-8") as f:
            json.dump(bundle, f, indent=2)
        print(f"[*] Exported full synthetic bundle -> {bundle_path}")

        # 2. Identities Fixture
        identities_path = out_dir / "synthetic_identities.json"
        with open(identities_path, "w", encoding="utf-8") as f:
            json.dump(bundle["identities"], f, indent=2)
        print(f"[*] Exported {len(bundle['identities'])} synthetic identities -> {identities_path}")

        # 3. Breach Catalog Fixture
        breaches_path = out_dir / "synthetic_breach_catalog.json"
        with open(breaches_path, "w", encoding="utf-8") as f:
            json.dump(bundle["breach_catalog"], f, indent=2)
        print(f"[*] Exported {len(bundle['breach_catalog'])} synthetic breaches -> {breaches_path}")

        # 4. WhatsApp DLP Messages Fixture
        wa_path = out_dir / "synthetic_whatsapp_messages.json"
        with open(wa_path, "w", encoding="utf-8") as f:
            json.dump(bundle["whatsapp_dlp_samples"], f, indent=2)
        print(f"[*] Exported {len(bundle['whatsapp_dlp_samples'])} synthetic WhatsApp DLP samples -> {wa_path}")


async def seed_database(num_residents: int = 5, seed: int = 101):
    """Seeds the local SQLite/PostgreSQL database with synthetic resident profiles and incidents."""
    print(f"[*] Initializing database schema...")
    await init_db()

    print(f"[*] Seeding {num_residents} synthetic resident profiles into database...")
    async with async_session_factory() as session:
        for i in range(num_residents):
            prof = generate_synthetic_resident_profile(seed=seed + i)
            tenant_name = f"tenant_{prof['last_name'].lower()}_{i+1}"
            
            # 1. Create User then Tenant
            user = User(
                idp_subject=f"synth_idp_{prof['last_name'].lower()}_{i+1}_{seed}",
                email=prof["email"],
                full_name=prof["full_name"],
                account_state="active"
            )
            session.add(user)
            await session.flush()

            tenant = Tenant(name=tenant_name, owner_user_id=user.id)
            session.add(tenant)
            await session.flush()

            # 2. Membership & Subject
            membership = Membership(
                tenant_id=tenant.id,
                user_id=user.id,
                role="citizen"
            )
            session.add(membership)

            subject = Subject(
                tenant_id=tenant.id,
                owner_user_id=user.id,
                monitoring_state="active"
            )
            session.add(subject)
            await session.flush()

            # 3. Consent Grant
            consent = ConsentGrant(
                tenant_id=tenant.id,
                subject_id=subject.id,
                notice_version="1.0",
                status="granted"
            )
            session.add(consent)

            # 4. Encrypted Aadhaar & PAN in Zero-Plaintext Vault
            enc_aadhaar = vault.encrypt(prof["aadhaar_raw"], associated_data=tenant.id)
            blind_aadhaar = vault.compute_blind_index(prof["aadhaar_raw"], scope=tenant.id)
            aadhaar_ident = Identifier(
                tenant_id=tenant.id,
                subject_id=subject.id,
                type="aadhaar",
                encrypted_value=enc_aadhaar,
                blind_index=blind_aadhaar,
                masked_value=prof["aadhaar_masked"],
                state="verified"
            )
            session.add(aadhaar_ident)

            enc_pan = vault.encrypt(prof["pan_raw"], associated_data=tenant.id)
            blind_pan = vault.compute_blind_index(prof["pan_raw"], scope=tenant.id)
            pan_ident = Identifier(
                tenant_id=tenant.id,
                subject_id=subject.id,
                type="pan",
                encrypted_value=enc_pan,
                blind_index=blind_pan,
                masked_value=prof["pan_masked"],
                state="verified"
            )
            session.add(pan_ident)
            await session.flush()

            # 5. Create a Synthetic Incident for the first resident
            if i == 0:
                incident = Incident(
                    tenant_id=tenant.id,
                    subject_id=subject.id,
                    incident_grouping_key=f"synthetic_breach_telecom_{user.id[:8]}",
                    title=f"Synthetic Dark Web KYC Dump Exposure ({prof['aadhaar_masked']})",
                    severity="critical",
                    confidence="confirmed",
                    state="new",
                    identifier_id=aadhaar_ident.id,
                    exposure_categories=["government_id", "darkweb_leak", "aadhaar", "pan"],
                    priority_score=95,
                    rules_version="1.0",
                    first_detected_at=datetime.now(timezone.utc)
                )
                session.add(incident)
                await session.flush()

                action_lock = RemediationAction(
                    tenant_id=tenant.id,
                    incident_id=incident.id,
                    action_type="biometric_lock",
                    title="Lock UIDAI Biometrics",
                    description="Enable biometric lock on https://myaadhaar.uidai.gov.in/.",
                    state="pending"
                )
                action_vid = RemediationAction(
                    tenant_id=tenant.id,
                    incident_id=incident.id,
                    action_type="generate_vid",
                    title="Generate 16-Digit Virtual ID",
                    description=f"Generate temporary VID for Aadhaar {prof['aadhaar_masked']}.",
                    state="pending"
                )
                session.add_all([action_lock, action_vid])

                outbox_evt = OutboxEvent(
                    event_id=f"evt_synth_{prof['last_name'].lower()}_{i}",
                    event_type="incident.detected",
                    tenant_id=tenant.id,
                    subject_id=subject.id,
                    resource_id=incident.id,
                    authorization_version=subject.authorization_version,
                    payload={
                        "incident_id": incident.id,
                        "masked_identifier": prof["aadhaar_masked"],
                        "severity": "critical",
                        "synthetic": True
                    }
                )
                session.add(outbox_evt)

        await session.commit()
    print(f"[✓] Successfully seeded {num_residents} synthetic resident profiles into the database!")


def main():
    parser = argparse.ArgumentParser(description="Synthetic Test Data Generator & DB Seeder (dummy_data_to_test)")
    parser.add_argument("--export-fixtures", action="store_true", help="Export static synthetic fixtures to JSON files")
    parser.add_argument("--seed-db", action="store_true", help="Seed the local database with synthetic test data")
    parser.add_argument("--residents", type=int, default=5, help="Number of synthetic resident profiles to generate (default: 5)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible generation (default: 42)")

    args = parser.parse_args()

    if not args.export_fixtures and not args.seed_db:
        args.export_fixtures = True

    bundle = generate_complete_test_fixture_bundle(num_profiles=args.residents * 2, seed=args.seed)

    if args.export_fixtures:
        export_fixture_files(bundle)

    if args.seed_db:
        asyncio.run(seed_database(num_residents=args.residents, seed=args.seed))


if __name__ == "__main__":
    main()
