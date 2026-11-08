"""
Lightweight in-memory telemetry and metric counters for operational observability.
Complies with PRD Page 53-54. Never records PII or queries as metric labels.
"""
from typing import Dict, Any


class MetricsRegistry:
    def __init__(self):
        self.counters: Dict[str, int] = {
            "verified_identifiers_total": 0,
            "active_monitoring_targets": 0,
            "initial_scans_completed": 0,
            "partial_scans_total": 0,
            "incidents_created_total": 0,
            "remediation_actions_completed": 0,
            "disputes_total": 0,
            "consent_withdrawals_total": 0,
            "account_deletions_total": 0,
            "provider_requests_total": 0,
            "provider_errors_total": 0,
            "outbox_events_published": 0,
            "dead_letter_events_total": 0,
            "authorization_denials_total": 0,
            "step_up_failures_total": 0,
        }

    def increment(self, metric_name: str, amount: int = 1):
        if metric_name in self.counters:
            self.counters[metric_name] += amount
        else:
            self.counters[metric_name] = amount

    def get_snapshot(self) -> Dict[str, int]:
        return dict(self.counters)


metrics = MetricsRegistry()
