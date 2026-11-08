# Runbook: Provider Outage

## Severity
Medium to High (depending on provider tier)

## Symptoms
- Outbox dispatcher logs 5xx errors or connection timeouts to HIBP or Flare.
- Dashboard indicates provider status `delayed` or `unavailable`.

## Actions
1. Confirm provider outage via external status pages or curl health check.
2. If outage exceeds 30 minutes, invoke kill switch: `POST /internal/connectors/{id}/disable` with reason `upstream_outage`.
3. Schedulers will automatically skip scans for disabled providers and mark scan runs as `partially_completed`.
4. Once upstream is restored, invoke `POST /internal/connectors/{id}/reconcile` and re-enable the connector.
