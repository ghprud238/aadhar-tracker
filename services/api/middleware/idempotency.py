"""
Idempotency Middleware for Mutating API Requests.
Protects residents and billing operations from accidental duplicate form submissions or network retries.
"""
import time
import asyncio
from typing import Dict, Any, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse


class IdempotencyRecord:
    def __init__(self, status_code: int, headers: dict, body: bytes, expires_at: float):
        self.status_code = status_code
        self.headers = headers
        self.body = body
        self.expires_at = expires_at


class IdempotencyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, ttl_seconds: int = 86400):
        super().__init__(app)
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, IdempotencyRecord] = {}
        self._in_flight: set = set()
        self._lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next):
        # Only check mutating methods
        if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
            return await call_next(request)

        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        now = time.time()

        # 1. Check if cached response exists
        async with self._lock:
            # Clean expired records periodically
            expired_keys = [k for k, v in self._cache.items() if v.expires_at < now]
            for k in expired_keys:
                del self._cache[k]

            if idempotency_key in self._cache:
                cached = self._cache[idempotency_key]
                response_headers = dict(cached.headers)
                response_headers["X-Idempotent-Replay"] = "true"
                return Response(
                    content=cached.body,
                    status_code=cached.status_code,
                    headers=response_headers,
                    media_type=cached.headers.get("content-type", "application/json")
                )

            # 2. Prevent concurrent duplicate requests with the exact same key
            if idempotency_key in self._in_flight:
                return JSONResponse(
                    status_code=409,
                    content={
                        "error": {
                            "code": "IDEMPOTENCY_CONFLICT",
                            "message": "A request with this Idempotency-Key is currently being processed. Please retry shortly.",
                            "retryable": True
                        }
                    }
                )

            self._in_flight.add(idempotency_key)

        try:
            response = await call_next(request)

            # Read response body to cache it
            response_body = [section async for section in response.body_iterator]
            body_bytes = b"".join(response_body)

            # Only cache 2xx and 4xx client errors (do not cache transient 5xx server errors)
            if response.status_code < 500:
                record = IdempotencyRecord(
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    body=body_bytes,
                    expires_at=now + self.ttl_seconds
                )
                async with self._lock:
                    self._cache[idempotency_key] = record

            return Response(
                content=body_bytes,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
        finally:
            async with self._lock:
                self._in_flight.discard(idempotency_key)
