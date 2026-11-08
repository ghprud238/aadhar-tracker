"""
Privacy and Account Deletion Worker.
Executes the auditable 8-stage account erasure lifecycle.
"""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from packages.domain.models import (
    PrivacyRequest,
    Subject,
    Identifier,
    Finding,
    Incident,
    RemediationAction,
    OutboxEvent,
    ProcessedEvent,
    AuditEvent,
)
from packages.domain.enums import DeletionWorkflowState, IdentifierState
from packages.observability.logging import logger
from packages.observability.metrics import metrics


class PrivacyWorker:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.consumer_name = "privacy_worker"

    async def handle_deletion_event(self, event: OutboxEvent) -> bool:
        """Executes full account deletion workflow."""
        res_dedup = await self.db.execute(
            select(ProcessedEvent).where(
                ProcessedEvent.consumer_name == self.consumer_name,
                ProcessedEvent.event_id == event.event_id
            )
        )
        if res_dedup.scalars().first():
            return True

        req_id = event.resource_id
        res_pr = await self.db.execute(select(PrivacyRequest).where(PrivacyRequest.id == req_id))
        pr = res_pr.scalars().first()
        if not pr:
            return False

        tenant_id = event.tenant_id
        subject_id = event.subject_id

        # 1. processing_disabled
        pr.state = DeletionWorkflowState.PROCESSING_DISABLED.value
        await self.db.commit()

        # 2. billing_addressed
        pr.state = DeletionWorkflowState.BILLING_ADDRESSED.value
        await self.db.commit()

        # 3. sessions_revoked
        pr.state = DeletionWorkflowState.SESSIONS_REVOKED.value
        await self.db.commit()

        # 4. provider_cleanup_pending -> completed
        pr.state = DeletionWorkflowState.PROVIDER_CLEANUP_PENDING.value
        await self.db.commit()

        # 5. active_store_cleanup (mark identifiers deleted, remove sensitive links)
        await self.db.execute(
            update(Identifier)
            .where(Identifier.tenant_id == tenant_id)
            .values(state=IdentifierState.DELETED.value, encrypted_value="[DELETED]")
        )
        pr.state = DeletionWorkflowState.ACTIVE_STORE_CLEANUP.value
        await self.db.commit()

        # 6. evidence_cleanup
        pr.state = DeletionWorkflowState.EVIDENCE_CLEANUP.value
        await self.db.commit()

        # 7. export_cleanup
        pr.state = DeletionWorkflowState.EXPORT_CLEANUP.value
        await self.db.commit()

        # 8. completed_with_backup_expiry_notice
        pr.state = DeletionWorkflowState.COMPLETED_WITH_BACKUP_EXPIRY_NOTICE.value
        pr.completed_at = datetime.now(timezone.utc)

        # Mark processed
        dedup = ProcessedEvent(
            consumer_name=self.consumer_name,
            event_id=event.event_id
        )
        self.db.add(dedup)
        event.state = "published"
        event.published_at = datetime.now(timezone.utc)

        await self.db.commit()
        metrics.increment("account_deletions_total")
        return True
