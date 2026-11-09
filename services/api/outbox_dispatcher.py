"""
Transactional Outbox Dispatcher.
Reads unhandled outbox events and dispatches them to respective workers.
Guarantees at-least-once delivery and consumer idempotency (ADR-006).
"""
import asyncio
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from packages.domain.models import OutboxEvent
from services.connector_worker.worker import ConnectorWorker
from services.notification_worker.worker import NotificationWorker
from services.privacy_worker.worker import PrivacyWorker
from packages.observability.logging import logger


class OutboxDispatcher:
    def __init__(self, db: AsyncSession, max_retries: int = 3):
        self.db = db
        self.max_retries = max_retries
        self.connector_worker = ConnectorWorker(db)
        self.notification_worker = NotificationWorker(db)
        self.privacy_worker = PrivacyWorker(db)

    async def dispatch_pending(self, limit: int = 10) -> int:
        """Process a batch of pending or failed retryable outbox events."""
        res = await self.db.execute(
            select(OutboxEvent)
            .where(OutboxEvent.state.in_(["pending", "failed"]))
            .where(OutboxEvent.retry_count < self.max_retries)
            .order_by(OutboxEvent.created_at.asc())
            .limit(limit)
        )
        events = res.scalars().all()
        processed_count = 0

        for event in events:
            try:
                if event.event_type == "monitoring.scan.requested":
                    job_id = event.payload.get("job_id") if event.payload else None
                    if job_id:
                        ok = await self.connector_worker.process_job(job_id)
                        if not ok:
                            raise RuntimeError(f"Monitoring job {job_id} not found or failed")
                    event.state = "published"
                    event.published_at = datetime.now(timezone.utc)
                    await self.db.commit()
                    processed_count += 1
                elif event.event_type == "alert.notification.requested":
                    await self.notification_worker.handle_alert_event(event)
                    processed_count += 1
                elif event.event_type == "privacy.account.deletion_requested":
                    await self.privacy_worker.handle_deletion_event(event)
                    processed_count += 1
                elif event.event_type == "privacy.consent.withdrawn":
                    event.state = "published"
                    event.published_at = datetime.now(timezone.utc)
                    await self.db.commit()
                    processed_count += 1
                else:
                    event.state = "published"
                    event.published_at = datetime.now(timezone.utc)
                    await self.db.commit()
                    processed_count += 1
            except Exception as e:
                err_msg = str(e)
                logger.error(f"Error dispatching outbox event {event.event_id}: {err_msg}")
                event.retry_count = (event.retry_count or 0) + 1
                event.last_error = err_msg

                if event.retry_count >= self.max_retries:
                    event.state = "dead_letter"
                    event.dead_lettered_at = datetime.now(timezone.utc)
                    logger.critical(
                        f"Outbox event {event.event_id} moved to DEAD LETTER QUEUE (exhausted {self.max_retries} attempts)"
                    )
                else:
                    event.state = "failed"
                await self.db.commit()

        return processed_count

    async def get_dead_letter_events(self, limit: int = 50) -> List[OutboxEvent]:
        """Query dead-lettered events for operator inspection."""
        res = await self.db.execute(
            select(OutboxEvent)
            .where(OutboxEvent.state == "dead_letter")
            .order_by(OutboxEvent.dead_lettered_at.desc())
            .limit(limit)
        )
        return list(res.scalars().all())

    async def re_drive_dead_letter(self, event_id: str) -> bool:
        """Operator re-drive: reset a dead-lettered event back to pending."""
        res = await self.db.execute(
            select(OutboxEvent).where(
                OutboxEvent.event_id == event_id,
                OutboxEvent.state == "dead_letter"
            )
        )
        event = res.scalars().first()
        if not event:
            return False

        event.state = "pending"
        event.retry_count = 0
        event.last_error = None
        event.dead_lettered_at = None
        await self.db.commit()
        logger.info(f"Outbox event {event_id} re-driven back to pending state.")
        return True
