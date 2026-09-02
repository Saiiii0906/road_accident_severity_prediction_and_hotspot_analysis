"""
Journey Safety Analysis Schemas.

Defines the data contract for multi-source journey safety evaluation,
combining routing, live environmental context, historical ML model
evidence (Students A, B, C), and grounded Gemini synthesis.
"""

from datetime import date, datetime, time, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DataAvailabilityStatus(str, Enum):
    """Lifecycle status of a data provider or analytical subsystem."""

    PENDING = "pending"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


# ==============================================================================
# Request Schemas
# ==============================================================================


class JourneyAnalyzeRequest(BaseModel):
    """Request payload for journey safety analysis."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "source": "London Victoria Station",
                "destination": "Heathrow Airport Terminal 5",
                "travel_date": "2026-09-02",
                "travel_time": "14:30",
            }
        },
    )

    source: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Origin address, landmark, or location query.",
    )
    destination: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Destination address, landmark, or location query.",
    )
    travel_date: date = Field(
        ...,
        description="Planned departure date (YYYY-MM-DD).",
    )
    travel_time: time = Field(
        ...,
        description="Planned departure time (HH:MM or HH:MM:SS).",
    )

    @field_validator("source", "destination")
    @classmethod
    def validate_non_empty_string(cls, value: str) -> str:
        stripped = value.strip()
        if len(stripped) < 2:
            raise ValueError("Location string must contain at least 2 non-whitespace characters.")
        return stripped


# ==============================================================================
# Response Sub-Schemas
# ==============================================================================


class JourneyDetailsSchema(BaseModel):
    """User-requested journey parameters."""

    source: str = Field(..., description="Origin location query.")
    destination: str = Field(..., description="Destination location query.")
    travel_date: str = Field(..., description="Planned travel date (ISO format).")
    travel_time: str = Field(..., description="Planned travel time (HH:MM).")


class RouteSegmentSchema(BaseModel):
    """Corridor or road segment belonging to the evaluated route."""

    segment_id: Optional[str] = Field(None, description="Identifier of the road segment.")
    name: Optional[str] = Field(None, description="Road designation or name (e.g. 'A4', 'M4').")
    length_km: Optional[float] = Field(None, ge=0.0, description="Segment length in kilometers.")


class GeocodedLocationSchema(BaseModel):
    """Resolved geographic coordinate and canonical address label."""

    latitude: float = Field(..., description="Latitude in decimal degrees.")
    longitude: float = Field(..., description="Longitude in decimal degrees.")
    display_name: str = Field(..., description="Canonical location label returned by geocoder.")


class RouteGeometrySchema(BaseModel):
    """GeoJSON LineString geometry of the traversed route."""

    type: str = Field("LineString", description="GeoJSON geometry type.")
    coordinates: list[list[float]] = Field(
        default_factory=list,
        description="Array of [longitude, latitude] coordinate pairs along the route.",
    )


class RouteInfoSchema(BaseModel):
    """Route alignment, topological geometric metadata, and resolved endpoints."""

    status: DataAvailabilityStatus = Field(
        DataAvailabilityStatus.PENDING,
        description="Status of routing provider computation.",
    )
    source: Optional[GeocodedLocationSchema] = Field(
        None, description="Resolved origin coordinates and display name."
    )
    destination: Optional[GeocodedLocationSchema] = Field(
        None, description="Resolved destination coordinates and display name."
    )
    distance_km: Optional[float] = Field(None, ge=0.0, description="Total journey distance in km.")
    duration_minutes: Optional[float] = Field(
        None, ge=0.0, description="Estimated traversal duration in minutes."
    )
    geometry: Optional[RouteGeometrySchema] = Field(
        None, description="GeoJSON LineString route geometry."
    )
    provider: Optional[str] = Field(None, description="Routing engine used (e.g. 'OSRM').")
    segments: list[RouteSegmentSchema] = Field(
        default_factory=list,
        description="Sequence of traversed road segments.",
    )


class TrafficContextSchema(BaseModel):
    """Real-time or forecasted traffic conditions along the corridor."""

    congestion_level: Optional[str] = Field(None, description="Congestion indicator (e.g. 'low', 'moderate', 'severe').")
    delay_minutes: Optional[float] = Field(None, ge=0.0, description="Estimated delay caused by traffic.")
    description: Optional[str] = Field(None, description="Traffic overview note.")


class WeatherContextSchema(BaseModel):
    """Real-time or forecasted atmospheric conditions along the corridor."""

    condition: Optional[str] = Field(None, description="Atmospheric state (e.g. 'Clear', 'Rain', 'Fog').")
    temperature_c: Optional[float] = Field(None, description="Ambient temperature in degrees Celsius.")
    visibility: Optional[str] = Field(None, description="Visibility classification.")
    precipitation_risk: Optional[str] = Field(None, description="Precipitation hazard level.")


class IncidentContextSchema(BaseModel):
    """Active road incident or hazard detected along the corridor."""

    incident_id: str = Field(..., description="Unique incident identifier.")
    description: str = Field(..., description="Description of hazard or obstruction.")
    severity: Optional[str] = Field(None, description="Incident severity level.")


class LiveContextSchema(BaseModel):
    """Real-time environmental and operational context."""

    status: DataAvailabilityStatus = Field(
        DataAvailabilityStatus.PENDING,
        description="Status of live environmental and traffic providers.",
    )
    traffic: Optional[TrafficContextSchema] = Field(None, description="Live traffic context.")
    weather: Optional[WeatherContextSchema] = Field(None, description="Live atmospheric context.")
    incidents: list[IncidentContextSchema] = Field(
        default_factory=list, description="Active incidents reported on route."
    )


class HistoricalSeverityEvidenceSchema(BaseModel):
    """Student A RandomForest baseline severity estimation for the journey conditions."""

    predicted_severity: Optional[str] = Field(None, description="Model-predicted severity class.")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Prediction confidence score.")
    probabilities: Optional[dict[str, float]] = Field(
        None, description="Class probabilities across slight, serious, fatal."
    )


class HistoricalHotspotEvidenceSchema(BaseModel):
    """Student B DBSCAN spatial cluster exposure along the journey corridor."""

    hotspots_on_route: int = Field(0, ge=0, description="Number of historical DBSCAN clusters intersected.")
    cluster_ids: list[str] = Field(default_factory=list, description="Identifiers of intersected clusters.")
    highest_cluster_density: Optional[int] = Field(None, description="Peak accident count among intersected clusters.")


class HistoricalRiskEvidenceSchema(BaseModel):
    """Student C RoadRiskGNN structural risk scoring along traversed segments."""

    critical_segments_count: int = Field(0, ge=0, description="Count of critical GNN risk segments intersected.")
    average_gnn_risk: Optional[float] = Field(None, description="Mean topological risk score across route.")
    high_risk_corridors: list[str] = Field(default_factory=list, description="Key high-risk corridor segments.")


class HistoricalEvidenceSchema(BaseModel):
    """Consolidated empirical analytical evidence from Students A, B, and C."""

    status: DataAvailabilityStatus = Field(
        DataAvailabilityStatus.PENDING,
        description="Status of historical model inference pipeline.",
    )
    student_a: Optional[HistoricalSeverityEvidenceSchema] = Field(
        None, description="Student A severity model evidence."
    )
    student_b: Optional[HistoricalHotspotEvidenceSchema] = Field(
        None, description="Student B DBSCAN hotspot evidence."
    )
    student_c: Optional[HistoricalRiskEvidenceSchema] = Field(
        None, description="Student C GNN network risk evidence."
    )


class SafetyAssessmentSchema(BaseModel):
    """Synthesized deterministic safety classification for the journey."""

    status: DataAvailabilityStatus = Field(
        DataAvailabilityStatus.PENDING,
        description="Status of safety assessment computation.",
    )
    overall_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Overall safety index (0-100).")
    level: Optional[str] = Field(None, description="Safety category (e.g. 'Low Risk', 'Moderate Risk', 'Critical Risk').")
    summary: Optional[str] = Field(None, description="Executive safety overview.")


class LLMSynthesisSchema(BaseModel):
    """Multimodal generative safety explanation and actionable recommendations."""

    status: DataAvailabilityStatus = Field(
        DataAvailabilityStatus.PENDING,
        description="Status of LLM synthesis pipeline.",
    )
    summary: Optional[str] = Field(None, description="Executive AI narrative summary.")
    recommendations: list[str] = Field(default_factory=list, description="Actionable driver or dispatcher precautions.")


class JourneyProvenanceSchema(BaseModel):
    """Data provenance and provider connectivity flags for the journey evaluation."""

    route_provider: Optional[str] = Field(None, description="Routing engine used (e.g. 'OSRM', 'Mapbox', None).")
    live_data_available: bool = Field(False, description="Whether live weather/traffic feeds were connected.")
    historical_data_available: bool = Field(False, description="Whether historical model grounding was connected.")
    student_a_used: bool = Field(False, description="Whether Student A severity model was invoked.")
    student_b_used: bool = Field(False, description="Whether Student B DBSCAN cluster lookup was invoked.")
    student_c_used: bool = Field(False, description="Whether Student C RoadRiskGNN lookup was invoked.")
    gemini_used: bool = Field(False, description="Whether Gemini LLM synthesis was invoked.")
    analysis_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the analysis generation.",
    )


# ==============================================================================
# Top-Level Response Schema
# ==============================================================================


class JourneyAnalyzeResponse(BaseModel):
    """Comprehensive Journey Safety Analysis evaluation response."""

    journey: JourneyDetailsSchema = Field(..., description="Echoed input journey parameters.")
    route: RouteInfoSchema = Field(..., description="Route distance, duration, and segment alignment.")
    live_context: LiveContextSchema = Field(..., description="Real-time traffic, weather, and hazard context.")
    historical_evidence: HistoricalEvidenceSchema = Field(
        ..., description="Historical model predictions from Students A, B, and C."
    )
    safety_assessment: SafetyAssessmentSchema = Field(
        ..., description="Synthesized safety classification."
    )
    llm_synthesis: LLMSynthesisSchema = Field(
        ..., description="Explainable AI safety synthesis."
    )
    provenance: JourneyProvenanceSchema = Field(
        ..., description="Provider connectivity and pipeline provenance metadata."
    )

