"""
Student B - Accident Hotspot Service & Data Manager.

Provides fast, in-memory spatial and attribute filtering over precomputed
DBSCAN hotspot clusters from Student B's authoritative hotspot summary artifact.
"""

from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import ClassVar, Optional

import numpy as np
import pandas as pd
from fastapi import HTTPException, status

from app.config import settings
from app.schemas.common import Coordinates, Severity, SeverityBreakdown
from app.schemas.hotspot import HotspotAnalysisResponse, HotspotCluster, HotspotQueryRequest

logger = logging.getLogger(__name__)

EARTH_RADIUS_KM = 6371.0


class HotspotDataManager:
    """Singleton manager for loading, indexing, and querying Student B hotspot clusters."""

    _instance: ClassVar[Optional["HotspotDataManager"]] = None
    _df: pd.DataFrame
    _lats_rad: np.ndarray
    _lons_rad: np.ndarray
    _lats: np.ndarray
    _lons: np.ndarray
    _loaded: bool = False
    _artifact_path: Path

    def __new__(cls) -> "HotspotDataManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def total_clusters(self) -> int:
        return len(self._df) if self._loaded else 0

    def load(self, custom_path: Path | None = None) -> None:
        """Load the precomputed Student B hotspot artifact into memory.

        Raises:
            FileNotFoundError: If the CSV artifact does not exist.
            ValueError: If required columns are missing or data integrity checks fail.
        """
        hotspot_path = custom_path or settings.STUDENT_B_HOTSPOT_PATH
        logger.info("Initializing Student B Hotspot Data Manager from %s", hotspot_path)

        if not hotspot_path.exists():
            raise FileNotFoundError(
                f"Student B Hotspot summary artifact not found at {hotspot_path}. "
                "Please ensure data/output/hotspot_summary.csv exists or run "
                "python3 student_B/generate_hotspots.py to generate it."
            )

        df = pd.read_csv(hotspot_path)
        required_cols = [
            "Cluster",
            "Center_Latitude",
            "Center_Longitude",
            "Total_Accidents",
            "Dominant_Severity",
            "Dominant_Weather",
            "Dominant_Road_Type",
            "Average_Speed",
            "Average_Casualties",
            "Peak_Hour",
            "Fatal_Count",
            "Serious_Count",
            "Slight_Count",
        ]

        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(
                f"Student B hotspot artifact {hotspot_path} is missing required columns: {missing}"
            )

        # Validate numeric ranges
        if (df["Center_Latitude"] < -90).any() or (df["Center_Latitude"] > 90).any():
            raise ValueError("Student B hotspot artifact contains invalid latitude values.")
        if (df["Center_Longitude"] < -180).any() or (df["Center_Longitude"] > 180).any():
            raise ValueError("Student B hotspot artifact contains invalid longitude values.")
        if (df["Total_Accidents"] < 1).any():
            raise ValueError("Student B hotspot artifact contains invalid Total_Accidents values.")

        # Validate severity count invariant
        sev_sum = df["Fatal_Count"] + df["Serious_Count"] + df["Slight_Count"]
        if (sev_sum != df["Total_Accidents"]).any():
            mismatches = (sev_sum != df["Total_Accidents"]).sum()
            raise ValueError(
                f"Student B artifact severity count invariant check failed for {mismatches} clusters: "
                "Fatal_Count + Serious_Count + Slight_Count != Total_Accidents."
            )

        # Precompute radian coordinate arrays for vectorised Haversine filtering
        self._df = df.copy()
        self._lats = df["Center_Latitude"].to_numpy(dtype=np.float64)
        self._lons = df["Center_Longitude"].to_numpy(dtype=np.float64)
        self._lats_rad = np.radians(self._lats)
        self._lons_rad = np.radians(self._lons)
        self._artifact_path = hotspot_path
        self._loaded = True

        logger.info(
            "Student B Hotspot Data Manager loaded successfully (%d clusters, 0 NaNs).",
            len(self._df),
        )

    def query(self, request: HotspotQueryRequest) -> HotspotAnalysisResponse:
        """Execute spatial and attribute filtering over in-memory hotspot clusters."""
        if not self._loaded:
            raise RuntimeError("HotspotDataManager has not been loaded. Call load() first.")

        # 1. Spatial Filter
        if request.min_lat is not None and request.max_lat is not None:
            # Bounding box filter
            spatial_mask = (
                (self._lats >= request.min_lat)
                & (self._lats <= request.max_lat)
                & (self._lons >= request.min_lon)
                & (self._lons <= request.max_lon)
            )
        elif request.center is not None and request.radius_km is not None:
            # Vectorised Haversine distance from search center
            c_lat_rad = np.radians(request.center.latitude)
            c_lon_rad = np.radians(request.center.longitude)

            d_lat = self._lats_rad - c_lat_rad
            d_lon = self._lons_rad - c_lon_rad

            a = (
                np.sin(d_lat / 2.0) ** 2
                + np.cos(c_lat_rad) * np.cos(self._lats_rad) * np.sin(d_lon / 2.0) ** 2
            )
            # Clip to [0, 1] to prevent numerical issues with arcsin
            a = np.clip(a, 0.0, 1.0)
            distances_km = 2.0 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))
            spatial_mask = distances_km <= request.radius_km
        else:
            spatial_mask = np.ones(len(self._df), dtype=bool)

        # 2. Minimum Severity Filter
        if request.min_severity is not None:
            if request.min_severity == Severity.FATAL:
                sev_mask = (self._df["Fatal_Count"] >= 1).to_numpy()
            elif request.min_severity == Severity.SERIOUS:
                sev_mask = ((self._df["Fatal_Count"] + self._df["Serious_Count"]) >= 1).to_numpy()
            else:  # Severity.SLIGHT
                sev_mask = np.ones(len(self._df), dtype=bool)
            combined_mask = spatial_mask & sev_mask
        else:
            combined_mask = spatial_mask

        # 3. Filter and Sort
        matched_df = self._df[combined_mask]
        total_hotspots_in_area = len(matched_df)

        if total_hotspots_in_area == 0:
            return HotspotAnalysisResponse(
                clusters=[],
                total_accidents_considered=0,
                total_hotspots_in_area=0,
                generated_at=datetime.now(timezone.utc),
            )

        # Deterministic sort: Total_Accidents descending, Cluster ascending
        sorted_df = matched_df.sort_values(by=["Total_Accidents", "Cluster"], ascending=[False, True])
        limited_df = sorted_df.head(request.limit)

        # 4. Map to Pydantic Response
        clusters: list[HotspotCluster] = []
        total_accidents = 0

        for row in limited_df.itertuples():
            acc_count = int(row.Total_Accidents)
            total_accidents += acc_count
            factor = f"{row.Dominant_Road_Type} - {row.Dominant_Weather}"

            clusters.append(
                HotspotCluster(
                    cluster_id=f"cluster-{int(row.Cluster)}",
                    center=Coordinates(
                        latitude=float(row.Center_Latitude),
                        longitude=float(row.Center_Longitude),
                    ),
                    radius_meters=500.0,
                    accident_count=acc_count,
                    severity_breakdown=SeverityBreakdown(
                        fatal=int(row.Fatal_Count),
                        serious=int(row.Serious_Count),
                        slight=int(row.Slight_Count),
                    ),
                    dominant_severity=str(row.Dominant_Severity),
                    dominant_weather=str(row.Dominant_Weather),
                    dominant_road_type=str(row.Dominant_Road_Type),
                    average_speed=float(row.Average_Speed),
                    average_casualties=float(row.Average_Casualties),
                    peak_hour=int(row.Peak_Hour),
                    dominant_contributing_factor=factor,
                )
            )

        return HotspotAnalysisResponse(
            clusters=clusters,
            total_accidents_considered=total_accidents,
            total_hotspots_in_area=total_hotspots_in_area,
            generated_at=datetime.now(timezone.utc),
        )


class HotspotService:
    """Provides accident hotspot cluster analysis via the HotspotDataManager singleton."""

    def __init__(self, data_manager: HotspotDataManager | None = None) -> None:
        self.data_manager = data_manager or HotspotDataManager()

    def analyze(self, request: HotspotQueryRequest) -> HotspotAnalysisResponse:
        """Analyze accidents matching the query and return real hotspot clusters."""
        try:
            return self.data_manager.query(request)
        except Exception as exc:
            logger.error("Hotspot query analysis failed: %s", exc, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Hotspot analysis query failed: {exc}",
            ) from exc