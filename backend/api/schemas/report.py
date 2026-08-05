from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .common import SeverityBreakdown


class ReportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"


class ReportFilterParams(BaseModel):
    """Date and region filters shared by both the inline summary and export endpoints."""

    date_from: date = Field(..., description="Start of the reporting period, inclusive.")
    date_to: date = Field(..., description="End of the reporting period, inclusive.")
    local_authority: str | None = Field(
        None, description="Restrict the report to a single local authority district."
    )

    @model_validator(mode="after")
    def date_range_is_ordered(self) -> "ReportFilterParams":
        if self.date_from > self.date_to:
            raise ValueError("date_from must be on or before date_to")
        return self


class TrendPoint(BaseModel):
    """Accident counts for a single period, used to build a trend series."""

    period_start: date
    total_accidents: int = Field(..., ge=0)
    severity_breakdown: SeverityBreakdown


class ReportSummaryResponse(BaseModel):
    """Aggregate accident statistics for the requested filters."""

    model_config = ConfigDict(from_attributes=True)

    filters: ReportFilterParams
    total_accidents: int = Field(..., ge=0)
    severity_breakdown: SeverityBreakdown
    top_contributing_factors: list[str] = Field(
        default_factory=list, description="Most frequently recorded contributing factors, ranked."
    )
    trend: list[TrendPoint] = Field(
        default_factory=list, description="Accident counts broken down by sub-period, for charting."
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ReportExportRequest(BaseModel):
    """Request to generate a downloadable report file rather than an inline response."""

    filters: ReportFilterParams
    format: ReportFormat = Field(ReportFormat.CSV, description="Output file format.")


class ReportExportResponse(BaseModel):
    """Reference to a generated report file. The file itself is served separately —
    this schema only carries the pointer and metadata."""

    model_config = ConfigDict(from_attributes=True)

    report_id: str = Field(..., description="Identifier used to retrieve the generated file.")
    format: ReportFormat
    download_url: str = Field(..., description="URL the client can use to download the file.")
    expires_at: datetime | None = Field(
        None, description="If set, the download_url will stop working after this time."
    )