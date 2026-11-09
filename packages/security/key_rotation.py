"""
Key Encryption Key (KEK) & DEK Re-encryption Utility.
Enables periodic or emergency cryptographic key rotation for RBI/DPDP compliance
without exposing resident plaintext credentials to logs or persistent storage.
"""
from typing import Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from packages.security.crypto import EnvelopeVault
from packages.domain.models import Identifier
from packages.observability.logging import logger


class KeyRotationManager:
    def __init__(self, current_vault: EnvelopeVault, target_vault: EnvelopeVault):
        self.current_vault = current_vault
        self.target_vault = target_vault

    def re_encrypt_value(self, encrypted_envelope: str, associated_data: str) -> str:
        """Decrypts with current vault and immediately re-encrypts with target vault."""
        plaintext = self.current_vault.decrypt(encrypted_envelope, associated_data=associated_data)
        return self.target_vault.encrypt(plaintext, associated_data=associated_data)

    async def rotate_tenant_identifiers(
        self,
        db: AsyncSession,
        tenant_id: str,
        dry_run: bool = False
    ) -> Tuple[int, int]:
        """
        Re-encrypts all resident identifiers belonging to a tenant under the new master key.
        Returns: (success_count, error_count)
        """
        res = await db.execute(
            select(Identifier).where(Identifier.tenant_id == tenant_id)
        )
        identifiers = res.scalars().all()
        success = 0
        errors = 0

        for ident in identifiers:
            try:
                ad = f"{ident.tenant_id}:{ident.subject_id}"
                re_encrypted = self.re_encrypt_value(ident.encrypted_value, associated_data=ad)
                if not dry_run:
                    ident.encrypted_value = re_encrypted
                success += 1
            except Exception as e:
                logger.error(f"Failed to re-encrypt identifier {ident.id}: {str(e)}")
                errors += 1

        if not dry_run and success > 0:
            await db.commit()

        logger.info(
            f"Key rotation completed for tenant {tenant_id}: "
            f"{success} rotated, {errors} errors (dry_run={dry_run})"
        )
        return success, errors
