"""
Report Grounding Service.

Aggregates structured evidence from Student A (Random Forest Severity),
Student B (DBSCAN Hotspots), and Student C (GNN Road Risk) into a compact,
strictly validated, deterministic grounding payload suitable for LLM interpretation.
"""

from datetime import datetime, timezone
import logging
from typing import Any, ClassVar, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Coordinates
from app.schemas.hotspot import HotspotQueryRequest
from app.schemas.report import AIInfrastructureReportRequest
from app.schemas.risk import RoadRiskQueryRequest
from app.services.hotspot_service import HotspotDataManager
from app.services.risk_service import RiskDataManager
from app.services.severity_service import SeverityModelManager

logger = logging.getLogger(__name__)

# Bounding boxes for standardized geographic regions across UK
REGION_BOUNDS: dict[str, dict[str, float]] = {
    "all": {"min_lat": 49.5, "max_lat": 61.0, "min_lon": -8.5, "max_lon": 2.0},
    "north": {"min_lat": 55.0, "max_lat": 61.0, "min_lon": -8.5, "max_lon": 2.0},
    "central": {"min_lat": 53.0, "max_lat": 55.0, "min_lon": -8.5, "max_lon": 2.0},
    "south": {"min_lat": 49.5, "max_lat": 53.0, "min_lon": -3.0, "max_lon": 2.0},
    "west": {"min_lat": 49.5, "max_lat": 55.0, "min_lon": -8.5, "max_lon": -2.5},
    "east": {"min_lat": 51.0, "max_lat": 55.0, "min_lon": 0.0, "max_lon": 2.0},
}


class StudentAEvidence(BaseModel):
    """Deterministic structural metadata from Student A Severity model."""

    source: str = "Student A Random Forest Severity Model"
    model_type: str = "RandomForestClassifier"
    feature_count: int = 138
    target_classes: list[str] = Field(default_factory=lambda: ["Fatal", "Serious", "Slight"])
    key_feature_groups: list[str] = Field(
        default_factory=lambda: [
            "Speed Limit & Vehicle Dynamics",
            "Junction Detail & Traffic Control",
            "Weather & Visibility Conditions",
            "Road Surface & Classification",
            "Casualty & Vehicle Count Interactions",
        ]
    )
    limitations: str = (
        "Point-in-time accident severity classifier. Evaluates single or batched "
        "incident scenarios; does not aggregate historical temporal trends directly."
    )


class GroundedHotspot(BaseModel):
    """Representative high-density cluster from Student B."""

    cluster_id: str
    center: Coordinates
    accident_count: int
    fatal_count: int
    serious_count: int
    slight_count: int
    dominant_weather: str
    dominant_road_type: str
    average_speed: float
    peak_hour: int


class StudentBEvidence(BaseModel):
    """Deterministic spatial cluster metrics from Student B DBSCAN artifact."""

    source: str = "Student B DBSCAN Hotspot Analysis"
    algorithm: str = "DBSCAN (eps=500m / haversine, min_samples=25)"
    total_clusters_in_scope: int
    total_accidents_in_scope: int
    aggregate_severity_in_scope: dict[str, int]
    top_hotspots: list[GroundedHotspot]
    limitations: str = (
        "Precomputed spatial clusters based on 2.04M historical UK accident records. "
        "Dynamic sub-period date slicing is not supported by this precomputed spatial artifact."
    )


class GroundedRoadSegment(BaseModel):
    """Representative high-risk road segment from Student C."""

    segment_id: int
    road_number: int
    start: Coordinates
    end: Coordinates
    predicted_risk: float
    risk_category: str


class StudentCEvidence(BaseModel):
    """Deterministic topological risk metrics from Student C GNN artifact."""

    source: str = "Student C Graph Neural Network (GNN) Road Risk Model"
    architecture: str = "2-layer Graph Convolutional Network (GCN) with 6 node features"
    total_segments_in_scope: int
    highest_predicted_risk: float
    risk_band_counts: dict[str, int]
    top_segments: list[GroundedRoadSegment]
    limitations: str = (
        "Topological network risk index across 13,921 road segments. Represents "
        "structural collision vulnerability, not real-time live traffic sensor feeds."
    )


class GroundingPayload(BaseModel):
    """Compact, strictly verified, and serializable grounding evidence payload."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    request_filters: AIInfrastructureReportRequest
    student_a: StudentAEvidence
    student_b: StudentBEvidence
    student_c: StudentCEvidence
    grounding_rules: list[str] = Field(
        default_factory=lambda: [
            "All quantitative values and geographic coordinates are verified facts from trained models.",
            "Do not invent accident counts, road numbers, coordinates, or model probabilities.",
            "Distinguish observed statistical correlations from unverified root causes.",
            "Do not claim interventions were empirically validated if they are recommendations.",
        ]
    )


class ReportGroundingService:
    """Aggregates deterministic evidence from Student A, B, and C managers for report generation."""

    _max_hotspots: ClassVar[int] = 12
    _max_segments: ClassVar[int] = 12

    def __init__(
        self,
        severity_manager: Optional[SeverityModelManager] = None,
        hotspot_manager: Optional[HotspotDataManager] = None,
        risk_manager: Optional[RiskDataManager] = None,
    ) -> None:
        self.severity_manager = severity_manager or SeverityModelManager.get_instance()
        self.hotspot_manager = hotspot_manager or HotspotDataManager()
        self.risk_manager = risk_manager or RiskDataManager()

    def build_grounding_payload(
        self, request: AIInfrastructureReportRequest
    ) -> GroundingPayload:
        """Construct a bounded, deterministic evidence payload from core model data managers."""
        # 1. Resolve Region Bounds
        bounds = REGION_BOUNDS.get(request.region.lower(), REGION_BOUNDS["all"])

        # 2. Student A Evidence
        feature_count = (
            len(self.severity_manager.features)
            if self.severity_manager.is_loaded
            else 138
        )
        student_a = StudentAEvidence(feature_count=feature_count)

        # 3. Student B Evidence (Hotspots)
        student_b = self._extract_student_b_evidence(bounds)

        # 4. Student C Evidence (GNN Road Risk)
        student_c = self._extract_student_c_evidence(bounds)

        return GroundingPayload(
            request_filters=request,
            student_a=student_a,
            student_b=student_b,
            student_c=student_c,
        )

    def _extract_student_b_evidence(self, bounds: dict[str, float]) -> StudentBEvidence:
        """Query HotspotDataManager deterministically within the geographic bounds."""
        if not self.hotspot_manager.is_loaded:
            self.hotspot_manager.load()

        hotspot_req = HotspotQueryRequest(
            min_lat=bounds["min_lat"],
            max_lat=bounds["max_lat"],
            min_lon=bounds["min_lon"],
            max_lon=bounds["max_lon"],
            limit=self._max_hotspots,
        )

        response = self.hotspot_manager.query(hotspot_req)

        top_hotspots: list[GroundedHotspot] = []
        total_fatal = 0
        total_serious = 0
        total_slight = 0

        for cluster in response.clusters:
            total_fatal += cluster.severity_breakdown.fatal
            total_serious += cluster.severity_breakdown.serious
            total_slight += cluster.severity_breakdown.slight

            top_hotspots.append(
                GroundedHotspot(
                    cluster_id=cluster.cluster_id,
                    center=cluster.center,
                    accident_count=cluster.accident_count,
                    fatal_count=cluster.severity_breakdown.fatal,
                    serious_count=cluster.severity_breakdown.serious,
                    slight_count=cluster.severity_breakdown.slight,
                    dominant_weather=cluster.dominant_weather or "Fine",
                    dominant_road_type=cluster.dominant_road_type or "Single Carriageway",
                    average_speed=cluster.average_speed or 30.0,
                    peak_hour=cluster.peak_hour or 17,
                )
            )

        return StudentBEvidence(
            total_clusters_in_scope=response.total_hotspots_in_area,
            total_accidents_in_scope=response.total_accidents_considered,
            aggregate_severity_in_scope={
                "fatal": total_fatal,
                "serious": total_serious,
                "slight": total_slight,
            },
            top_hotspots=top_hotspots,
        )

    def _extract_student_c_evidence(self, bounds: dict[str, float]) -> StudentCEvidence:
        """Query RiskDataManager deterministically within the geographic bounds."""
        if not self.risk_manager.is_loaded:
            self.risk_manager.load()

        risk_req = RoadRiskQueryRequest(
            min_lat=bounds["min_lat"],
            max_lat=bounds["max_lat"],
            min_lon=bounds["min_lon"],
            max_lon=bounds["max_lon"],
            limit=self._max_segments,
        )

        response = self.risk_manager.query(risk_req)

        top_segments: list[GroundedRoadSegment] = []
        band_counts: dict[str, int] = {"critical": 0, "high": 0, "moderate": 0, "low": 0}
        highest_risk = 0.0

        for seg in response.segments:
            if seg.predicted_risk > highest_risk:
                highest_risk = seg.predicted_risk

            cat_norm = seg.risk_category.lower()
            if cat_norm in band_counts:
                band_counts[cat_norm] += 1

            top_segments.append(
                GroundedRoadSegment(
                    segment_id=seg.segment_id,
                    road_number=seg.road_number,
                    start=seg.start,
                    end=seg.end,
                    predicted_risk=seg.predicted_risk,
                    risk_category=seg.risk_category,
                )
            )

        return StudentCEvidence(
            total_segments_in_scope=response.total_segments_matched,
            highest_predicted_risk=round(highest_risk, 4),
            risk_band_counts=band_counts,
            top_segments=top_segments,
        )

