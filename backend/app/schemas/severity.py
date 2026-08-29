from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .common import (
    Coordinates,
    LightCondition,
    RoadSurfaceCondition,
    RoadType,
    Severity,
    UrbanOrRuralArea,
    WeatherCondition,
)


class SeverityPredictionRequest(BaseModel):
    """Conditions for a single accident, submitted for a severity prediction."""

    model_config = ConfigDict(extra="ignore")

    # Coordinates
    latitude: Optional[float] = Field(
        default=52.23759, description="Latitude in decimal degrees (WGS84)."
    )
    longitude: Optional[float] = Field(
        default=-1.362233, description="Longitude in decimal degrees (WGS84)."
    )
    location: Optional[Coordinates] = Field(
        default=None, description="Optional nested coordinates object."
    )

    # Date / Time
    accident_date: Optional[str] = Field(
        default=None, description="Accident date (YYYY-MM-DD)."
    )
    accident_time: Optional[str] = Field(
        default=None, description="Accident time (HH:MM)."
    )
    day_of_week: Optional[str] = Field(
        default=None, description="Day of week name (e.g., Friday)."
    )
    occurred_at: Optional[datetime] = Field(
        default=None, description="Timestamp when the accident occurred."
    )

    # Accident characteristics
    number_of_vehicles: int = Field(
        default=2, ge=1, le=50, description="Vehicles involved in the accident."
    )
    number_of_casualties: int = Field(
        default=1, ge=0, le=200, description="Casualties resulting from the accident."
    )
    speed_limit: int = Field(
        default=30, ge=0, le=120, description="Posted speed limit in mph/kph."
    )

    # Environmental and Road Conditions
    road_type: Optional[str] = Field(
        default="single_carriageway", description="Type of road."
    )
    road_surface_conditions: Optional[str] = Field(
        default="dry", description="Road surface condition."
    )
    road_surface: Optional[str] = Field(
        default=None, description="Alias for road_surface_conditions."
    )
    weather_conditions: Optional[str] = Field(
        default="fine", description="Weather conditions."
    )
    weather: Optional[str] = Field(
        default=None, description="Alias for weather_conditions."
    )
    light_conditions: Optional[str] = Field(
        default="daylight", description="Lighting conditions."
    )
    urban_or_rural_area: Optional[str] = Field(
        default="urban", description="Urban or rural area."
    )
    area_type: Optional[str] = Field(
        default=None, description="Alias for urban_or_rural_area."
    )

    # Junction Details
    is_junction: bool = Field(
        default=False, description="Whether the accident occurred at or near a junction."
    )
    junction_control: Optional[str] = Field(
        default="not_at_junction", description="Junction control type."
    )
    junction_detail: Optional[str] = Field(
        default="not_at_junction", description="Junction detail."
    )

    # Fleet / vehicle aggregates (optional overrides)
    age_of_vehicle_mean: Optional[float] = Field(
        default=None, description="Mean vehicle age."
    )
    traffic_density: Optional[str] = Field(
        default=None, description="Traffic density indicator."
    )

    @model_validator(mode="after")
    def populate_aliases_and_locations(self) -> "SeverityPredictionRequest":
        if self.location is not None:
            self.latitude = self.location.latitude
            self.longitude = self.location.longitude
        if self.road_surface and not self.road_surface_conditions:
            self.road_surface_conditions = self.road_surface
        if self.weather and not self.weather_conditions:
            self.weather_conditions = self.weather
        if self.area_type and not self.urban_or_rural_area:
            self.urban_or_rural_area = self.area_type
        return self


class SeverityClassProbability(BaseModel):
    """Predicted probability for a single severity class."""

    severity: Severity
    probability: float = Field(..., ge=0.0, le=1.0)


class SeverityPredictionResponse(BaseModel):
    """Model output for a single severity prediction."""

    model_config = ConfigDict(from_attributes=True)

    predicted_severity: Severity = Field(..., description="Most likely severity class.")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Probability assigned to predicted_severity."
    )
    class_probabilities: list[SeverityClassProbability] = Field(
        ..., description="Full probability distribution across all severity classes."
    )
    probabilities: dict[str, float] = Field(
        default_factory=dict, description="Dictionary mapping severity class to probability."
    )
    model_version: str = Field(
        default="student-a-rf-v1.0", description="Identifier of the model."
    )
    predicted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def sync_probabilities_dict(self) -> "SeverityPredictionResponse":
        if not self.probabilities and self.class_probabilities:
            self.probabilities = {
                item.severity.value if hasattr(item.severity, "value") else str(item.severity): item.probability
                for item in self.class_probabilities
            }
        return self


class BatchSeverityPredictionRequest(BaseModel):
    """Multiple accidents submitted for prediction in a single call."""

    accidents: list[SeverityPredictionRequest] = Field(..., min_length=1, max_length=500)


class BatchSeverityPredictionResponse(BaseModel):
    """Predictions returned in the same order as the submitted batch request."""

    model_config = ConfigDict(from_attributes=True)

    predictions: list[SeverityPredictionResponse]