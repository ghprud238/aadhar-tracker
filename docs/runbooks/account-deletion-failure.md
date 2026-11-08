# Runbook: Account Deletion Failure

## Severity
High (Regulatory / Privacy SLA)

## Symptoms
- `privacy_requests` or `deletion_tasks` in state `pending` beyond 24 hours.
- Upstream provider unregister API times out.

## Actions
1. Inspect `GET /internal/privacy/deletions` for stuck deletion task IDs.
2. If external provider unregister failed, review provider connectivity and trigger retry: `POST /internal/jobs/{id}/retry`.
3. Verify that the user's active tenant and subject records have their processing flagged `processing_disabled`.
4. Once completed, issue deletion tombstone.
