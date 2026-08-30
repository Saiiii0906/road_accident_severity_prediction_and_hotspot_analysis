from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.schemas.report import (
    AIInfrastructureReportRequest,
    AIInfrastructureReportResponse,
    ReportExportRequest,
    ReportExportResponse,
    ReportFilterParams,
    ReportSummaryResponse,
)
from app.services.llm_report_service import LLMReportService
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


def get_report_service() -> ReportService:
    """Dependency provider for legacy ReportService."""
    return ReportService()


ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]


def get_llm_report_service() -> LLMReportService:
    """Dependency provider for LLMReportService."""
    return LLMReportService()


LLMReportServiceDep = Annotated[LLMReportService, Depends(get_llm_report_service)]


def get_report_filters(
    date_from: Annotated[date, Query(description="Start of the reporting period, inclusive.")],
    date_to: Annotated[date, Query(description="End of the reporting period, inclusive.")],
    local_authority: Annotated[
        str | None,
        Query(description="Restrict the report to a single local authority district."),
    ] = None,
) -> ReportFilterParams:
    """Build and validate ReportFilterParams from individual query parameters."""
    try:
        return ReportFilterParams(
            date_from=date_from, date_to=date_to, local_authority=local_authority
        )
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


ReportFiltersQuery = Annotated[ReportFilterParams, Depends(get_report_filters)]


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


@router.get(
    "/summary",
    response_model=ReportSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get aggregate accident statistics for a date range",
    description=(
        "Return total accident counts, a severity breakdown, top "
        "contributing factors, and a trend series for the given date "
        "range, optionally restricted to a single local authority."
    ),
)
def get_report_summary(
    filters: ReportFiltersQuery,
    service: ReportServiceDep,
) -> ReportSummaryResponse:
    """Return an aggregate accident report for the requested filters."""
    return service.get_summary(filters)


@router.post(
    "/export",
    response_model=ReportExportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a downloadable report file",
    description=(
        "Generate a report file (CSV, JSON, or PDF) for the given filters "
        "and return a reference to it, including a download URL. This "
        "creates a new report resource, so it responds with 201 Created "
        "and a Location header pointing at the download URL."
    ),
)
def export_report(
    request: ReportExportRequest,
    service: ReportServiceDep,
    response: Response,
) -> ReportExportResponse:
    """Generate a downloadable report file for the requested filters."""
    result = service.export(request)
    response.headers["Location"] = result.download_url
    return result