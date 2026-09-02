"""
Historical Model Corridor Matching Service.

Connects the resolved route geometry to precomputed Student B (DBSCAN Hotspots)
and Student C (GNN Road Risk) empirical models using spherical spatial indexing (BallTree).
Evaluates geographic coverage constraints and truthfully represents absent evidence.
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree

from app.config import settings
from app.schemas.journey import (
    CorridorMatchingMetadataSchema,
    DataAvailabilityStatus,
    HistoricalCoverageSchema,
    HistoricalEvidenceSchema,
    HistoricalHotspotEvidenceSchema,
    HistoricalRiskEvidenceSchema,
    HistoricalSeverityEvidenceSchema,
    MatchedHotspotSchema,
    MatchedSegmentSchema,
    RouteInfoSchema,
)
from app.services.hotspot_service import HotspotDataManager
from app.services.risk_service import RiskDataManager

logger = logging.getLogger(__name__)

EARTH_RADIUS_METERS = 6371000.0


class CorridorMatchingService:
    """Performs spatial corridor matching against historical Student A, B, and C artifacts."""

    def __init__(
        self,
        hotspot_data_manager: Optional[HotspotDataManager] = None,
        risk_data_manager: Optional[RiskDataManager] = None,
        corridor_radius_m: Optional[float] = None,
    ) -> None:
        self.hotspot_manager = hotspot_data_manager or HotspotDataManager()
        self.risk_manager = risk_data_manager or RiskDataManager()
        self.corridor_radius_m = (
            settings.HISTORICAL_CORRIDOR_RADIUS_METERS
            if corridor_radius_m is None
            else corridor_radius_m
        )

        # Lazy spatial trees
        self._hotspot_tree: Optional[BallTree] = None
        self._hotspot_coords_rad: Optional[np.ndarray] = None
        self._segment_tree: Optional[BallTree] = None
        self._segment_coords_rad: Optional[np.ndarray] = None

    def _ensure_data_loaded(self) -> None:
        """Ensure singleton managers are loaded."""
        if not self.hotspot_manager.is_loaded:
            try:
                self.hotspot_manager.load()
            except Exception as exc:
                logger.error("Failed to load HotspotDataManager: %s", exc)

        if not self.risk_manager.is_loaded:
            try:
                self.risk_manager.load()
            except Exception as exc:
                logger.error("Failed to load RiskDataManager: %s", exc)

    def _get_hotspot_tree(self) -> Optional[BallTree]:
        """Build or return cached BallTree for Student B hotspots."""
        self._ensure_data_loaded()
        if not self.hotspot_manager.is_loaded:
            return None

        if self._hotspot_tree is None:
            # Coordinates in radians [lat_rad, lon_rad]
            lats_rad = self.hotspot_manager._lats_rad
            lons_rad = self.hotspot_manager._lons_rad
            self._hotspot_coords_rad = np.column_stack([lats_rad, lons_rad])
            self._hotspot_tree = BallTree(self._hotspot_coords_rad, metric="haversine")
            logger.info("Initialized BallTree for %d DBSCAN hotspots.", len(lats_rad))

        return self._hotspot_tree

    def _get_segment_tree(self) -> Optional[BallTree]:
        """Build or return cached BallTree for Student C GNN segments."""
        self._ensure_data_loaded()
        if not self.risk_manager.is_loaded:
            return None

        if self._segment_tree is None:
            mid_lats_rad = self.risk_manager._mid_lats_rad
            mid_lons_rad = self.risk_manager._mid_lons_rad
            self._segment_coords_rad = np.column_stack([mid_lats_rad, mid_lons_rad])
            self._segment_tree = BallTree(self._segment_coords_rad, metric="haversine")
            logger.info("Initialized BallTree for %d GNN road segments.", len(mid_lats_rad))

        return self._segment_tree

    def check_coverage(
        self, route: RouteInfoSchema
    ) -> tuple[bool, DataAvailabilityStatus, str]:
        """Evaluate whether route geometry falls within supported UK historical coverage."""
        coords = route.geometry.coordinates if route.geometry else []
        if not coords:
            if route.source and route.destination:
                coords = [
                    [route.source.longitude, route.source.latitude],
                    [route.destination.longitude, route.destination.latitude],
                ]
            else:
                return (
                    False,
                    DataAvailabilityStatus.UNAVAILABLE,
                    "Route geometry unavailable for coverage evaluation.",
                )

        min_lat_bound, max_lat_bound, min_lon_bound, max_lon_bound = (
            settings.HISTORICAL_COVERAGE_BOUNDS
        )

        in_bounds_flags = [
            (min_lat_bound <= lat <= max_lat_bound) and (min_lon_bound <= lon <= max_lon_bound)
            for lon, lat in coords
        ]

        in_count = sum(in_bounds_flags)
        total_count = len(coords)

        if in_count == total_count:
            return (
                True,
                DataAvailabilityStatus.AVAILABLE,
                "Route is within supported historical model coverage (Great Britain).",
            )
        elif in_count > 0:
            return (
                True,
                DataAvailabilityStatus.PARTIAL,
                "Route partially intersects supported historical model coverage (Great Britain).",
            )
        else:
            return (
                False,
                DataAvailabilityStatus.UNAVAILABLE,
                "Route is outside the geographic coverage of historical UK road safety models (Great Britain).",
            )

    def match_hotspots(
        self, route: RouteInfoSchema, corridor_radius_m: float
    ) -> HistoricalHotspotEvidenceSchema:
        """Spatially match route geometry against Student B DBSCAN cluster centers."""
        tree = self._get_hotspot_tree()
        if tree is None:
            return HistoricalHotspotEvidenceSchema(
                status=DataAvailabilityStatus.UNAVAILABLE,
                hotspots_on_route=0,
                total_historical_accidents=0,
                cluster_ids=[],
                highest_cluster_density=None,
                matched_hotspots=[],
                description="Student B hotspot dataset could not be loaded.",
            )

        coords = route.geometry.coordinates if route.geometry and route.geometry.coordinates else []
        if not coords and route.source and route.destination:
            coords = [
                [route.source.longitude, route.source.latitude],
                [route.destination.longitude, route.destination.latitude],
            ]

        if not coords:
            return HistoricalHotspotEvidenceSchema(
                status=DataAvailabilityStatus.UNAVAILABLE,
                hotspots_on_route=0,
                total_historical_accidents=0,
                cluster_ids=[],
                highest_cluster_density=None,
                matched_hotspots=[],
                description="Route geometry unavailable for spatial corridor matching.",
            )

        # Convert route coordinates to [lat_rad, lon_rad]
        route_rad = np.radians([[lat, lon] for lon, lat in coords])
        radius_rad = corridor_radius_m / EARTH_RADIUS_METERS

        # Query all clusters within corridor distance of any route waypoint
        indices_list, distances_list = tree.query_radius(
            route_rad, r=radius_rad, return_distance=True
        )

        # Map cluster_index -> minimum distance to any route waypoint
        cluster_min_dist: dict[int, float] = {}
        for wp_indices, wp_dists in zip(indices_list, distances_list):
            for c_idx, d_rad in zip(wp_indices, wp_dists):
                d_m = d_rad * EARTH_RADIUS_METERS
                if c_idx not in cluster_min_dist or d_m < cluster_min_dist[c_idx]:
                    cluster_min_dist[c_idx] = d_m

        if not cluster_min_dist:
            return HistoricalHotspotEvidenceSchema(
                status=DataAvailabilityStatus.AVAILABLE,
                hotspots_on_route=0,
                total_historical_accidents=0,
                cluster_ids=[],
                highest_cluster_density=None,
                matched_hotspots=[],
                description=(
                    f"No historical DBSCAN accident clusters identified within the "
                    f"{corridor_radius_m:.0f}m corridor buffer. This indicates an absence "
                    "of dense statistical crash clusters, not necessarily zero historical accidents."
                ),
            )

        df = self.hotspot_manager._df
        matched_records: list[MatchedHotspotSchema] = []
        total_accidents_corridor = 0
        peak_density = 0

        for c_idx, dist_m in cluster_min_dist.items():
            row = df.iloc[c_idx]
            tot_acc = int(row["Total_Accidents"])
            total_accidents_corridor += tot_acc
            if tot_acc > peak_density:
                peak_density = tot_acc

            matched_records.append(
                MatchedHotspotSchema(
                    cluster_id=int(row["Cluster"]),
                    latitude=float(row["Center_Latitude"]),
                    longitude=float(row["Center_Longitude"]),
                    total_accidents=tot_acc,
                    fatal_count=int(row.get("Fatal_Count", 0)),
                    serious_count=int(row.get("Serious_Count", 0)),
                    slight_count=int(row.get("Slight_Count", 0)),
                    dominant_severity=str(row.get("Dominant_Severity", "")),
                    dominant_weather=str(row.get("Dominant_Weather", "")),
                    dominant_road_type=str(row.get("Dominant_Road_Type", "")),
                    average_speed=float(row["Average_Speed"]) if pd.notna(row.get("Average_Speed")) else None,
                    average_casualties=float(row["Average_Casualties"]) if pd.notna(row.get("Average_Casualties")) else None,
                    peak_hour=float(row["Peak_Hour"]) if pd.notna(row.get("Peak_Hour")) else None,
                    distance_to_route_m=round(dist_m, 1),
                )
            )

        # Sort by total historical accidents descending
        matched_records.sort(key=lambda r: r.total_accidents, reverse=True)

        cluster_ids = [str(r.cluster_id) for r in matched_records]
        # Display top 10 in schema to keep response payload concise
        top_records = matched_records[:10]

        return HistoricalHotspotEvidenceSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            hotspots_on_route=len(matched_records),
            total_historical_accidents=total_accidents_corridor,
            cluster_ids=cluster_ids,
            highest_cluster_density=peak_density,
            matched_hotspots=top_records,
            description=(
                f"Identified {len(matched_records)} historical accident hotspot clusters within "
                f"{corridor_radius_m:.0f}m corridor buffer (peak density: {peak_density} accidents, "
                f"total historical corridor crashes: {total_accidents_corridor:,})."
            ),
        )

    def match_segments(
        self, route: RouteInfoSchema, corridor_radius_m: float
    ) -> HistoricalRiskEvidenceSchema:
        """Spatially match route geometry against Student C GNN road network segments."""
        tree = self._get_segment_tree()
        if tree is None:
            return HistoricalRiskEvidenceSchema(
                status=DataAvailabilityStatus.UNAVAILABLE,
                segments_on_route=0,
                critical_segments_count=0,
                high_risk_segments_count=0,
                average_gnn_risk=None,
                peak_gnn_risk=None,
                high_risk_corridors=[],
                matched_segments=[],
                description="Student C GNN prediction dataset could not be loaded.",
            )

        coords = route.geometry.coordinates if route.geometry and route.geometry.coordinates else []
        if not coords and route.source and route.destination:
            coords = [
                [route.source.longitude, route.source.latitude],
                [route.destination.longitude, route.destination.latitude],
            ]

        if not coords:
            return HistoricalRiskEvidenceSchema(
                status=DataAvailabilityStatus.UNAVAILABLE,
                segments_on_route=0,
                critical_segments_count=0,
                high_risk_segments_count=0,
                average_gnn_risk=None,
                peak_gnn_risk=None,
                high_risk_corridors=[],
                matched_segments=[],
                description="Route geometry unavailable for spatial corridor matching.",
            )

        # Convert route coordinates to [lat_rad, lon_rad]
        route_rad = np.radians([[lat, lon] for lon, lat in coords])
        radius_rad = corridor_radius_m / EARTH_RADIUS_METERS

        # Query all segment midpoints within corridor distance
        indices_list, distances_list = tree.query_radius(
            route_rad, r=radius_rad, return_distance=True
        )

        segment_min_dist: dict[int, float] = {}
        for wp_indices, wp_dists in zip(indices_list, distances_list):
            for s_idx, d_rad in zip(wp_indices, wp_dists):
                d_m = d_rad * EARTH_RADIUS_METERS
                if s_idx not in segment_min_dist or d_m < segment_min_dist[s_idx]:
                    segment_min_dist[s_idx] = d_m

        if not segment_min_dist:
            return HistoricalRiskEvidenceSchema(
                status=DataAvailabilityStatus.AVAILABLE,
                segments_on_route=0,
                critical_segments_count=0,
                high_risk_segments_count=0,
                average_gnn_risk=None,
                peak_gnn_risk=None,
                high_risk_corridors=[],
                matched_segments=[],
                description=(
                    f"No modeled GNN road network segments identified within the "
                    f"{corridor_radius_m:.0f}m corridor buffer. This indicates an absence "
                    "of mapped network links in the topological graph, not low risk."
                ),
            )

        rm = self.risk_manager
        matched_records: list[MatchedSegmentSchema] = []
        risks = []
        high_risk_roads = set()
        critical_count = 0
        high_count = 0

        for s_idx, dist_m in segment_min_dist.items():
            risk_val = float(rm._predicted_risks[s_idx])
            cat = rm._categorize_risk(risk_val)
            road_num = int(rm._road_numbers[s_idx])
            road_name = f"A{road_num}" if road_num > 0 else "Unclassified"

            risks.append(risk_val)
            if risk_val >= 0.10:
                critical_count += 1
                high_risk_roads.add(road_name)
            elif risk_val >= 0.08:
                high_count += 1
                high_risk_roads.add(road_name)

            matched_records.append(
                MatchedSegmentSchema(
                    edge_id=int(rm._edge_ids[s_idx]),
                    road_number=road_num,
                    start_lat=float(rm._start_lats[s_idx]),
                    start_lon=float(rm._start_lons[s_idx]),
                    end_lat=float(rm._end_lats[s_idx]),
                    end_lon=float(rm._end_lons[s_idx]),
                    predicted_risk=round(risk_val, 4),
                    risk_category=cat,
                    distance_to_route_m=round(dist_m, 1),
                )
            )

        # Sort by predicted risk descending
        matched_records.sort(key=lambda r: r.predicted_risk, reverse=True)

        avg_risk = float(np.mean(risks)) if risks else None
        peak_risk = float(np.max(risks)) if risks else None
        top_records = matched_records[:10]

        return HistoricalRiskEvidenceSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            segments_on_route=len(matched_records),
            critical_segments_count=critical_count,
            high_risk_segments_count=high_count,
            average_gnn_risk=round(avg_risk, 4) if avg_risk is not None else None,
            peak_gnn_risk=round(peak_risk, 4) if peak_risk is not None else None,
            high_risk_corridors=sorted(high_risk_roads),
            matched_segments=top_records,
            description=(
                f"Traversed {len(matched_records)} GNN road segments along corridor "
                f"({critical_count} critical, {high_count} high risk, peak risk: {peak_risk:.3f})."
            ),
        )

    def get_student_a_evidence(self) -> HistoricalSeverityEvidenceSchema:
        """Provide truthful explanation of Student A model applicability for corridor traversal."""
        return HistoricalSeverityEvidenceSchema(
            status=DataAvailabilityStatus.UNAVAILABLE,
            predicted_severity=None,
            confidence=None,
            probabilities=None,
            reason=(
                "Student A RandomForest model predicts individual collision severity outcomes given "
                "specific crash-level parameters (vehicles involved, casualty counts, impact characteristics) "
                "rather than prospective corridor traversal risk. It is not applicable for route corridor "
                "spatial matching without fabricating hypothetical collision inputs."
            ),
        )

    def evaluate_historical_evidence(
        self, route: RouteInfoSchema
    ) -> tuple[HistoricalEvidenceSchema, bool, bool, bool]:
        """Perform comprehensive spatial corridor evaluation against Students A, B, and C."""
        # 1. Geographic coverage evaluation
        is_supported, cov_status, cov_reason = self.check_coverage(route)

        coverage_schema = HistoricalCoverageSchema(
            supported=is_supported,
            status=cov_status,
            region="Great Britain (UK)",
            reason=cov_reason,
        )

        matching_metadata = CorridorMatchingMetadataSchema(
            corridor_radius_m=self.corridor_radius_m,
            method="Spherical BallTree (Haversine distance from route geometry)",
            route_waypoints_count=len(route.geometry.coordinates) if route.geometry else 0,
        )

        student_a_evidence = self.get_student_a_evidence()

        # If outside geographic coverage, truthfully mark as unavailable without extrapolating UK models
        if not is_supported:
            logger.info("Route is outside historical model coverage: %s", cov_reason)
            evidence = HistoricalEvidenceSchema(
                status=DataAvailabilityStatus.UNAVAILABLE,
                coverage=coverage_schema,
                matching=matching_metadata,
                student_a=student_a_evidence,
                student_b=HistoricalHotspotEvidenceSchema(
                    status=DataAvailabilityStatus.UNAVAILABLE,
                    hotspots_on_route=0,
                    total_historical_accidents=0,
                    cluster_ids=[],
                    highest_cluster_density=None,
                    matched_hotspots=[],
                    description="Route lies outside historical UK model coverage.",
                ),
                student_c=HistoricalRiskEvidenceSchema(
                    status=DataAvailabilityStatus.UNAVAILABLE,
                    segments_on_route=0,
                    critical_segments_count=0,
                    high_risk_segments_count=0,
                    average_gnn_risk=None,
                    peak_gnn_risk=None,
                    high_risk_corridors=[],
                    matched_segments=[],
                    description="Route lies outside historical UK model coverage.",
                ),
                summary=(
                    "Historical model evidence is unavailable because the requested journey "
                    "lies outside the geographic coverage of the historical UK road safety models."
                ),
            )
            return evidence, False, False, False

        # 2. Match Student B Hotspots
        hotspot_evidence = self.match_hotspots(route, self.corridor_radius_m)

        # 3. Match Student C Segments
        risk_evidence = self.match_segments(route, self.corridor_radius_m)

        # 4. Determine overall historical status
        overall_status = cov_status  # AVAILABLE or PARTIAL

        summary = (
            f"Historical corridor analysis within {self.corridor_radius_m:.0f}m buffer: "
            f"{hotspot_evidence.hotspots_on_route} DBSCAN hotspot clusters matched "
            f"({hotspot_evidence.total_historical_accidents:,} historical crashes); "
            f"{risk_evidence.segments_on_route} GNN road segments analyzed "
            f"({risk_evidence.critical_segments_count} critical, {risk_evidence.high_risk_segments_count} high risk). "
            "Student A is not applicable to corridor traversal."
        )

        evidence = HistoricalEvidenceSchema(
            status=overall_status,
            coverage=coverage_schema,
            matching=matching_metadata,
            student_a=student_a_evidence,
            student_b=hotspot_evidence,
            student_c=risk_evidence,
            summary=summary,
        )

        student_b_used = hotspot_evidence.status == DataAvailabilityStatus.AVAILABLE
        student_c_used = risk_evidence.status == DataAvailabilityStatus.AVAILABLE
        student_a_used = False

        return evidence, student_a_used, student_b_used, student_c_used
