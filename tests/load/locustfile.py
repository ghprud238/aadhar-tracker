"""
Locust Load & Stress Testing Benchmark for Suraksha Platform.
Simulates high-concurrency resident activity: authentication, companion glance,
idempotent scan requests, and incident retrievals.

Run with:
  uv run locust -f tests/load/locustfile.py --headless -u 50 -r 10 --run-time 30s --host http://localhost:8000
"""
import uuid
import random
from locust import HttpUser, task, between


class ResidentUser(HttpUser):
    wait_time = between(0.1, 0.5)

    def on_start(self):
        """Simulate resident login and session creation."""
        self.user_email = f"loadtest_{uuid.uuid4().hex[:8]}@domain.com"
        res = self.client.get(
            f"/api/v1/auth/callback?email={self.user_email}&full_name=Load+Tester",
            name="/api/v1/auth/callback"
        )
        if res.status_code == 200:
            self.token = res.json()["data"]["session_id"]
            self.subject_id = res.json()["data"]["subject_id"]
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
        else:
            self.token = None
            self.headers = {}

    @task(5)
    def fetch_companion_glance(self):
        """High-frequency watch/widget polling."""
        if not self.token:
            return
        self.client.get("/api/v1/companion/glance", headers=self.headers, name="/api/v1/companion/glance")

    @task(3)
    def fetch_incidents(self):
        """Resident reviewing breach intelligence feed."""
        if not self.token:
            return
        self.client.get("/api/v1/incidents", headers=self.headers, name="/api/v1/incidents")

    @task(2)
    def submit_idempotent_scan(self):
        """Idempotent scan trigger with UUID key."""
        if not self.token:
            return
        key = str(uuid.uuid4())
        headers = dict(self.headers)
        headers["Idempotency-Key"] = key

        self.client.post(
            "/api/v1/scans",
            headers=headers,
            json={"identifier_ids": []},
            name="/api/v1/scans"
        )

    @task(1)
    def check_health(self):
        """External orchestrator health probe."""
        self.client.get("/readyz", name="/readyz")
