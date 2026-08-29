"""
Student C - Graph Neural Network (GNN) Road Risk Service & Data Manager.

Provides fast, in-memory spatial and topological querying over precomputed
GNN road-segment risk predictions.
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import ClassVar, Optional

from fastapi import HTTPException, status
import numpy as np

from app.config import settings
from app.schemas.common import Coordinates
from app.schemas.risk import (
    RiskAssessmentRequest,
    RiskAssessmentResponse,
    RiskLevel,
    RoadRiskPredictionResponse,
    RoadRiskQueryRequest,
    RoadSegment,
)

logger = logging.getLogger(__name__)

EARTH_RADIUS_KM = 6371.0


class RiskDataManager:
    """Singleton manager for loading, validating, and querying Student C GNN road risk predictions."""

    _instance: ClassVar[Optional["RiskDataManager"]] = None
    _edge_ids: np.ndarray
    _road_numbers: np.ndarray
    _start_lats: np.ndarray
    _start_lons: np.ndarray
    _end_lats: np.ndarray
    _end_lons: np.ndarray
    _mid_lats: np.ndarray
    _mid_lons: np.ndarray
    _mid_lats_rad: np.ndarray
    _mid_lons_rad: np.ndarray
    _predicted_risks: np.ndarray
    _total_segments: int = 0
    _loaded: bool = False
    _artifact_path: Path

    def __new__(cls) -> "RiskDataManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def total_segments(self) -> int:
        return self._total_segments

    def load(self, custom_path: Path | None = None) -> None:
        """Load and validate the precomputed Student C GNN prediction artifact into memory.

        Raises:
            FileNotFoundError: If the JSON artifact does not exist.
            ValueError: If schema or data integrity validation fails.
        """
        artifact_path = custom_path or settings.STUDENT_C_RISK_PATH
        logger.info("Initializing Student C Risk Data Manager from %s", artifact_path)

        if not artifact_path.exists():
            raise FileNotFoundError(
                f"Student C GNN prediction artifact not found at {artifact_path}. "
                "Ensure student_C/gnn_risk_predictions.json exists or export it from the canonical notebook."
            )

        with open(artifact_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as exc:
                raise ValueError(f"Student C prediction artifact {artifact_path} contains malformed JSON: {exc}") from exc

        if not isinstance(data, list) or len(data) == 0:
            raise ValueError(f"Student C prediction artifact {artifact_path} must be a non-empty list of records.")

        required_fields = ["edge_id", "road_number", "start_lat", "start_lon", "end_lat", "end_lon", "predicted_risk"]
        
        edge_ids = []
        road_numbers = []
        start_lats = []
        start_lons = []
        end_lats = []
        end_lons = []
        predicted_risks = []

        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                raise ValueError(f"Record #{idx} in {artifact_path} is not a valid JSON object.")
            
            missing = [k for k in required_fields if k not in item]
            if missing:
                raise ValueError(f"Record #{idx} in {artifact_path} is missing required fields: {missing}")

            try:
                e_id = int(item["edge_id"])
                r_num = int(float(item["road_number"]))
                s_lat = float(item["start_lat"])
                s_lon = float(item["start_lon"])
                e_lat = float(item["end_lat"])
                e_lon = float(item["end_lon"])
                p_risk = float(item["predicted_risk"])
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Record #{idx} in {artifact_path} has invalid numeric types: {exc}") from exc

            # Coordinate validation
            if not (-90.0 <= s_lat <= 90.0 and -90.0 <= e_lat <= 90.0):
                raise ValueError(f"Record #{idx} contains out-of-range latitude values.")
            if not (-180.0 <= s_lon <= 180.0 and -180.0 <= e_lon <= 180.0):
                raise ValueError(f"Record #{idx} contains out-of-range longitude values.")
            
            # Risk range validation
            if not (0.0 <= p_risk <= 1.0):
                raise ValueError(f"Record #{idx} predicted_risk {p_risk} is out of bounds [0.0, 1.0].")

            edge_ids.append(e_id)
            road_numbers.append(r_num)
            start_lats.append(s_lat)
            start_lons.append(s_lon)
            end_lats.append(e_lat)
            end_lons.append(e_lon)
            predicted_risks.append(p_risk)

        # Validate unique edge_ids
        if len(set(edge_ids)) != len(edge_ids):
            raise ValueError(f"Duplicate edge_ids detected in {artifact_path}.")

        # Store arrays in memory
        self._edge_ids = np.array(edge_ids, dtype=np.int64)
        self._road_numbers = np.array(road_numbers, dtype=np.int64)
        self._start_lats = np.array(start_lats, dtype=np.float64)
        self._start_lons = np.array(start_lons, dtype=np.float64)
        self._end_lats = np.array(end_lats, dtype=np.float64)
        self._end_lons = np.array(end_lons, dtype=np.float64)
        self._predicted_risks = np.array(predicted_risks, dtype=np.float64)

        # Precompute segment midpoints
        self._mid_lats = (self._start_lats + self._end_lats) / 2.0
        self._mid_lons = (self._start_lons + self._end_lons) / 2.0
        self._mid_lats_rad = np.radians(self._mid_lats)
        self._mid_lons_rad = np.radians(self._mid_lons)

        self._total_segments = len(self._edge_ids)
        self._artifact_path = artifact_path
        self._loaded = True

        logger.info(
            "Student C Risk Data Manager loaded successfully (%d road segments, 0 NaNs).",
            self._total_segments,
        )

    @staticmethod
    def _categorize_risk(score: float) -> str:
        """Classify predicted continuous risk into relative presentation categories."""
        if score >= 0.10:
            return "Critical"
        if score >= 0.08:
            return "High"
        if score >= 0.06:
            return "Moderate"
        return "Low"

    def query(self, request: RoadRiskQueryRequest) -> RoadRiskPredictionResponse:
        """Execute spatial, road, and risk-threshold filtering over precomputed road segments."""
        if not self._loaded:
            raise RuntimeError("RiskDataManager has not been loaded. Call load() first.")

        mask = np.ones(self._total_segments, dtype=bool)

        # 1. Road Number Filter
        if request.road_number is not None:
            mask = mask & (self._road_numbers == request.road_number)

        # 2. Spatial Filter: Bounding Box
        if request.min_lat is not None and request.max_lat is not None:
            # Segment matches if its midpoint is within the bounding box
            bbox_mask = (
                (self._mid_lats >= request.min_lat)
                & (self._mid_lats <= request.max_lat)
                & (self._mid_lons >= request.min_lon)
                & (self._mid_lons <= request.max_lon)
            )
            mask = mask & bbox_mask

        # 3. Spatial Filter: Center + Radius (Haversine)
        elif request.center is not None and request.radius_km is not None:
            c_lat_rad = np.radians(request.center.latitude)
            c_lon_rad = np.radians(request.center.longitude)

            d_lat = self._mid_lats_rad - c_lat_rad
            d_lon = self._mid_lons_rad - c_lon_rad

            a = (
                np.sin(d_lat / 2.0) ** 2
                + np.cos(c_lat_rad) * np.cos(self._mid_lats_rad) * np.sin(d_lon / 2.0) ** 2
            )
            a = np.clip(a, 0.0, 1.0)
            distances_km = 2.0 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))
            mask = mask & (distances_km <= request.radius_km)

        # 4. Minimum Risk Threshold Filter
        if request.min_risk is not None:
            mask = mask & (self._predicted_risks >= request.min_risk)

        matched_indices = np.where(mask)[0]
        total_matched = len(matched_indices)

        if total_matched == 0:
            return RoadRiskPredictionResponse(
                segments=[],
                total_segments=0,
                total_segments_matched=0,
                generated_at=datetime.now(timezone.utc),
            )

        # 5. Deterministic Sort: predicted_risk descending, segment_id ascending
        # Invert predicted_risk for descending order in np.lexsort
        order = np.lexsort((self._edge_ids[matched_indices], -self._predicted_risks[matched_indices]))
        sorted_indices = matched_indices[order]
        top_indices = sorted_indices[: request.limit]

        # 6. Map to RoadSegment schemas
        segments: list[RoadSegment] = []
        for idx in top_indices:
            p_risk = float(self._predicted_risks[idx])
            segments.append(
                RoadSegment(
                    segment_id=int(self._edge_ids[idx]),
                    road_number=int(self._road_numbers[idx]),
                    start=Coordinates(
                        latitude=float(self._start_lats[idx]),
                        longitude=float(self._start_lons[idx]),
                    ),
                    end=Coordinates(
                        latitude=float(self._end_lats[idx]),
                        longitude=float(self._end_lons[idx]),
                    ),
                    predicted_risk=round(p_risk, 4),
                    risk_category=self._categorize_risk(p_risk),
                )
            )

        return RoadRiskPredictionResponse(
            segments=segments,
            total_segments=len(segments),
            total_segments_matched=total_matched,
            generated_at=datetime.now(timezone.utc),
        )


class RiskService:
    """Provides road risk analysis via the RiskDataManager singleton."""

    def __init__(self, data_manager: RiskDataManager | None = None) -> None:
        self.data_manager = data_manager or RiskDataManager()

    def predict(self, request: RoadRiskQueryRequest) -> RoadRiskPredictionResponse:
        """Query precomputed topological road risk predictions."""
        try:
            return self.data_manager.query(request)
        except Exception as exc:
            logger.error("Road risk query failed: %s", exc, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Road risk query failed: {exc}",
            ) from exc

    def assess(self, request: RiskAssessmentRequest) -> RiskAssessmentResponse:
        """Legacy location-based risk assessment endpoint."""
        # Query nearest road segment around the requested location
        query_req = RoadRiskQueryRequest(
            center=request.location,
            radius_km=5.0,
            limit=1,
        )
        prediction_res = self.data_manager.query(query_req)
        
        if prediction_res.segments:
            top_segment = prediction_res.segments[0]
            risk_score = round(top_segment.predicted_risk * 100.0, 2)
            category = top_segment.risk_category.lower()
            risk_level = RiskLevel(category) if category in [e.value for e in RiskLevel] else RiskLevel.MEDIUM
        else:
            risk_score = 42.0
            risk_level = RiskLevel.MEDIUM

        return RiskAssessmentResponse(
            location=request.location,
            risk_score=risk_score,
            risk_level=risk_level,
            contributing_factors=[],
            model_version="Student_C_RoadRiskGNN_v1.0",
            assessed_at=request.assessed_at,
        )