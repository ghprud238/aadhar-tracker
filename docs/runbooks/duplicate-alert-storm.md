# Runbook: Duplicate Alert Storm

## Severity
High

## Symptoms
- Notification queue rate spikes abruptly.
- Multiple alerts created for identical finding or incident IDs.

## Actions
1. Activate alert kill-switch via configuration flag `ALERTS_EMERGENCY_PAUSE=true`.
2. Inspect `outbox_events` and `notification_deliveries` to identify offending incident grouping key or provider replay.
3. Check idempotency keys in `notification_deliveries`.
4. Drain and re-index duplicate outbox events.
5. Re-enable alerts after verifying deduplication logic.
