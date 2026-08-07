from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.schemas.hotspot import HotspotAnalysisResponse, HotspotQueryRequest
from app.services.hotspot_service import HotspotService

router = APIRouter(prefix="/hotspots", tags=["Hotspot Analysis"])


def get_hotspot_service() -> HotspotService:
    """Dependency provider for HotspotService.

    This is the single place that decides which HotspotService
    implementation handles requests. Swapping the mock for a real
    clustering/ML-backed service later means changing this one function
    only.
    """
    return HotspotService()


HotspotServiceDep = Annotated[HotspotService, Depends(get_hotspot_service)]


@router.post(
    "/analyze",
    response_model=HotspotAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Identify accident hotspot clusters",
    description=(
        "Given an area (bounding box, or center + radius) and optional "
        "date range / minimum severity filters, return the accident "
        "clusters found within it, ranked and capped at `limit`. A "
        "request body is used instead of query parameters because the "
        "filter set is complex (mutually exclusive area definitions, "
        "cross-field date validation) and does not map cleanly onto a "
        "flat query string."
    ),
)
def analyze_hotspots(
    request: HotspotQueryRequest,
    service: HotspotServiceDep,
) -> HotspotAnalysisResponse:
    """Analyze accidents in the requested area and return hotspot clusters."""
    return service.analyze(request)