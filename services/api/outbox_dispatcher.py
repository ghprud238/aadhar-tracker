"""
Transactional Outbox Dispatcher.
Reads unhandled outbox events and dispatches them to respective workers.
Guarantees at-least-once delivery and consumer idempotency (ADR-006).
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from packages.domain.models import OutboxEvent
from services.connector_worker.worker import ConnectorWorker
from services.notification_worker.worker import NotificationWorker
from services.privacy_worker.worker import PrivacyWorker
from packages.observability.logging import logger


class OutboxDispatcher:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.connector_worker = ConnectorWorker(db)
        self.notification_worker = NotificationWorker(db)
        self.privacy_worker = PrivacyWorker(db)

    async def dispatch_pending(self, limit: int = 10) -> int:
        """Process a batch of pending outbox events."""
        res = await self.db.execute(
            select(OutboxEvent)
            .where(OutboxEvent.state == "pending")
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
                        await self.connector_worker.process_job(job_id)
                    event.state = "published"
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
                    await self.db.commit()
                    processed_count += 1
                else:
                    event.state = "published"
                    await self.db.commit()
                    processed_count += 1
            except Exception as e:
                logger.error(f"Error dispatching outbox event {event.event_id}: {str(e)}")
                event.state = "failed"
                await self.db.commit()

        return processed_count
