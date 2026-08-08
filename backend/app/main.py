import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Router objects are named `router` in each route module; aliased here to
# the domain-specific names used throughout this file for readability.
from app.routes.severity_route import router as severity_router
from app.routes.hotspot_route import router as hotspot_router
from app.routes.risk_route import router as risk_router
from app.routes.report_route import router as report_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

API_VERSION = "1.0.0"

API_DESCRIPTION = """
API for predicting road accident severity, identifying accident hotspots,
assessing location-based risk, and generating accident reports, built on
the UK Road Safety Dataset.

**Current status:** the prediction and analysis endpoints are backed by a
mock service layer with a stable response contract. Real trained models
will be integrated behind the same endpoints without any change to this
API surface.

**Capabilities:**
- Predict the severity of a single accident or a batch of accidents
- Identify accident hotspot clusters within an area
- Assess accident risk for a given location and condition set
- Generate aggregate accident reports and export them as files
"""

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown.

    Replaces the deprecated `@app.on_event("startup"/"shutdown")` pattern.
    Code before `yield` runs on startup; code after `yield` runs on
    shutdown. No resources are acquired here today (the mock service
    layer needs none), but this is the single place to add them — e.g. a
    database connection pool or a loaded ML model — when they exist.
    """
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

DEVELOPMENT_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=DEVELOPMENT_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(severity_router)
app.include_router(hotspot_router)
app.include_router(risk_router)
app.include_router(report_router)

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