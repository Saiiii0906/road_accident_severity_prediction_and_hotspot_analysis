"""
Student C - Graph Neural Network (GNN) Road Risk Schemas.

Defines request/response contracts for querying precomputed topological
accident risk predictions produced by Student C's RoadRiskGNN model.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .common import Coordinates, LightCondition, RoadSurfaceCondition, RoadType, WeatherCondition


class RiskLevel(str, Enum):
    """Relative risk category derived from GNN predicted_risk distribution."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class RoadRiskQueryRequest(BaseModel):
    """Filters for querying road segment risk predictions.

    Supports three query modes:
    1. Filter by specific `road_number`
    2. Spatial bounding box (`min_lat`, `max_lat`, `min_lon`, `max_lon`)
    3. Spatial center + radius (`center`, `radius_km`)

    At least one query mode must be provided.
    """

    road_number: Optional[int] = Field(
        None, ge=0, description="UK Road number to query (e.g. 1 for A1, 6 for A6)."
    )

    min_lat: Optional[float] = Field(None, description="Bounding box southern latitude edge.")
    max_lat: Optional[float] = Field(None, description="Bounding box northern latitude edge.")
    min_lon: Optional[float] = Field(None, description="Bounding box western longitude edge.")
    max_lon: Optional[float] = Field(None, description="Bounding box eastern longitude edge.")

    center: Optional[Coordinates] = Field(None, description="Center point for radius search.")
    radius_km: Optional[float] = Field(None, gt=0, le=1000, description="Search radius in kilometres.")

    min_risk: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Optional minimum predicted risk threshold (0.0 to 1.0)."
    )
    limit: int = Field(50, ge=1, le=500, description="Maximum number of segments to return.")

    @model_validator(mode="after")
    def validate_query_mode(self) -> "RoadRiskQueryRequest":
        bbox_fields = (self.min_lat, self.max_lat, self.min_lon, self.max_lon)
        bbox_given = all(f is not None for f in bbox_fields)
        bbox_partial = any(f is not None for f in bbox_fields) and not bbox_given
        radius_given = self.center is not None and self.radius_km is not None
        radius_partial = (self.center is not None or self.radius_km is not None) and not radius_given
        road_given = self.road_number is not None

        if bbox_partial:
            raise ValueError("min_lat, max_lat, min_lon, and max_lon must all be provided together")
        if radius_partial:
            raise ValueError("center and radius_km must both be provided together")
        if not bbox_given and not radius_given and not road_given:
            raise ValueError(
                "At least one query mode must be provided: 'road_number', bounding box, or 'center + radius_km'"
            )

        if bbox_given:
            if self.min_lat > self.max_lat:
                raise ValueError("min_lat must be less than or equal to max_lat")
            if self.min_lon > self.max_lon:
                raise ValueError("min_lon must be less than or equal to max_lon")

        return self


class RoadSegment(BaseModel):
    """A single topological road segment with GNN predicted risk."""

    model_config = ConfigDict(from_attributes=True)

    segment_id: int = Field(..., description="Unique edge index from Student C GNN graph.")
    road_number: int = Field(..., description="UK Road number classification.")
    start: Coordinates = Field(..., description="Start node coordinates (WGS84).")
    end: Coordinates = Field(..., description="End node coordinates (WGS84).")
    predicted_risk: float = Field(
        ..., ge=0.0, le=1.0, description="Continuous topological accident risk index (0.0 to 1.0)."
    )
    risk_category: str = Field(
        ..., description="Relative risk classification (Low, Moderate, High, Critical)."
    )


class RoadRiskPredictionResponse(BaseModel):
    """Result of a road risk query."""

    model_config = ConfigDict(from_attributes=True)

    segments: list[RoadSegment] = Field(..., description="Matched road segments ordered by predicted risk.")
    total_segments: int = Field(..., ge=0, description="Total number of returned road segments.")
    total_segments_matched: int = Field(
        ..., ge=0, description="Total number of segments matching filters before limit."
    )
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ==========================================
# Legacy / Compatibility schemas
# ==========================================

class RiskAssessmentRequest(BaseModel):
    """Legacy single location risk assessment request."""

    location: Coordinates
    road_type: RoadType
    speed_limit: int = Field(..., ge=0, le=70, description="Posted speed limit in mph.")
    weather_conditions: WeatherCondition
    road_surface_conditions: RoadSurfaceCondition
    light_conditions: LightCondition
    is_junction: bool = Field(False, description="Whether the location is at or near a junction.")
    assessed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ContributingFactor(BaseModel):
    factor: str = Field(..., description="Human-readable name of the risk factor.")
    weight: float = Field(..., ge=0.0, le=1.0, description="Relative contribution of this factor.")


class RiskAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    location: Coordinates
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Overall risk score, 0-100.")
    risk_level: RiskLevel
    contributing_factors: list[ContributingFactor] = Field(default_factory=list)
    model_version: str = Field(..., description="Identifier of the model that produced this score.")
    assessed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))