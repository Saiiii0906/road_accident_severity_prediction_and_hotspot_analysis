from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.schemas.risk import RiskAssessmentRequest, RiskAssessmentResponse
from app.services.risk_service import RiskService

router = APIRouter(prefix="/risk", tags=["Risk Assessment"])


def get_risk_service() -> RiskService:
    """Dependency provider for RiskService.

    This is the single place that decides which RiskService
    implementation handles requests. Swapping the mock for a real
    ML-backed service later means changing this one function only.
    """
    return RiskService()


RiskServiceDep = Annotated[RiskService, Depends(get_risk_service)]


@router.post(
    "/assess",
    response_model=RiskAssessmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Assess accident risk for a location and condition set",
    description=(
        "Given a location, road type, speed limit, and current weather/"
        "surface/light conditions, return an overall risk score (0-100), "
        "a bucketed risk level, and the factors driving that score."
    ),
)
def assess_risk(
    request: RiskAssessmentRequest,
    service: RiskServiceDep,
) -> RiskAssessmentResponse:
    """Assess accident risk for the given location and conditions."""
    return service.assess(request)