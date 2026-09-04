from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.schemas.report import (
    AIInfrastructureReportRequest,
    AIInfrastructureReportResponse,
)
from app.services.llm_report_service import LLMReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


def get_llm_report_service() -> LLMReportService:
    """Dependency provider for LLMReportService."""
    return LLMReportService()


LLMReportServiceDep = Annotated[LLMReportService, Depends(get_llm_report_service)]


@router.post(
    "/ai-infrastructure-report",
    response_model=AIInfrastructureReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate evidence-grounded AI Infrastructure decision-support report",
    description=(
        "Synthesizes deterministic model facts from Student A (Severity), "
        "Student B (DBSCAN Hotspots), and Student C (GNN Road Risk) into "
        "a structured, prioritized infrastructure and safety intervention report."
    ),
)
def generate_ai_infrastructure_report(
    request: AIInfrastructureReportRequest,
    service: LLMReportServiceDep,
) -> AIInfrastructureReportResponse:
    """Generate structured AI decision-support report from empirical model grounding."""
    return service.generate_report(request)