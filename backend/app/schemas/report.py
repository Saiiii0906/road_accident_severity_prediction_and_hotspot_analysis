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


# ==============================================================================
# AI Infrastructure Report Schemas (Structured LLM Contract)
# ==============================================================================


class PriorityLevel(str, Enum):
    """Presentation-only priority bands aligned with risk visual tokens."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class MatrixImpactEffort(str, Enum):
    """Standardized discrete scale for implementation matrix impact and effort."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class AIInfrastructureReportRequest(BaseModel):
    """Structured query filters for AI Infrastructure decision support report."""

    region: str = Field(
        default="all",
        description="Geographic region or district filter (e.g. 'all', 'north', 'central', 'south', 'east', 'west').",
    )
    period: str = Field(
        default="last_12_months",
        description="Time period filter (e.g. 'last_30_days', 'last_6_months', 'last_12_months', 'last_3_years').",
    )
    threshold: str = Field(
        default="moderate",
        description="Minimum priority threshold filter (e.g. 'low', 'moderate', 'high', 'critical').",
    )
    focus: str = Field(
        default="overall_safety",
        description="Intervention focus area (e.g. 'overall_safety', 'speed_reduction', 'junction_safety', 'pedestrian_cyclist').",
    )


class RiskSignalSchema(BaseModel):
    """Key quantitative or topological risk signal synthesized from model outputs."""

    id: str = Field(..., min_length=1, description="Unique identifier for signal.")
    label: str = Field(..., min_length=1, description="Human-readable signal label.")
    value: str = Field(..., min_length=1, description="Formatted summary metric or status value.")
    note: str = Field(..., min_length=1, description="Contextual note or scope description.")
    level: PriorityLevel = Field(..., description="Severity or priority level.")


class PriorityInterventionSchema(BaseModel):
    """Ranked engineering or policy infrastructure intervention."""

    id: str = Field(..., min_length=1, description="Unique identifier for intervention.")
    intervention: str = Field(..., min_length=1, description="Proposed engineering action.")
    signal: str = Field(..., min_length=1, description="Primary model trigger signal.")
    location: str = Field(..., min_length=1, description="Target corridor, road number, or hotspot location.")
    level: PriorityLevel = Field(..., description="Priority severity level.")
    rationale: str = Field(..., min_length=1, description="Empirical and model-grounded justification.")


class EvidenceItemSchema(BaseModel):
    """Empirical model-derived corroboration point."""

    id: str = Field(..., min_length=1, description="Unique identifier for evidence item.")
    signal: str = Field(..., min_length=1, description="Observed model or statistical signal.")
    value: str = Field(..., min_length=1, description="Measured signal value.")
    strength: int = Field(..., ge=0, le=100, description="Evidence confidence score on 0-100 scale.")
    relation: str = Field(..., min_length=1, description="Corroborating factor or relationship.")
    level: PriorityLevel = Field(..., description="Priority severity level.")


class RecommendationSchema(BaseModel):
    """Actionable tactical recommendation."""

    id: str = Field(..., min_length=1, description="Unique identifier for recommendation.")
    title: str = Field(..., min_length=1, description="Recommendation title.")
    why: str = Field(..., min_length=1, description="Underlying cause or problem statement.")
    objective: str = Field(..., min_length=1, description="Target safety outcome.")
    level: PriorityLevel = Field(..., description="Priority severity level.")
    supportingSignals: list[str] = Field(
        default_factory=list, description="Referenced signals corroborating recommendation."
    )


class PriorityMatrixRowSchema(BaseModel):
    """Impact versus delivery effort matrix mapping for proposed interventions."""

    id: str = Field(..., min_length=1, description="Unique identifier for priority row.")
    intervention: str = Field(..., min_length=1, description="Intervention action description.")
    priority: PriorityLevel = Field(..., description="Priority urgency level.")
    impact: MatrixImpactEffort = Field(..., description="Projected safety impact.")
    effort: MatrixImpactEffort = Field(..., description="Estimated delivery effort.")


class ReportSummarySchema(BaseModel):
    """Executive decision-support summary."""

    theme: str = Field(..., min_length=1, description="Strategic overview theme.")
    topIntervention: str = Field(..., min_length=1, description="Highest priority immediate intervention.")
    keySignal: str = Field(..., min_length=1, description="Dominant empirical risk signal.")
    nextStep: str = Field(..., min_length=1, description="Recommended operational next step.")


class ReportProvenanceSchema(BaseModel):
    """Grounding metadata tracking source artifacts."""

    student_a_model: str = Field(default="RandomForest_138_features", description="Student A severity model")
    student_b_hotspots: str = Field(default="DBSCAN_3705_clusters", description="Student B hotspot artifact")
    student_c_gnn: str = Field(default="GNN_13921_segments", description="Student C GNN risk artifact")
    grounded: bool = Field(default=True, description="Strictly grounded in empirical model outputs")


class AIInfrastructureReportResponse(BaseModel):
    """Complete machine-readable and validated structured report contract."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    generatedLabel: str = Field(
        default_factory=lambda: datetime.utcnow().strftime("Generated %d %b %Y, %H:%M UTC"),
        description="User-facing timestamp label.",
    )
    signals: list[RiskSignalSchema] = Field(
        ...,
        description="Key quantitative or topological risk signals synthesized from model outputs.",
    )
    interventions: list[PriorityInterventionSchema] = Field(
        ...,
        description="Ranked engineering or policy infrastructure interventions tied to specific evidence.",
    )
    evidence: list[EvidenceItemSchema] = Field(
        ...,
        description="Empirical model-derived corroboration points.",
    )
    recommendations: list[RecommendationSchema] = Field(
        ...,
        description="Actionable tactical recommendations.",
    )
    priorities: list[PriorityMatrixRowSchema] = Field(
        ...,
        description="Impact versus delivery effort matrix mapping for proposed interventions.",
    )
    summary: ReportSummarySchema
    provenance: ReportProvenanceSchema | None = Field(
        default_factory=ReportProvenanceSchema,
        description="Model grounding provenance metadata.",
    )