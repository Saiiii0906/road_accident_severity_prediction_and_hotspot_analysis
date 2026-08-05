from enum import Enum

from pydantic import BaseModel, ConfigDict, Field
_UK_MIN_LATITUDE = 49.5
_UK_MAX_LATITUDE = 61.0
_UK_MIN_LONGITUDE = -8.5
_UK_MAX_LONGITUDE = 2.0


class Severity(str, Enum):
    """Accident severity classes, ordered from least to most severe."""

    SLIGHT = "slight"
    SERIOUS = "serious"
    FATAL = "fatal"


class WeatherCondition(str, Enum):
    FINE = "fine"
    RAINING = "raining"
    SNOWING = "snowing"
    FOG_OR_MIST = "fog_or_mist"
    OTHER = "other"


class RoadSurfaceCondition(str, Enum):
    DRY = "dry"
    WET_OR_DAMP = "wet_or_damp"
    SNOW = "snow"
    ICE = "ice"
    OTHER = "other"


class LightCondition(str, Enum):
    DAYLIGHT = "daylight"
    DARKNESS_LIT = "darkness_lit"
    DARKNESS_UNLIT = "darkness_unlit"


class RoadType(str, Enum):
    SINGLE_CARRIAGEWAY = "single_carriageway"
    DUAL_CARRIAGEWAY = "dual_carriageway"
    ROUNDABOUT = "roundabout"
    ONE_WAY_STREET = "one_way_street"
    SLIP_ROAD = "slip_road"
    OTHER = "other"


class UrbanOrRuralArea(str, Enum):
    URBAN = "urban"
    RURAL = "rural"


class Coordinates(BaseModel):
    """A single lat/lon point, constrained to the UK mainland bounding box used
    throughout this project."""

    latitude: float = Field(
        ...,
        ge=_UK_MIN_LATITUDE,
        le=_UK_MAX_LATITUDE,
        description="Latitude in decimal degrees (WGS84).",
    )
    longitude: float = Field(
        ...,
        ge=_UK_MIN_LONGITUDE,
        le=_UK_MAX_LONGITUDE,
        description="Longitude in decimal degrees (WGS84).",
    )


class SeverityBreakdown(BaseModel):
    """Accident counts split by severity class. Used anywhere a group of accidents
    needs to be summarized (hotspot clusters, report totals)."""

    model_config = ConfigDict(from_attributes=True)

    slight: int = Field(0, ge=0, description="Number of slight-severity accidents.")
    serious: int = Field(0, ge=0, description="Number of serious-severity accidents.")
    fatal: int = Field(0, ge=0, description="Number of fatal accidents.")

    @property
    def total(self) -> int:
        return self.slight + self.serious + self.fatal