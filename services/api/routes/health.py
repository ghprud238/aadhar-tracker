"""
Health, Readiness, Liveness Probes, and Prometheus Metrics Exporter.
Conforms to Kubernetes standard probe specifications and RFC 8615 healthcheck formats.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func

from services.api.database import get_db
from packages.domain.models import OutboxEvent
from packages.provider_adapters.registry import provider_registry
from packages.observability.metrics import (
    metrics,
    prom_outbox_queue_depth,
    prom_dead_letter_depth,
    CONTENT_TYPE_LATEST,
)

router = APIRouter(tags=["observability"])


@router.get("/metrics", include_in_schema=False)
async def get_prometheus_metrics(db: AsyncSession = Depends(get_db)):
    """Scrape endpoint for Prometheus monitoring agents."""
    try:
        # Update gauges prior to scrape
        res_pending = await db.execute(
            select(func.count(OutboxEvent.id)).where(OutboxEvent.state == "pending")
        )
        prom_outbox_queue_depth.set(res_pending.scalar() or 0)

        res_dlq = await db.execute(
            select(func.count(OutboxEvent.id)).where(OutboxEvent.state == "dead_letter")
        )
        prom_dead_letter_depth.set(res_dlq.scalar() or 0)
    except Exception:
        pass

    return Response(
        content=metrics.export_prometheus(),
        media_type=CONTENT_TYPE_LATEST
    )


@router.get("/healthz")
@router.get("/livez")
async def liveness_probe():
    """Liveness probe: verifies process is up and responsive."""
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/readyz")
async def readiness_probe(db: AsyncSession = Depends(get_db)):
    """
    Readiness probe: verifies database connection pool and external provider circuits.
    Returns HTTP 503 if essential dependencies are failing.
    """
    checks = {
        "database": False,
        "circuit_breakers": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    # 1. Database Check
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        checks["database_error"] = str(e)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "checks": checks}
        )

    # 2. Check provider health
    health_reports = await provider_registry.get_all_health()
    open_circuits = [h.provider for h in health_reports if "OPEN" in (h.status_message or "")]
    if open_circuits:
        checks["open_circuits"] = open_circuits
        checks["circuit_breakers"] = "degraded"

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "ready", "checks": checks}
    )
