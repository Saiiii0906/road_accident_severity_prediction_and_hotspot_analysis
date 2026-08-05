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
    radius_km: float | None = Field(None, gt=0, le=100, description="Search radius in kilometres.")

    date_from: date | None = Field(None, description="Include accidents on or after this date.")
    date_to: date | None = Field(None, description="Include accidents on or before this date.")
    min_severity: Severity | None = Field(
        None, description="Only include accidents at or above this severity."
    )
    limit: int = Field(50, ge=1, le=500, description="Maximum number of hotspots to return.")

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
        return self

    @model_validator(mode="after")
    def date_range_is_ordered(self) -> "HotspotQueryRequest":
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must be on or before date_to")
        return self


class HotspotCluster(BaseModel):
    """A single identified accident cluster."""

    model_config = ConfigDict(from_attributes=True)

    cluster_id: str = Field(..., description="Stable identifier for this cluster.")
    center: Coordinates
    radius_meters: float = Field(..., ge=0, description="Approximate radius of the cluster.")
    accident_count: int = Field(..., ge=1)
    severity_breakdown: SeverityBreakdown
    dominant_contributing_factor: str | None = Field(
        None, description="Most common contributing factor among accidents in this cluster, if known."
    )


class HotspotAnalysisResponse(BaseModel):
    """Result of a hotspot query."""

    model_config = ConfigDict(from_attributes=True)

    clusters: list[HotspotCluster]
    total_accidents_considered: int = Field(
        ..., ge=0, description="Total accidents matched by the query filters, before clustering."
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)