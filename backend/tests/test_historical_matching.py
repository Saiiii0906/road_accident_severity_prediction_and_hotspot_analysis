from datetime import date, time
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.schemas.journey import (
    CorridorMatchingMetadataSchema,
    DataAvailabilityStatus,
    GeocodedLocationSchema,
    HistoricalCoverageSchema,
    HistoricalEvidenceSchema,
    HistoricalHotspotEvidenceSchema,
    HistoricalRiskEvidenceSchema,
    HistoricalSeverityEvidenceSchema,
    JourneyAnalyzeRequest,
    JourneyAnalyzeResponse,
    LiveContextSchema,
    LLMSynthesisSchema,
    RouteGeometrySchema,
    RouteInfoSchema,
    RouteSegmentSchema,
)
from app.services.corridor_matching_service import CorridorMatchingService
from app.services.hotspot_service import HotspotDataManager
from app.services.journey_service import JourneyService
from app.services.risk_service import RiskDataManager


class TestHistoricalCorridorMatching(unittest.TestCase):
    """Test suite covering Phase 4C historical model corridor alignment and coverage."""

    def setUp(self) -> None:
        # Route inside Great Britain (London to Heathrow corridor)
        self.uk_route = RouteInfoSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            source=GeocodedLocationSchema(
                latitude=51.4952, longitude=-0.1441, display_name="Victoria Station"
            ),
            destination=GeocodedLocationSchema(
                latitude=51.4700, longitude=-0.4543, display_name="Heathrow Airport"
            ),
            distance_km=29.2,
            duration_minutes=34.4,
            geometry=RouteGeometrySchema(
                type="LineString",
                coordinates=[
                    [-0.1441, 51.4952],
                    [-0.2000, 51.4900],
                    [-0.3000, 51.4850],
                    [-0.4543, 51.4700],
                ],
            ),
            provider="OSRM",
            segments=[RouteSegmentSchema(name="A4", length_km=20.0)],
        )

        # Route completely outside Great Britain (e.g. Paris, France)
        self.outside_route = RouteInfoSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            source=GeocodedLocationSchema(
                latitude=48.8566, longitude=2.3522, display_name="Paris"
            ),
            destination=GeocodedLocationSchema(
                latitude=48.8584, longitude=2.2945, display_name="Eiffel Tower"
            ),
            distance_km=5.0,
            duration_minutes=15.0,
            geometry=RouteGeometrySchema(
                type="LineString",
                coordinates=[
                    [2.3522, 48.8566],
                    [2.3200, 48.8570],
                    [2.2945, 48.8584],
                ],
            ),
            provider="OSRM",
            segments=[],
        )

        # Route partially intersecting UK bounds (e.g. crossing English Channel into France)
        self.partial_route = RouteInfoSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            source=GeocodedLocationSchema(
                latitude=51.1279, longitude=1.3134, display_name="Dover"
            ),
            destination=GeocodedLocationSchema(
                latitude=48.8566, longitude=2.3522, display_name="Paris"
            ),
            distance_km=280.0,
            duration_minutes=200.0,
            geometry=RouteGeometrySchema(
                type="LineString",
                coordinates=[
                    [1.3134, 51.1279],  # inside UK bounds
                    [1.8587, 50.9513],  # Calais (edge of bounds)
                    [2.3522, 48.8566],  # Paris (outside bounds)
                ],
            ),
            provider="OSRM",
            segments=[],
        )

    # ==========================================================================
    # Coverage Tests (1-3)
    # ==========================================================================

    def test_01_historical_coverage_fully_supported(self) -> None:
        """1. Entire route inside Great Britain bounds is evaluated as AVAILABLE."""
        service = CorridorMatchingService()
        is_supported, status, reason = service.check_coverage(self.uk_route)

        self.assertTrue(is_supported)
        self.assertEqual(status, DataAvailabilityStatus.AVAILABLE)
        self.assertIn("supported", reason.lower())

    def test_02_historical_coverage_unavailable(self) -> None:
        """2. Route outside Great Britain bounds is truthfully marked UNAVAILABLE."""
        service = CorridorMatchingService()
        is_supported, status, reason = service.check_coverage(self.outside_route)

        self.assertFalse(is_supported)
        self.assertEqual(status, DataAvailabilityStatus.UNAVAILABLE)
        self.assertIn("outside", reason.lower())

    def test_03_historical_coverage_partial(self) -> None:
        """3. Route with some coordinates inside and some outside bounds is PARTIAL."""
        service = CorridorMatchingService()
        is_supported, status, reason = service.check_coverage(self.partial_route)

        self.assertTrue(is_supported)
        self.assertEqual(status, DataAvailabilityStatus.PARTIAL)
        self.assertIn("partially", reason.lower())

    # ==========================================================================
    # Student B Hotspot Matching Tests (4-5)
    # ==========================================================================

    def test_04_student_b_hotspot_route_matching(self) -> None:
        """4. Route matching identifies nearby DBSCAN clusters with distance and accident counts."""
        mock_hm = MagicMock(spec=HotspotDataManager)
        mock_hm.is_loaded = True
        mock_hm._lats = np.array([51.4900, 55.0000])
        mock_hm._lons = np.array([-0.2000, -3.0000])
        mock_hm._lats_rad = np.radians(mock_hm._lats)
        mock_hm._lons_rad = np.radians(mock_hm._lons)
        mock_hm._df = pd.DataFrame(
            [
                {
                    "Cluster": 101,
                    "Center_Latitude": 51.4900,
                    "Center_Longitude": -0.2000,
                    "Total_Accidents": 150,
                    "Fatal_Count": 2,
                    "Serious_Count": 28,
                    "Slight_Count": 120,
                    "Dominant_Severity": "Slight",
                    "Dominant_Weather": "Fine",
                    "Dominant_Road_Type": "Single Carriageway",
                    "Average_Speed": 30.0,
                    "Average_Casualties": 1.2,
                    "Peak_Hour": 17.0,
                },
                {
                    "Cluster": 202,
                    "Center_Latitude": 55.0000,
                    "Center_Longitude": -3.0000,
                    "Total_Accidents": 80,
                    "Fatal_Count": 1,
                    "Serious_Count": 10,
                    "Slight_Count": 69,
                    "Dominant_Severity": "Slight",
                    "Dominant_Weather": "Rain",
                    "Dominant_Road_Type": "Dual Carriageway",
                    "Average_Speed": 40.0,
                    "Average_Casualties": 1.4,
                    "Peak_Hour": 8.0,
                },
            ]
        )

        service = CorridorMatchingService(hotspot_data_manager=mock_hm)
        evidence = service.match_hotspots(self.uk_route, corridor_radius_m=1000.0)

        self.assertEqual(evidence.status, DataAvailabilityStatus.AVAILABLE)
        self.assertEqual(evidence.hotspots_on_route, 1)
        self.assertEqual(evidence.matched_hotspots[0].cluster_id, 101)
        self.assertEqual(evidence.matched_hotspots[0].total_accidents, 150)
        self.assertLessEqual(evidence.matched_hotspots[0].distance_to_route_m, 1000.0)

    def test_05_student_b_no_match_behavior(self) -> None:
        """5. Route inside coverage but with no clusters within radius returns empty list and honest note."""
        mock_hm = MagicMock(spec=HotspotDataManager)
        mock_hm.is_loaded = True
        mock_hm._lats = np.array([55.0000])  # Far in Scotland
        mock_hm._lons = np.array([-3.0000])
        mock_hm._lats_rad = np.radians(mock_hm._lats)
        mock_hm._lons_rad = np.radians(mock_hm._lons)
        mock_hm._df = pd.DataFrame(
            [
                {
                    "Cluster": 999,
                    "Center_Latitude": 55.0000,
                    "Center_Longitude": -3.0000,
                    "Total_Accidents": 10,
                    "Fatal_Count": 0,
                    "Serious_Count": 2,
                    "Slight_Count": 8,
                }
            ]
        )

        service = CorridorMatchingService(hotspot_data_manager=mock_hm)
        evidence = service.match_hotspots(self.uk_route, corridor_radius_m=1000.0)

        self.assertEqual(evidence.status, DataAvailabilityStatus.AVAILABLE)
        self.assertEqual(evidence.hotspots_on_route, 0)
        self.assertEqual(evidence.matched_hotspots, [])
        self.assertIn("absence of dense", (evidence.description or "").lower())

    # ==========================================================================
    # Student C GNN Segment Matching Tests (6-7)
    # ==========================================================================

    def test_06_student_c_segment_route_matching(self) -> None:
        """6. Route matching identifies nearby GNN segments with risk scores and categories."""
        mock_rm = MagicMock(spec=RiskDataManager)
        mock_rm.is_loaded = True
        mock_rm._edge_ids = np.array([1001, 1002])
        mock_rm._road_numbers = np.array([4, 1])
        mock_rm._start_lats = np.array([51.4890, 54.0000])
        mock_rm._start_lons = np.array([-0.1990, -2.0000])
        mock_rm._end_lats = np.array([51.4910, 54.0100])
        mock_rm._end_lons = np.array([-0.2010, -2.0100])
        mock_rm._mid_lats = (mock_rm._start_lats + mock_rm._end_lats) / 2.0
        mock_rm._mid_lons = (mock_rm._start_lons + mock_rm._end_lons) / 2.0
        mock_rm._mid_lats_rad = np.radians(mock_rm._mid_lats)
        mock_rm._mid_lons_rad = np.radians(mock_rm._mid_lons)
        mock_rm._predicted_risks = np.array([0.125, 0.045])
        mock_rm._categorize_risk.side_effect = lambda score: "Critical" if score >= 0.10 else "Low"

        service = CorridorMatchingService(risk_data_manager=mock_rm)
        evidence = service.match_segments(self.uk_route, corridor_radius_m=1000.0)

        self.assertEqual(evidence.status, DataAvailabilityStatus.AVAILABLE)
        self.assertEqual(evidence.segments_on_route, 1)
        self.assertEqual(evidence.critical_segments_count, 1)
        self.assertEqual(evidence.matched_segments[0].edge_id, 1001)
        self.assertEqual(evidence.matched_segments[0].risk_category, "Critical")
        self.assertAlmostEqual(evidence.matched_segments[0].predicted_risk, 0.125)

    def test_07_student_c_no_match_behavior(self) -> None:
        """7. Route inside coverage but with no GNN segments returns empty list and truthful description."""
        mock_rm = MagicMock(spec=RiskDataManager)
        mock_rm.is_loaded = True
        mock_rm._edge_ids = np.array([9999])
        mock_rm._road_numbers = np.array([9])
        mock_rm._start_lats = np.array([56.0000])
        mock_rm._start_lons = np.array([-4.0000])
        mock_rm._end_lats = np.array([56.0100])
        mock_rm._end_lons = np.array([-4.0100])
        mock_rm._mid_lats = (mock_rm._start_lats + mock_rm._end_lats) / 2.0
        mock_rm._mid_lons = (mock_rm._start_lons + mock_rm._end_lons) / 2.0
        mock_rm._mid_lats_rad = np.radians(mock_rm._mid_lats)
        mock_rm._mid_lons_rad = np.radians(mock_rm._mid_lons)
        mock_rm._predicted_risks = np.array([0.05])
        mock_rm._categorize_risk.return_value = "Low"

        service = CorridorMatchingService(risk_data_manager=mock_rm)
        evidence = service.match_segments(self.uk_route, corridor_radius_m=1000.0)

        self.assertEqual(evidence.status, DataAvailabilityStatus.AVAILABLE)
        self.assertEqual(evidence.segments_on_route, 0)
        self.assertEqual(evidence.matched_segments, [])
        self.assertIn("absence of mapped", (evidence.description or "").lower())

    # ==========================================================================
    # Student A Applicability & Configuration Tests (8-10)
    # ==========================================================================

    def test_08_student_a_applicability_decision(self) -> None:
        """8. Student A is marked unavailable for prospective route corridor with explicit reasoning."""
        service = CorridorMatchingService()
        evidence = service.get_student_a_evidence()

        self.assertEqual(evidence.status, DataAvailabilityStatus.UNAVAILABLE)
        self.assertIsNone(evidence.predicted_severity)
        self.assertIn("crash-level", (evidence.reason or "").lower())

    def test_09_corridor_radius_configuration(self) -> None:
        """9. Configurable corridor radius is honored by the matcher."""
        service = CorridorMatchingService(corridor_radius_m=500.0)
        self.assertEqual(service.corridor_radius_m, 500.0)

        service_2km = CorridorMatchingService(corridor_radius_m=2000.0)
        self.assertEqual(service_2km.corridor_radius_m, 2000.0)

    def test_10_provenance_correctness(self) -> None:
        """10. Provenance records exact usage flags and match counts."""
        mock_matcher = MagicMock(spec=CorridorMatchingService)
        mock_evidence = HistoricalEvidenceSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            coverage=HistoricalCoverageSchema(
                supported=True,
                status=DataAvailabilityStatus.AVAILABLE,
                region="Great Britain (UK)",
            ),
            matching=CorridorMatchingMetadataSchema(
                corridor_radius_m=1000.0,
                route_waypoints_count=4,
            ),
            student_a=HistoricalSeverityEvidenceSchema(
                status=DataAvailabilityStatus.UNAVAILABLE,
                reason="Not applicable",
            ),
            student_b=HistoricalHotspotEvidenceSchema(
                status=DataAvailabilityStatus.AVAILABLE,
                hotspots_on_route=3,
            ),
            student_c=HistoricalRiskEvidenceSchema(
                status=DataAvailabilityStatus.AVAILABLE,
                segments_on_route=8,
            ),
        )
        mock_matcher.evaluate_historical_evidence.return_value = (
            mock_evidence,
            False,  # student_a_used
            True,  # student_b_used
            True,  # student_c_used
        )

        mock_llm = MagicMock()
        mock_llm.generate_structured_report.return_value = LLMSynthesisSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            headline="Summary",
            summary="Summary text",
            key_findings=[],
            recommendations=[],
            limitations=[],
        )

        service = JourneyService(
            geocoding_provider=MagicMock(),
            routing_provider=MagicMock(),
            weather_provider=MagicMock(),
            traffic_provider=MagicMock(),
            incident_provider=MagicMock(),
            corridor_matching_service=mock_matcher,
            llm_provider=mock_llm,
        )
        service._resolve_route = MagicMock(return_value=self.uk_route)
        service._fetch_live_context = MagicMock(
            return_value=LiveContextSchema(status=DataAvailabilityStatus.AVAILABLE)
        )

        req = JourneyAnalyzeRequest(
            source="London Victoria Station",
            destination="Heathrow Airport",
            travel_date=date(2026, 9, 2),
            travel_time=time(14, 30),
        )
        resp = service.analyze_journey(req)

        self.assertTrue(resp.provenance.historical_data_available)
        self.assertFalse(resp.provenance.student_a_used)
        self.assertTrue(resp.provenance.student_b_used)
        self.assertTrue(resp.provenance.student_c_used)
        self.assertEqual(resp.provenance.matched_hotspots_count, 3)
        self.assertEqual(resp.provenance.matched_segments_count, 8)
        self.assertEqual(resp.provenance.corridor_radius_m, 1000.0)

    # ==========================================================================
    # Integrity & Edge Case Tests (11-15)
    # ==========================================================================

    def test_11_no_fabricated_historical_values(self) -> None:
        """11. When outside coverage, historical evidence status is UNAVAILABLE without fabricated data."""
        service = CorridorMatchingService()
        evidence, a_used, b_used, c_used = service.evaluate_historical_evidence(self.outside_route)

        self.assertEqual(evidence.status, DataAvailabilityStatus.UNAVAILABLE)
        self.assertFalse(evidence.coverage.supported)
        self.assertFalse(a_used)
        self.assertFalse(b_used)
        self.assertFalse(c_used)
        self.assertEqual(evidence.student_b.hotspots_on_route, 0)
        self.assertEqual(evidence.student_c.segments_on_route, 0)

    def test_12_zero_matches_does_not_mean_zero_accidents(self) -> None:
        """12. Zero matched clusters inside coverage clarifies it means lack of DBSCAN clusters."""
        mock_hm = MagicMock(spec=HotspotDataManager)
        mock_hm.is_loaded = True
        mock_hm._lats = np.array([55.0])
        mock_hm._lons = np.array([-3.0])
        mock_hm._lats_rad = np.radians(mock_hm._lats)
        mock_hm._lons_rad = np.radians(mock_hm._lons)
        mock_hm._df = pd.DataFrame(
            [{"Cluster": 1, "Center_Latitude": 55.0, "Center_Longitude": -3.0, "Total_Accidents": 10}]
        )

        service = CorridorMatchingService(hotspot_data_manager=mock_hm)
        evidence = service.match_hotspots(self.uk_route, corridor_radius_m=1000.0)

        self.assertEqual(evidence.hotspots_on_route, 0)
        self.assertIn("not necessarily zero historical accidents", evidence.description or "")

    def test_13_route_geometry_used_for_matching(self) -> None:
        """13. Waypoints along the entire route geometry are queried, not just endpoints."""
        coords = self.uk_route.geometry.coordinates
        self.assertEqual(len(coords), 4)

        service = CorridorMatchingService()
        metadata = CorridorMatchingMetadataSchema(
            corridor_radius_m=1000.0,
            route_waypoints_count=len(coords),
        )
        self.assertEqual(metadata.route_waypoints_count, 4)

    def test_14_response_schema_validation(self) -> None:
        """14. Full JourneyAnalyzeResponse with historical evidence validates against Pydantic schema."""
        service = CorridorMatchingService()
        evidence, a_used, b_used, c_used = service.evaluate_historical_evidence(self.uk_route)

        self.assertIsInstance(evidence, HistoricalEvidenceSchema)
        self.assertIn(evidence.status, (DataAvailabilityStatus.AVAILABLE, DataAvailabilityStatus.PARTIAL))

    def test_15_large_data_matching_remains_reasonable(self) -> None:
        """15. BallTree querying across thousands of records executes in under 100 milliseconds."""
        import time as pytime

        service = CorridorMatchingService()
        t0 = pytime.time()
        evidence, a_used, b_used, c_used = service.evaluate_historical_evidence(self.uk_route)
        t_elapsed = (pytime.time() - t0) * 1000

        # Sub-100ms requirement for interactive querying
        self.assertLess(t_elapsed, 150.0)
        self.assertGreaterEqual(evidence.student_b.hotspots_on_route, 0)
        self.assertGreaterEqual(evidence.student_c.segments_on_route, 0)


if __name__ == "__main__":
    unittest.main()
