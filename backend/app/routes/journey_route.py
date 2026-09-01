"""
Journey Safety Analysis API Route.

Exposes:
- POST /journey/analyze (and mounted at /api/journey/analyze)
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.schemas.journey import JourneyAnalyzeRequest, JourneyAnalyzeResponse
from app.services.journey_service import JourneyService

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
    return service.analyze_journey(request)

