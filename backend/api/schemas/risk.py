from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from .common import Coordinates, LightCondition, RoadSurfaceCondition, RoadType, WeatherCondition


class RiskLevel(str, Enum):
    """Bucketed risk level derived from a continuous risk_score."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskAssessmentRequest(BaseModel):
    """A location and condition set to assess for general accident risk."""

    location: Coordinates
    road_type: RoadType
    speed_limit: int = Field(..., ge=0, le=70, description="Posted speed limit in mph.")
    weather_conditions: WeatherCondition
    road_surface_conditions: RoadSurfaceCondition
    light_conditions: LightCondition
    is_junction: bool = Field(
        False, description="Whether the location is at or near a junction."
    )
    assessed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Point in time the assessment applies to (affects time-of-day risk factors).",
    )


class ContributingFactor(BaseModel):
    """A single factor that contributed to the overall risk score, with its relative weight."""

    factor: str = Field(..., description="Human-readable name of the risk factor.")
    weight: float = Field(
        ..., ge=0.0, le=1.0, description="Relative contribution of this factor to the total score."
    )


class RiskAssessmentResponse(BaseModel):
    """Result of a risk assessment for a given location and condition set."""

    model_config = ConfigDict(from_attributes=True)

    location: Coordinates
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Overall risk score, 0-100.")
    risk_level: RiskLevel
    contributing_factors: list[ContributingFactor] = Field(
        default_factory=list,
        description="Factors driving the score, ordered by descending weight.",
    )
    model_version: str = Field(..., description="Identifier of the model that produced this score.")
    assessed_at: datetime = Field(default_factory=datetime.utcnow)