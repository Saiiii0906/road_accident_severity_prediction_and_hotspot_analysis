"""
Journey Safety Analysis API Route.

Exposes:
- POST /journey/analyze (and mounted at /api/journey/analyze)
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.journey import JourneyAnalyzeRequest, JourneyAnalyzeResponse
from app.services.geocoding_service import (
    GeocodingProviderError,
    GeocodingTimeoutError,
    LocationNotFoundError,
)
from app.services.journey_service import JourneyService
from app.services.routing_service import (
    RouteNotFoundError,
    RoutingProviderError,
    RoutingTimeoutError,
)

router = APIRouter(tags=["Journey Safety Analysis"])


def get_journey_service() -> JourneyService:
    """Dependency provider for JourneyService."""
    return JourneyService()


JourneyServiceDep = Annotated[JourneyService, Depends(get_journey_service)]


@router.post(
    "/journey/analyze",
    response_model=JourneyAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze safety profile for a journey",
    description=(
        "Comprehensive journey safety analysis evaluating origin/destination corridors, "
        "environmental context, and historical machine learning models (Students A, B, C)."
    ),
)
def analyze_journey(
    request: JourneyAnalyzeRequest,
    service: JourneyServiceDep,
) -> JourneyAnalyzeResponse:
    """Analyze safety risks and generate recommendations for a specified journey."""
    try:
        return service.analyze_journey(request)
    except LocationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except RouteNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except (GeocodingTimeoutError, RoutingTimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        ) from exc
    except (GeocodingProviderError, RoutingProviderError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
