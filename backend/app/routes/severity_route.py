from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.schemas.severity import (
    BatchSeverityPredictionRequest,
    BatchSeverityPredictionResponse,
    SeverityPredictionRequest,
    SeverityPredictionResponse,
)
from app.services.severity_service import SeverityService

router = APIRouter(prefix="/severity", tags=["Severity Prediction"])


def get_severity_service() -> SeverityService:
    """Dependency provider for SeverityService."""
    return SeverityService()


SeverityServiceDep = Annotated[SeverityService, Depends(get_severity_service)]


@router.post(
    "/predict",
    response_model=SeverityPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict the severity of a single accident",
    description=(
        "Given a single accident's location and conditions (road type, "
        "weather, surface, lighting, etc.), return the predicted severity "
        "class along with the full class probability distribution."
    ),
)
def predict_severity(
    request: SeverityPredictionRequest,
    service: SeverityServiceDep,
) -> SeverityPredictionResponse:
    """Predict severity for one accident."""
    return service.predict(request)


@router.post(
    "/predict-batch",
    response_model=BatchSeverityPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict the severity of multiple accidents in one call",
    description=(
        "Given a batch of up to 500 accidents, return one severity "
        "prediction per accident, in the same order they were submitted."
    ),
)
def predict_severity_batch(
    request: BatchSeverityPredictionRequest,
    service: SeverityServiceDep,
) -> BatchSeverityPredictionResponse:
    """Predict severity for a batch of accidents."""
    return service.predict_batch(request)