"""
Identity Protection Platform - Business API & BFF Entry Point.
"""
import uuid
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from services.api.database import init_db
from services.api.dependencies import get_request_id
from packages.domain.schemas import ApiErrorResponse, ErrorDetail, ResponseMeta

from services.api.routes.auth import router as auth_router
from services.api.routes.account import router as account_router
from services.api.routes.consents import router as consents_router
from services.api.routes.identifiers import router as identifiers_router
from services.api.routes.monitoring import router as monitoring_router
from services.api.routes.incidents import router as incidents_router
from services.api.routes.notifications import router as notifications_router
from services.api.routes.identity_assistance import router as assistance_router
from services.api.routes.billing import router as billing_router
from services.api.routes.privacy import router as privacy_router
from services.api.routes.internal import router as internal_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables and seeds on startup
    await init_db()
    yield


app = FastAPI(
    title="Identity Protection Platform",
    description="Consent-first identity monitoring, breach intelligence, and Aadhaar/PAN assistance platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_and_tracing_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = req_id

    response = await call_next(request)

    # Security headers
    response.headers["X-Request-ID"] = req_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    code_map = {
        400: "BAD_REQUEST",
        401: "AUTHENTICATION_REQUIRED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMITED",
        500: "INTERNAL_SERVER_ERROR",
        503: "SERVICE_UNAVAILABLE"
    }
    err_code = code_map.get(exc.status_code, "HTTP_ERROR")
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiErrorResponse(
            error=ErrorDetail(
                code=err_code,
                message=str(exc.detail),
                retryable=exc.status_code in (429, 503)
            ),
            meta=ResponseMeta(request_id=req_id)
        ).model_dump()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    field_errors = [
        {"field": ".".join(str(loc) for loc in err["loc"]), "message": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ApiErrorResponse(
            error=ErrorDetail(
                code="VALIDATION_FAILED",
                message="Request validation failed",
                retryable=False,
                field_errors=field_errors
            ),
            meta=ResponseMeta(request_id=req_id)
        ).model_dump()
    )


# Attach API routes under /api/v1
app.include_router(auth_router, prefix="/api/v1")
app.include_router(account_router, prefix="/api/v1")
app.include_router(consents_router, prefix="/api/v1")
app.include_router(identifiers_router, prefix="/api/v1")
app.include_router(monitoring_router, prefix="/api/v1")
app.include_router(incidents_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(assistance_router, prefix="/api/v1")
app.include_router(billing_router, prefix="/api/v1")
app.include_router(privacy_router, prefix="/api/v1")
app.include_router(internal_router, prefix="/api/v1")

# Mount Static Files and Web App Frontend
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "apps", "web", "public")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    @app.get("/app", include_in_schema=False)
    async def serve_index():
        return FileResponse(os.path.join(static_dir, "index.html"))
