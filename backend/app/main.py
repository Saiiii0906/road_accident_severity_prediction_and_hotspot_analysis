import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import uuid
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# Router objects are named `router` in each route module; aliased here to
# the domain-specific names used throughout this file for readability.
from app.routes.severity_route import router as severity_router
from app.routes.hotspot_route import router as hotspot_router
from app.routes.risk_route import router as risk_router
from app.routes.report_route import router as report_router
from app.routes.journey_route import router as journey_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

API_VERSION = "1.0.0"

API_DESCRIPTION = """
Production API for road accident severity prediction, accident hotspot analysis,
topological road risk assessment, and journey safety intelligence, built on
the UK Road Safety Dataset and real-time environmental data feeds.

**Capabilities:**
- **Student A (Severity Prediction):** 138-feature Random Forest classifier predicting collision severity (Fatal, Serious, Slight).
- **Student B (Hotspot Analysis):** In-memory DBSCAN clustering over 3,700+ empirical accident clusters across Great Britain.
- **Student C (Road Risk Analysis):** Graph Neural Network (GNN) continuous structural risk evaluation over 13,900+ road segments.
- **Journey Safety Analysis:** Multi-source corridor safety evaluation combining real geocoding (Nominatim), routing (OSRM), live environmental telemetry (Open-Meteo weather, TfL traffic delays, and active incident disruptions), historical corridor matching, deterministic safety assessment, and grounded Gemini AI synthesis.
- **AI Infrastructure Report:** Evidence-grounded multi-model decision-support report synthesis for transport planning.
"""

from app.config import settings
from app.services.severity_service import SeverityModelManager
from app.services.hotspot_service import HotspotDataManager
from app.services.risk_service import RiskDataManager
from app.services.corridor_matching_service import CorridorMatchingService

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown.

    Loads the Student A Machine Learning model artifacts, Student B
    DBSCAN hotspot summary artifacts, Student C GNN road risk predictions,
    and pre-warms corridor spatial indexing structures.
    """
    logger.info("Application Starting: loading model artifacts and data...")
    try:
        SeverityModelManager.get_instance().load()
        logger.info("Student A Severity Model loaded and ready.")
    except Exception as exc:
        logger.error("Critical: Could not load Student A severity model at startup: %s", exc)
        raise exc

    try:
        HotspotDataManager().load()
        logger.info("Student B Hotspot Data Manager loaded and ready.")
    except Exception as exc:
        logger.error("Critical: Could not load Student B hotspot data at startup: %s", exc)
        raise exc

    try:
        RiskDataManager().load()
        logger.info("Student C Risk Data Manager loaded and ready.")
    except Exception as exc:
        logger.error("Critical: Could not load Student C risk data at startup: %s", exc)
        raise exc

    try:
        CorridorMatchingService.prewarm()
        logger.info("Corridor Matching spatial indexes pre-warmed and ready.")
    except Exception as exc:
        logger.error("Critical: Could not pre-warm corridor matching indexes: %s", exc)
        raise exc

    logger.info("Application Started")
    yield
    logger.info("Application Stopped")

app = FastAPI(
    title="Road Accident Severity Prediction & Hotspot Analysis API",
    description=API_DESCRIPTION,
    version=API_VERSION,
    contact={
        "name": "Road Safety Analytics Team",
        "email": "team@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    terms_of_service="https://example.com/terms",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_REQUEST_BODY_BYTES = 5 * 1024 * 1024  # 5 MB


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Enforce payload size limits and inject defense-in-depth security headers."""
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_REQUEST_BODY_BYTES:
                return JSONResponse(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    content={"detail": "Request payload exceeds maximum allowed limit (5 MB)."},
                )
        except ValueError:
            pass

    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"

    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch unhandled exceptions and return safe 500 response without leaking internals."""
    if isinstance(exc, StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None),
        )

    error_id = f"err-{uuid.uuid4().hex[:12]}"
    logger.error(
        "Unhandled exception [error_id=%s] on %s %s: %s",
        error_id,
        request.method,
        request.url.path,
        exc,
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred.",
            "error_id": error_id,
        },
    )

# Mount routes at root and /api for full compatibility with frontend / direct consumers
app.include_router(severity_router)
app.include_router(severity_router, prefix=settings.API_PREFIX)
app.include_router(hotspot_router)
app.include_router(hotspot_router, prefix=settings.API_PREFIX)
app.include_router(risk_router)
app.include_router(risk_router, prefix=settings.API_PREFIX)
app.include_router(report_router)
app.include_router(report_router, prefix=settings.API_PREFIX)
app.include_router(journey_router)
app.include_router(journey_router, prefix=settings.API_PREFIX)


@app.get(
    "/",
    tags=["System"],
    summary="API root",
    description="Basic metadata confirming the API is reachable.",
)
def read_root() -> dict[str, str]:
    """Return basic project metadata."""
    return {
        "project": "Road Accident Severity Prediction & Hotspot Analysis",
        "version": API_VERSION,
        "status": "Running",
        "docs": "/docs",
    }


@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
    description="Liveness check for uptime monitoring and load balancers.",
)
def read_health() -> dict[str, str]:
    """Return current service health and timestamp."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "api_version": API_VERSION,
    }