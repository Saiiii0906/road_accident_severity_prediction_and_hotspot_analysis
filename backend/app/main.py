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
from app.routes.journey_route import router as journey_router

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

from app.config import settings
from app.services.severity_service import SeverityModelManager
from app.services.hotspot_service import HotspotDataManager
from app.services.risk_service import RiskDataManager

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown.

    Loads the Student A Machine Learning model artifacts, Student B
    DBSCAN hotspot summary artifacts, and Student C GNN road risk predictions
    once at startup and keeps them resident in memory.
    """
    logger.info("Application Starting: loading model artifacts and data...")
    try:
        SeverityModelManager.get_instance().load()
        logger.info("Student A Severity Model loaded and ready.")
    except Exception as exc:
        logger.error("Warning: Could not pre-load Student A model at startup: %s", exc)

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
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=DEVELOPMENT_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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