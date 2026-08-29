from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .common import Coordinates, Severity, SeverityBreakdown


class HotspotQueryRequest(BaseModel):
    """Filters for locating accident hotspots. Exactly one of (bounding box) or
    (center + radius_km) must be provided."""

    min_lat: float | None = Field(None, description="Bounding box southern edge.")
    max_lat: float | None = Field(None, description="Bounding box northern edge.")
    min_lon: float | None = Field(None, description="Bounding box western edge.")
    max_lon: float | None = Field(None, description="Bounding box eastern edge.")

    center: Coordinates | None = Field(None, description="Center point for a radius search.")
    radius_km: float | None = Field(None, gt=0, le=1000, description="Search radius in kilometres.")

    date_from: date | None = Field(None, description="Include accidents on or after this date.")
    date_to: date | None = Field(None, description="Include accidents on or before this date.")
    min_severity: Severity | None = Field(
        None, description="Only include hotspots with at least one accident at or above this severity ('fatal', 'serious', 'slight')."
    )
    limit: int = Field(50, ge=1, le=500, description="Maximum number of hotspots to return.")

    @model_validator(mode="after")
    def validate_date_filters_not_supported(self) -> "HotspotQueryRequest":
        if self.date_from is not None or self.date_to is not None:
            raise ValueError(
                "Date filtering (date_from/date_to) is not available from the precomputed Student B DBSCAN hotspot summary artifact."
            )
        return self

    @model_validator(mode="after")
    def exactly_one_area_definition(self) -> "HotspotQueryRequest":
        bbox_fields = (self.min_lat, self.max_lat, self.min_lon, self.max_lon)
        bbox_given = all(f is not None for f in bbox_fields)
        bbox_partial = any(f is not None for f in bbox_fields) and not bbox_given
        radius_given = self.center is not None and self.radius_km is not None

        if bbox_partial:
            raise ValueError("min_lat, max_lat, min_lon, and max_lon must all be provided together")
        if bbox_given and radius_given:
            raise ValueError("provide either a bounding box or a center + radius_km, not both")
        if not bbox_given and not radius_given:
            raise ValueError("provide either a bounding box or a center + radius_km")
        if bbox_given:
            if self.min_lat > self.max_lat:
                raise ValueError("min_lat must be less than or equal to max_lat")
            if self.min_lon > self.max_lon:
                raise ValueError("min_lon must be less than or equal to max_lon")
        return self


class HotspotCluster(BaseModel):
    """A single identified accident cluster from Student B DBSCAN."""

    model_config = ConfigDict(from_attributes=True)

    cluster_id: str = Field(..., description="Stable identifier for this cluster.")
    center: Coordinates
    radius_meters: float = Field(500.0, ge=0, description="DBSCAN neighborhood radius (eps) parameter in metres.")
    accident_count: int = Field(..., ge=1, description="Total accidents in cluster.")
    severity_breakdown: SeverityBreakdown = Field(..., description="Exact counts of accidents by severity level.")
    dominant_severity: str | None = Field(None, description="Mode severity class across incidents in this cluster.")
    dominant_weather: str | None = Field(None, description="Mode weather condition across incidents in this cluster.")
    dominant_road_type: str | None = Field(None, description="Mode road type across incidents in this cluster.")
    average_speed: float | None = Field(None, description="Mean speed limit in this cluster.")
    average_casualties: float | None = Field(None, description="Mean casualties per collision in this cluster.")
    peak_hour: int | None = Field(None, description="Mode collision hour (0-23) in this cluster.")
    dominant_contributing_factor: str | None = Field(
        None, description="Descriptive condition indicator for backwards compatibility."
    )


class HotspotAnalysisResponse(BaseModel):
    """Result of a hotspot query."""

    model_config = ConfigDict(from_attributes=True)

    clusters: list[HotspotCluster]
    total_accidents_considered: int = Field(
        ..., ge=0, description="Total accidents matched across returned clusters."
    )
    total_hotspots_in_area: int | None = Field(
        None, ge=0, description="Total hotspot clusters matching area filters before limit."
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)