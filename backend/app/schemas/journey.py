"""
Journey Safety Analysis Schemas.

Defines the data contract for multi-source journey safety evaluation,
combining routing, live environmental context, historical ML model
evidence (Students A, B, C), and grounded Gemini synthesis.
"""

from datetime import date, datetime, time, timezone
from enum import Enum
from typing import Any, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class DataAvailabilityStatus(str, Enum):
    """Lifecycle status of a data provider or analytical subsystem."""

    PENDING = "pending"
    AVAILABLE = "available"
    PARTIAL = "partial"
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

    status: DataAvailabilityStatus = Field(
        DataAvailabilityStatus.AVAILABLE,
        description="Status of traffic provider computation.",
    )
    congestion_level: Optional[str] = Field(None, description="Congestion indicator (e.g. 'low', 'moderate', 'severe').")
    delay_minutes: Optional[float] = Field(None, ge=0.0, description="Estimated delay caused by traffic.")
    description: Optional[str] = Field(None, description="Traffic overview note.")
    corridor_monitored: Optional[str] = Field(None, description="Specific monitored road corridor evaluated (e.g. 'A4').")


class WeatherContextSchema(BaseModel):
    """Real-time or forecasted atmospheric conditions along the corridor."""

    status: DataAvailabilityStatus = Field(
        DataAvailabilityStatus.AVAILABLE,
        description="Status of weather provider computation.",
    )
    condition: Optional[str] = Field(None, description="Atmospheric state (e.g. 'Clear', 'Rain', 'Fog').")
    temperature_c: Optional[float] = Field(None, description="Ambient temperature in degrees Celsius.")
    precipitation_probability: Optional[int] = Field(None, ge=0, le=100, description="Precipitation probability in percent.")
    precipitation_mm: Optional[float] = Field(None, ge=0.0, description="Precipitation amount in mm.")
    wind_speed_kmh: Optional[float] = Field(None, ge=0.0, description="Wind speed in km/h.")
    visibility: Optional[str] = Field(None, description="Visibility classification (e.g. 'Good', 'Moderate', 'Poor').")
    precipitation_risk: Optional[str] = Field(None, description="Precipitation hazard level.")
    queried_time: Optional[str] = Field(None, description="Target timestamp queried (ISO format).")
    location_name: Optional[str] = Field(None, description="Representative location or coordinates queried.")


class IncidentContextSchema(BaseModel):
    """Active road incident or hazard detected along the corridor."""

    incident_id: str = Field(..., description="Unique incident identifier.")
    description: str = Field(..., description="Description of hazard or obstruction.")
    severity: Optional[str] = Field(None, description="Incident severity level.")
    category: Optional[str] = Field(None, description="Disruption category (e.g. 'Works', 'Accident', 'Hazard').")
    location: Optional[str] = Field(None, description="Location text.")


class LiveContextProvidersSchema(BaseModel):
    """Names of upstream providers consulted for live context."""

    weather: Optional[str] = Field(None, description="Weather provider name or None.")
    traffic: Optional[str] = Field(None, description="Traffic provider name or None.")
    incidents: Optional[str] = Field(None, description="Incidents provider name or None.")


class LiveContextSchema(BaseModel):
    """Real-time environmental and operational context."""

    status: DataAvailabilityStatus = Field(
        DataAvailabilityStatus.PENDING,
        description="Status of live environmental and traffic providers.",
    )
    weather: Optional[WeatherContextSchema] = Field(None, description="Live atmospheric context.")
    traffic: Optional[TrafficContextSchema] = Field(None, description="Live traffic context.")
    incidents: list[IncidentContextSchema] = Field(
        default_factory=list, description="Active incidents reported on route."
    )
    providers: Optional[LiveContextProvidersSchema] = Field(
        None, description="Live providers consulted."
    )


class HistoricalCoverageSchema(BaseModel):
    """Geographic applicability and coverage check for historical models."""

    supported: bool = Field(..., description="Whether the journey intersects supported historical coverage.")
    status: DataAvailabilityStatus = Field(
        ..., description="Coverage availability classification (available, partial, unavailable)."
    )
    region: str = Field(
        "Great Britain (UK)", description="Geographic region covered by historical datasets."
    )
    reason: Optional[str] = Field(None, description="Explanation of coverage status.")


class CorridorMatchingMetadataSchema(BaseModel):
    """Spatial matching parameters and methodology metadata."""

    corridor_radius_m: float = Field(..., ge=0.0, description="Corridor buffer radius in meters.")
    method: str = Field(
        "Spherical BallTree (Haversine distance from route geometry)",
        description="Spatial matching algorithm employed.",
    )
    route_waypoints_count: int = Field(0, ge=0, description="Count of route waypoints evaluated.")


class MatchedHotspotSchema(BaseModel):
    """Historical DBSCAN accident cluster intersected by the journey corridor."""

    cluster_id: int = Field(..., description="DBSCAN cluster identifier.")
    latitude: float = Field(..., description="Cluster centroid latitude.")
    longitude: float = Field(..., description="Cluster centroid longitude.")
    total_accidents: int = Field(..., ge=1, description="Total historical accident count in cluster.")
    fatal_count: int = Field(0, ge=0, description="Fatal accident count in cluster.")
    serious_count: int = Field(0, ge=0, description="Serious accident count in cluster.")
    slight_count: int = Field(0, ge=0, description="Slight accident count in cluster.")
    dominant_severity: Optional[str] = Field(None, description="Most frequent severity level.")
    dominant_weather: Optional[str] = Field(None, description="Most frequent atmospheric condition.")
    dominant_road_type: Optional[str] = Field(None, description="Most frequent carriageway type.")
    average_speed: Optional[float] = Field(None, description="Average posted speed limit in mph.")
    average_casualties: Optional[float] = Field(None, description="Average casualty count per crash.")
    peak_hour: Optional[float] = Field(None, description="Peak crash occurrence hour (0-23).")
    distance_to_route_m: float = Field(..., ge=0.0, description="Distance from cluster centroid to nearest route waypoint in meters.")


class MatchedSegmentSchema(BaseModel):
    """Historical GNN road network segment intersected by the journey corridor."""

    edge_id: int = Field(..., description="Unique graph edge identifier.")
    road_number: int = Field(..., description="UK Road number designation (e.g. 4 for A4).")
    start_lat: float = Field(..., description="Segment start latitude.")
    start_lon: float = Field(..., description="Segment start longitude.")
    end_lat: float = Field(..., description="Segment end latitude.")
    end_lon: float = Field(..., description="Segment end longitude.")
    predicted_risk: float = Field(..., ge=0.0, le=1.0, description="Continuous GNN predicted risk score.")
    risk_category: str = Field(..., description="Categorized risk (Critical, High, Moderate, Low).")
    distance_to_route_m: float = Field(..., ge=0.0, description="Distance from segment midpoint to nearest route waypoint in meters.")


class HistoricalSeverityEvidenceSchema(BaseModel):
    """Student A RandomForest baseline severity estimation for the journey conditions."""

    status: DataAvailabilityStatus = Field(
        DataAvailabilityStatus.UNAVAILABLE,
        description="Status of Student A applicability for route corridor.",
    )
    predicted_severity: Optional[str] = Field(None, description="Model-predicted severity class.")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Prediction confidence score.")
    probabilities: Optional[dict[str, float]] = Field(
        None, description="Class probabilities across slight, serious, fatal."
    )
    reason: Optional[str] = Field(
        None, description="Reason why Student A is or is not applicable to route corridor traversal."
    )


class HistoricalHotspotEvidenceSchema(BaseModel):
    """Student B DBSCAN spatial cluster exposure along the journey corridor."""

    status: DataAvailabilityStatus = Field(
        DataAvailabilityStatus.AVAILABLE,
        description="Status of Student B DBSCAN corridor lookup.",
    )
    hotspots_on_route: int = Field(0, ge=0, description="Number of historical DBSCAN clusters intersected.")
    total_historical_accidents: int = Field(0, ge=0, description="Sum of accidents across intersected clusters.")
    cluster_ids: list[str] = Field(default_factory=list, description="Identifiers of intersected clusters.")
    highest_cluster_density: Optional[int] = Field(None, description="Peak accident count among intersected clusters.")
    matched_hotspots: list[MatchedHotspotSchema] = Field(
        default_factory=list, description="Top matched DBSCAN accident clusters along the corridor."
    )
    description: Optional[str] = Field(None, description="Summary interpretation note.")


class HistoricalRiskEvidenceSchema(BaseModel):
    """Student C RoadRiskGNN structural risk scoring along traversed segments."""

    status: DataAvailabilityStatus = Field(
        DataAvailabilityStatus.AVAILABLE,
        description="Status of Student C RoadRiskGNN corridor lookup.",
    )
    segments_on_route: int = Field(0, ge=0, description="Total GNN segments intersected by route corridor.")
    critical_segments_count: int = Field(0, ge=0, description="Count of critical GNN risk segments intersected (risk >= 0.10).")
    high_risk_segments_count: int = Field(0, ge=0, description="Count of high GNN risk segments intersected (risk >= 0.08).")
    average_gnn_risk: Optional[float] = Field(None, description="Mean topological risk score across matched segments.")
    peak_gnn_risk: Optional[float] = Field(None, description="Maximum topological risk score across matched segments.")
    high_risk_corridors: list[str] = Field(default_factory=list, description="Key high-risk corridor road designations.")
    matched_segments: list[MatchedSegmentSchema] = Field(
        default_factory=list, description="Top matched GNN road segments ranked by predicted risk."
    )
    description: Optional[str] = Field(None, description="Summary interpretation note.")


class HistoricalEvidenceSchema(BaseModel):
    """Consolidated empirical analytical evidence from Students A, B, and C."""

    status: DataAvailabilityStatus = Field(
        DataAvailabilityStatus.PENDING,
        description="Status of historical model inference pipeline.",
    )
    coverage: Optional[HistoricalCoverageSchema] = Field(
        None, description="Geographic coverage assessment of route."
    )
    matching: Optional[CorridorMatchingMetadataSchema] = Field(
        None, description="Corridor buffer and matching metadata."
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
    summary: Optional[str] = Field(None, description="Overall historical evidence synthesis.")


class SafetyKeyFactorSchema(BaseModel):
    """A distinct environmental, operational, or empirical risk factor identified on route."""

    factor: str = Field(..., description="Factor identifier (e.g. 'live_traffic', 'historical_gnn_risk').")
    title: str = Field(..., description="Human-readable title.")
    severity: str = Field(
        ..., description="Factor severity tier ('critical', 'high', 'moderate', 'low', 'advisory', 'informational', 'unknown')."
    )
    description: str = Field(..., description="Evidence-grounded description.")
    source: str = Field(..., description="Data provider or model originating this factor.")


class SafetyEvidenceItemSchema(BaseModel):
    """An itemized empirical metric with transparent interpretation."""

    source: str = Field(..., description="Data provider or analytical model (e.g. 'Student B DBSCAN', 'TfL').")
    metric: str = Field(..., description="Metric name.")
    value: str = Field(..., description="Metric value represented as formatted text.")
    interpretation: str = Field(..., description="Factual interpretation of what this value signifies.")


class SafetyDataCoverageSchema(BaseModel):
    """Subsystem availability state for the assessment."""

    route: DataAvailabilityStatus = Field(..., description="Routing corridor availability.")
    weather: DataAvailabilityStatus = Field(..., description="Atmospheric context availability.")
    traffic: DataAvailabilityStatus = Field(..., description="Traffic flow monitoring availability.")
    incidents: DataAvailabilityStatus = Field(..., description="Incident & hazard feed availability.")
    historical: DataAvailabilityStatus = Field(..., description="Historical model grounding availability.")


class SafetyAssessmentSchema(BaseModel):
    """Synthesized deterministic safety classification and evidence breakdown for the journey."""

    status: DataAvailabilityStatus = Field(
        DataAvailabilityStatus.PENDING,
        description="Status of safety assessment computation.",
    )
    overall_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Composite numerical safety score. Remains null as no defensible composite weighting formula is defined in the project.",
    )
    level: Optional[str] = Field(
        None,
        description="Route-wide safety level. Remains null to avoid arbitrary thresholding across heterogeneous signals.",
    )
    summary: Optional[str] = Field(None, description="Executive deterministic synthesis of verified factors.")
    key_factors: list[SafetyKeyFactorSchema] = Field(
        default_factory=list, description="Identified operational and empirical safety factors."
    )
    supporting_evidence: list[SafetyEvidenceItemSchema] = Field(
        default_factory=list, description="Itemized evidentiary metrics with honest interpretations."
    )
    data_coverage: Optional[SafetyDataCoverageSchema] = Field(
        None, description="Subsystem data availability breakdown."
    )
    limitations: list[str] = Field(
        default_factory=list, description="Explicit data constraints, boundary limits, and non-applicability notes."
    )


LLMKeyFindingSeverity = Literal[
    "critical",
    "high",
    "moderate",
    "low",
    "unknown",
]


class LLMKeyFindingSchema(BaseModel):
    """A synthesized key risk or operational finding grounded in multi-source evidence."""

    title: str = Field(
        ...,
        description="Concise finding headline.",
    )
    description: str = Field(
        ...,
        description="Evidence-grounded finding explanation.",
    )
    severity: LLMKeyFindingSeverity = Field(
        ...,
        description="Severity level ('critical', 'high', 'moderate', 'low', 'unknown').",
    )
    evidence_sources: list[str] = Field(
        default_factory=list,
        description="Data sources or models supporting this finding.",
    )


class LLMRecommendationSchema(BaseModel):
    """An actionable, evidence-linked safety precaution or navigation recommendation."""

    action: str = Field(..., description="Actionable safety precaution or navigation guidance.")
    reason: str = Field(..., description="Empirical rationale grounded in observed evidence.")
    evidence_sources: list[str] = Field(
        default_factory=list, description="Data sources or models backing this recommendation."
    )


class LLMSynthesisSchema(BaseModel):
    """Multimodal generative safety explanation and actionable recommendations."""

    status: DataAvailabilityStatus = Field(
        DataAvailabilityStatus.PENDING,
        description="Status of LLM synthesis pipeline ('available', 'partial', 'unavailable', 'pending').",
    )
    headline: Optional[str] = Field(None, description="Executive takeaway headline.")
    summary: Optional[str] = Field(None, description="Executive AI narrative summary.")
    key_findings: list[LLMKeyFindingSchema] = Field(
        default_factory=list, description="Key empirical and environmental risk findings."
    )
    recommendations: list[LLMRecommendationSchema] = Field(
        default_factory=list, description="Actionable driver or dispatcher precautions."
    )
    limitations: list[str] = Field(
        default_factory=list, description="Explicit notes on missing data feeds or boundary constraints."
    )


class JourneyProvenanceSchema(BaseModel):
    """Data provenance and provider connectivity flags for the journey evaluation."""

    route_provider: Optional[str] = Field(None, description="Routing engine used (e.g. 'OSRM', 'Mapbox', None).")
    weather_provider: Optional[str] = Field(None, description="Weather provider used (e.g. 'Open-Meteo', None).")
    traffic_provider: Optional[str] = Field(None, description="Traffic provider used (e.g. 'TfL', None).")
    incident_provider: Optional[str] = Field(None, description="Road incident provider used (e.g. 'TfL', None).")
    live_data_available: bool = Field(False, description="Whether live weather/traffic feeds were connected.")
    historical_data_available: bool = Field(False, description="Whether historical model grounding was connected.")
    historical_coverage_region: Optional[str] = Field(None, description="Region covered by historical data.")
    corridor_radius_m: Optional[float] = Field(None, description="Corridor buffer radius in meters.")
    matched_hotspots_count: int = Field(0, description="Count of matched DBSCAN clusters.")
    matched_segments_count: int = Field(0, description="Count of matched GNN segments.")
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

