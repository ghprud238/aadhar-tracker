"""
Sliding Window Rate Limiting Middleware.
Throttles abusive endpoints (e.g. OTP verification attempts, high-frequency scans)
and enforces fair usage across tenants without storing PII.
"""
import time
import asyncio
from typing import Dict, List, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitRule:
    def __init__(self, path_prefix: str, method: str, max_requests: int, window_seconds: int):
        self.path_prefix = path_prefix
        self.method = method
        self.max_requests = max_requests
        self.window_seconds = window_seconds


# Targeted rules for sensitive routes
RULES = [
    # Protect challenge token verification against brute-force (5 attempts per 15 mins)
    RateLimitRule(
        path_prefix="/api/v1/identifiers/verification-challenges/complete",
        method="POST",
        max_requests=5,
        window_seconds=900
    ),
    # Protect on-demand scans against quota exhaustion (10 scans per 60 secs)
    RateLimitRule(
        path_prefix="/api/v1/scans",
        method="POST",
        max_requests=10,
        window_seconds=60
    ),
]


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, default_max_per_minute: int = 180):
        super().__init__(app)
        self.default_max = default_max_per_minute
        # Dict[client_key, List[timestamp]]
        self._history: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()

    def _get_client_key(self, request: Request, rule_key: str) -> str:
        # Prefer Authorization bearer or session cookie; fallback to client IP
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1][:16]
            return f"{rule_key}:usr_{token}"

        client_host = request.client.host if request.client else "unknown_ip"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_host = forwarded.split(",")[0].strip()
        return f"{rule_key}:ip_{client_host}"

    async def dispatch(self, request: Request, call_next):
        # Exclude static assets and health probes from rate limiting
        if request.url.path.startswith(("/static", "/wearable", "/healthz", "/livez", "/readyz", "/metrics", "/docs", "/openapi.json")):
            return await call_next(request)

        # Match specific rule if any
        matching_rule: RateLimitRule | None = None
        for rule in RULES:
            if request.url.path.startswith(rule.path_prefix) and request.method == rule.method:
                matching_rule = rule
                break

        max_reqs = matching_rule.max_requests if matching_rule else self.default_max
        window_sec = matching_rule.window_seconds if matching_rule else 60
        rule_name = matching_rule.path_prefix if matching_rule else "global"

        client_key = self._get_client_key(request, rule_name)
        now = time.time()
        window_start = now - window_sec

        async with self._lock:
            # Filter timestamps outside window
            timestamps = [t for t in self._history.get(client_key, []) if t > window_start]

            if len(timestamps) >= max_reqs:
                earliest = timestamps[0]
                retry_after = int(max(1.0, (earliest + window_sec) - now))
                return JSONResponse(
                    status_code=429,
                    headers={"Retry-After": str(retry_after)},
                    content={
                        "error": {
                            "code": "RATE_LIMITED",
                            "message": f"Rate limit exceeded. Maximum {max_reqs} requests allowed per {window_sec} seconds.",
                            "retryable": True,
                            "retry_after_seconds": retry_after
                        }
                    }
                )

            timestamps.append(now)
            self._history[client_key] = timestamps

        response = await call_next(request)
        return response
