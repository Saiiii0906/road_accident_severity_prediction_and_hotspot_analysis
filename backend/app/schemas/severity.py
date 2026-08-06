from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

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

    location: Coordinates
    road_type: RoadType
    speed_limit: int = Field(..., ge=0, le=70, description="Posted speed limit in mph.")
    weather_conditions: WeatherCondition
    road_surface_conditions: RoadSurfaceCondition
    light_conditions: LightCondition
    urban_or_rural_area: UrbanOrRuralArea
    number_of_vehicles: int = Field(..., ge=1, description="Vehicles involved in the accident.")
    is_junction: bool = Field(
        False, description="Whether the accident occurred at or near a junction."
    )
    occurred_at: datetime = Field(
        ..., description="Date and time the accident occurred, used to derive time-based features."
    )

    @field_validator("occurred_at")
    @classmethod
    def occurred_at_not_in_future(cls, value: datetime) -> datetime:
        if value > datetime.now(tz=value.tzinfo):
            raise ValueError("occurred_at cannot be in the future")
        return value


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
    model_version: str = Field(..., description="Identifier of the model that produced this prediction.")
    predicted_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("class_probabilities")
    @classmethod
    def probabilities_sum_to_one(
        cls, value: list[SeverityClassProbability]
    ) -> list[SeverityClassProbability]:
        total = sum(item.probability for item in value)
        if not 0.99 <= total <= 1.01:
            raise ValueError(f"class_probabilities must sum to ~1.0, got {total:.4f}")
        return value


class BatchSeverityPredictionRequest(BaseModel):
    """Multiple accidents submitted for prediction in a single call."""

    accidents: list[SeverityPredictionRequest] = Field(..., min_length=1, max_length=500)


class BatchSeverityPredictionResponse(BaseModel):
    """Predictions returned in the same order as the submitted batch request."""

    model_config = ConfigDict(from_attributes=True)

    predictions: list[SeverityPredictionResponse]