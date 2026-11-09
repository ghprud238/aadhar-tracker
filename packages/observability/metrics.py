"""
Telemetry, Prometheus Metrics, and Operational Counters.
Complies with PRD Page 53-54: Never records resident PII or queries as metric labels.
"""
from typing import Dict, Any
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    REGISTRY
)

# Standard Prometheus Metrics
prom_requests_total = Counter(
    "suraksha_http_requests_total",
    "Total HTTP requests received",
    ["method", "status", "endpoint"]
)

prom_request_duration = Histogram(
    "suraksha_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

prom_scans_total = Counter(
    "suraksha_scans_total",
    "Total intelligence scans executed",
    ["provider", "status"]
)

prom_incidents_total = Counter(
    "suraksha_incidents_total",
    "Total incidents detected across sources",
    ["severity", "source_type"]
)

prom_circuit_breaker_trips = Counter(
    "suraksha_circuit_breaker_trips_total",
    "Total times provider circuit breakers tripped OPEN",
    ["provider"]
)

prom_outbox_queue_depth = Gauge(
    "suraksha_outbox_queue_depth",
    "Number of pending outbox events awaiting processing"
)

prom_dead_letter_depth = Gauge(
    "suraksha_outbox_dead_letter_depth",
    "Number of events permanently failed in dead letter queue"
)


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

    def export_prometheus(self) -> bytes:
        """Generates standard Prometheus scrape output."""
        return generate_latest(REGISTRY)


metrics = MetricsRegistry()
