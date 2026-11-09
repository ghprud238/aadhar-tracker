#!/usr/bin/env python3
"""
CLI Tool for Cryptographic Key Rotation.
Usage:
  uv run python -m services.tools.rotate_keys --tenant-id <id> [--dry-run]
"""
import asyncio
import argparse
import sys
from services.api.database import async_session_factory
from packages.security.crypto import vault, EnvelopeVault
from packages.security.key_rotation import KeyRotationManager


async def main():
    parser = argparse.ArgumentParser(description="Suraksha Cryptographic Vault Key Rotator")
    parser.add_argument("--tenant-id", required=True, help="Tenant UUID to rotate keys for")
    parser.add_argument("--dry-run", action="store_true", help="Simulate rotation without committing changes")
    parser.add_argument("--new-master-key", default="new_secret_master_key_2026_rotated!", help="Target master key")
    args = parser.parse_args()

    new_vault = EnvelopeVault(master_key=args.new_master_key.encode())
    manager = KeyRotationManager(current_vault=vault, target_vault=new_vault)

    print(f"[*] Starting key rotation for tenant: {args.tenant_id} (dry_run={args.dry_run})")
    async with async_session_factory() as session:
        success, errors = await manager.rotate_tenant_identifiers(session, args.tenant_id, dry_run=args.dry_run)

    print(f"[+] Rotation finished: {success} succeeded, {errors} failed.")
    if errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
