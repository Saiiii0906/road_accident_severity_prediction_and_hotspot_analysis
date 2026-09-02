from datetime import date, time
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock

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
    IncidentContextSchema,
    JourneyAnalyzeRequest,
    LiveContextProvidersSchema,
    LiveContextSchema,
    MatchedHotspotSchema,
    MatchedSegmentSchema,
    RouteGeometrySchema,
    RouteInfoSchema,
    RouteSegmentSchema,
    SafetyAssessmentSchema,
    TrafficContextSchema,
    WeatherContextSchema,
)
from app.services.journey_service import JourneyService
from app.services.safety_assessment_service import SafetyAssessmentService


class TestDeterministicSafetyAssessment(unittest.TestCase):
    """Test suite covering Phase 4D deterministic, evidence-based journey safety assessment."""

    def setUp(self) -> None:
        self.service = SafetyAssessmentService()

        # Canonical UK Route
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

        # Full Live Context
        self.full_live = LiveContextSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            weather=WeatherContextSchema(
                status=DataAvailabilityStatus.AVAILABLE,
                condition="Overcast",
                temperature_c=16.5,
                precipitation_probability=20,
                precipitation_mm=0.0,
                wind_speed_kmh=14.0,
                visibility="Good",
                precipitation_risk="Low",
                location_name="Hounslow",
            ),
            traffic=TrafficContextSchema(
                status=DataAvailabilityStatus.AVAILABLE,
                congestion_level="moderate",
                delay_minutes=6,
                description="Moderate congestion along A4 Westbound (+6 min delay).",
                corridor_monitored="A4",
            ),
            incidents=[
                IncidentContextSchema(
                    incident_id="TFL-1001",
                    description="Lane closure due to roadworks on A4 Great West Road.",
                    severity="Moderate",
                    category="Works",
                    location="A4 Chiswick",
                )
            ],
            providers=LiveContextProvidersSchema(
                weather="Open-Meteo",
                traffic="TfL",
                incidents="TfL",
            ),
        )

        # Full Historical Context
        self.full_historical = HistoricalEvidenceSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            coverage=HistoricalCoverageSchema(
                supported=True,
                status=DataAvailabilityStatus.AVAILABLE,
                region="Great Britain (UK)",
                reason="Route within UK coverage.",
            ),
            matching=CorridorMatchingMetadataSchema(
                corridor_radius_m=1000.0,
                method="Spherical BallTree",
                route_waypoints_count=4,
            ),
            student_a=HistoricalSeverityEvidenceSchema(
                status=DataAvailabilityStatus.UNAVAILABLE,
                reason="Student A RandomForest model predicts individual collision severity outcomes...",
            ),
            student_b=HistoricalHotspotEvidenceSchema(
                status=DataAvailabilityStatus.AVAILABLE,
                hotspots_on_route=2,
                total_historical_accidents=85,
                highest_cluster_density=52,
                matched_hotspots=[
                    MatchedHotspotSchema(
                        cluster_id=45,
                        latitude=51.4900,
                        longitude=-0.2000,
                        total_accidents=52,
                        fatal_count=1,
                        serious_count=10,
                        slight_count=41,
                        dominant_severity="Slight",
                        dominant_weather="Fine",
                        dominant_road_type="Dual Carriageway",
                        distance_to_route_m=150.0,
                    )
                ],
            ),
            student_c=HistoricalRiskEvidenceSchema(
                status=DataAvailabilityStatus.AVAILABLE,
                segments_on_route=120,
                critical_segments_count=2,
                high_risk_segments_count=5,
                peak_gnn_risk=0.1042,
                high_risk_corridors=["A4"],
                matched_segments=[
                    MatchedSegmentSchema(
                        edge_id=2001,
                        road_number=4,
                        start_lat=51.4900,
                        start_lon=-0.2000,
                        end_lat=51.4910,
                        end_lon=-0.2010,
                        predicted_risk=0.1042,
                        risk_category="Critical",
                        distance_to_route_m=80.0,
                    )
                ],
            ),
        )

    # ==========================================================================
    # Live Data Variations (1-3)
    # ==========================================================================

    def test_01_all_live_data_available(self) -> None:
        """1. Assessment factors in traffic, weather, and incidents when all are available."""
        assessment = self.service.assess(self.uk_route, self.full_live, self.full_historical)

        self.assertEqual(assessment.status, DataAvailabilityStatus.AVAILABLE)
        factors = {f.factor: f for f in assessment.key_factors}
        self.assertIn("live_traffic", factors)
        self.assertIn("live_weather", factors)
        self.assertIn("active_disruptions", factors)
        self.assertEqual(factors["live_traffic"].severity, "moderate")
        self.assertIn("+6 min delay", factors["live_traffic"].description)

    def test_02_partial_live_data(self) -> None:
        """2. Partial live feeds are handled gracefully and missing feeds noted in limitations."""
        partial_live = LiveContextSchema(
            status=DataAvailabilityStatus.PARTIAL,
            weather=self.full_live.weather,
            traffic=None,
            incidents=[],
            providers=LiveContextProvidersSchema(weather="Open-Meteo", traffic=None, incidents=None),
        )
        assessment = self.service.assess(self.uk_route, partial_live, self.full_historical)

        self.assertEqual(assessment.status, DataAvailabilityStatus.PARTIAL)
        self.assertEqual(assessment.data_coverage.weather, DataAvailabilityStatus.AVAILABLE)
        self.assertEqual(assessment.data_coverage.traffic, DataAvailabilityStatus.UNAVAILABLE)
        limitations_text = " ".join(assessment.limitations).lower()
        self.assertIn("traffic monitoring is unavailable", limitations_text)

    def test_03_no_live_data(self) -> None:
        """3. When no live feeds are available, assessment marks status PARTIAL and records limitations."""
        no_live = LiveContextSchema(
            status=DataAvailabilityStatus.UNAVAILABLE,
            weather=None,
            traffic=None,
            incidents=[],
            providers=None,
        )
        assessment = self.service.assess(self.uk_route, no_live, self.full_historical)

        self.assertEqual(assessment.status, DataAvailabilityStatus.PARTIAL)
        limitations_text = " ".join(assessment.limitations).lower()
        self.assertIn("weather forecast is unavailable", limitations_text)
        self.assertIn("traffic monitoring is unavailable", limitations_text)

    # ==========================================================================
    # Historical Coverage Variations (4-6)
    # ==========================================================================

    def test_04_historical_coverage_available(self) -> None:
        """4. Historical coverage available includes Student B & C empirical factors."""
        assessment = self.service.assess(self.uk_route, self.full_live, self.full_historical)

        self.assertEqual(assessment.data_coverage.historical, DataAvailabilityStatus.AVAILABLE)
        factors = {f.factor: f for f in assessment.key_factors}
        self.assertIn("historical_hotspots", factors)
        self.assertIn("topological_road_risk", factors)

    def test_05_historical_coverage_partial(self) -> None:
        """5. Partial historical coverage marks assessment status as PARTIAL."""
        partial_historical = self.full_historical.model_copy()
        partial_historical.status = DataAvailabilityStatus.PARTIAL
        partial_historical.coverage = HistoricalCoverageSchema(
            supported=True,
            status=DataAvailabilityStatus.PARTIAL,
            region="Great Britain (UK)",
            reason="Route partially intersects UK bounds.",
        )
        assessment = self.service.assess(self.uk_route, self.full_live, partial_historical)

        self.assertEqual(assessment.status, DataAvailabilityStatus.PARTIAL)
        self.assertEqual(assessment.data_coverage.historical, DataAvailabilityStatus.PARTIAL)

    def test_06_historical_coverage_unavailable(self) -> None:
        """6. When historical coverage is unavailable, B/C factors are excluded and limitation is recorded."""
        unavailable_historical = HistoricalEvidenceSchema(
            status=DataAvailabilityStatus.UNAVAILABLE,
            coverage=HistoricalCoverageSchema(
                supported=False,
                status=DataAvailabilityStatus.UNAVAILABLE,
                region="Great Britain (UK)",
                reason="Route is outside historical UK model coverage.",
            ),
        )
        assessment = self.service.assess(self.uk_route, self.full_live, unavailable_historical)

        self.assertEqual(assessment.status, DataAvailabilityStatus.PARTIAL)
        factors = {f.factor: f for f in assessment.key_factors}
        self.assertNotIn("historical_hotspots", factors)
        self.assertNotIn("topological_road_risk", factors)
        limitations_text = " ".join(assessment.limitations).lower()
        self.assertIn("historical model evidence is unavailable", limitations_text)

    # ==========================================================================
    # Student B & Student C Specifics (7-10)
    # ==========================================================================

    def test_07_student_b_hotspot_evidence(self) -> None:
        """7. Positive Student B matches yield structured factor with cluster count and peak density."""
        assessment = self.service.assess(self.uk_route, self.full_live, self.full_historical)
        factors = {f.factor: f for f in assessment.key_factors}

        self.assertIn("historical_hotspots", factors)
        self.assertEqual(factors["historical_hotspots"].severity, "high")
        self.assertIn("2 historical dbscan accident cluster(s)", factors["historical_hotspots"].description.lower())

    def test_08_zero_student_b_matches(self) -> None:
        """8. Zero matched hotspots explicitly states absence of clusters without claiming zero crashes."""
        hist_zero_b = self.full_historical.model_copy(deep=True)
        hist_zero_b.student_b.hotspots_on_route = 0
        hist_zero_b.student_b.total_historical_accidents = 0
        hist_zero_b.student_b.highest_cluster_density = None
        hist_zero_b.student_b.matched_hotspots = []

        assessment = self.service.assess(self.uk_route, self.full_live, hist_zero_b)
        factors = {f.factor: f for f in assessment.key_factors}

        self.assertIn("historical_hotspots", factors)
        self.assertEqual(factors["historical_hotspots"].severity, "low")
        self.assertIn("not necessarily zero historical accidents", factors["historical_hotspots"].description.lower())

    def test_09_student_c_high_risk_segments(self) -> None:
        """9. Student C critical segments escalate severity to critical and identify road corridors."""
        assessment = self.service.assess(self.uk_route, self.full_live, self.full_historical)
        factors = {f.factor: f for f in assessment.key_factors}

        self.assertIn("topological_road_risk", factors)
        self.assertEqual(factors["topological_road_risk"].severity, "critical")
        self.assertIn("A4", factors["topological_road_risk"].description)

    def test_10_zero_student_c_matches(self) -> None:
        """10. Zero matched GNN segments clarifies absence of mapped links rather than claiming safety."""
        hist_zero_c = self.full_historical.model_copy(deep=True)
        hist_zero_c.student_c.segments_on_route = 0
        hist_zero_c.student_c.critical_segments_count = 0
        hist_zero_c.student_c.high_risk_segments_count = 0
        hist_zero_c.student_c.peak_gnn_risk = None
        hist_zero_c.student_c.high_risk_corridors = []
        hist_zero_c.student_c.matched_segments = []

        assessment = self.service.assess(self.uk_route, self.full_live, hist_zero_c)
        factors = {f.factor: f for f in assessment.key_factors}

        self.assertIn("topological_road_risk", factors)
        self.assertEqual(factors["topological_road_risk"].severity, "unknown")
        self.assertIn("not low risk", factors["topological_road_risk"].description.lower())

    # ==========================================================================
    # Methodological Integrity (11-14)
    # ==========================================================================

    def test_11_student_a_excluded_from_route_risk(self) -> None:
        """11. Student A collision-level model is excluded from route risk with explicit limitation."""
        assessment = self.service.assess(self.uk_route, self.full_live, self.full_historical)
        factors = [f.factor for f in assessment.key_factors]

        self.assertNotIn("severity_model", factors)
        self.assertNotIn("student_a", factors)
        limitations_text = " ".join(assessment.limitations).lower()
        self.assertIn("student a randomforest model predicts individual collision severity", limitations_text)

    def test_12_no_arbitrary_score(self) -> None:
        """12. overall_score is strictly None because no defensible composite formula exists."""
        assessment = self.service.assess(self.uk_route, self.full_live, self.full_historical)
        self.assertIsNone(assessment.overall_score)

    def test_13_no_arbitrary_thresholds(self) -> None:
        """13. Route-wide safety level remains None to avoid arbitrary thresholding."""
        assessment = self.service.assess(self.uk_route, self.full_live, self.full_historical)
        self.assertIsNone(assessment.level)

    def test_14_structured_key_factors(self) -> None:
        """14. Key factors are structured records with valid severity, title, and source."""
        assessment = self.service.assess(self.uk_route, self.full_live, self.full_historical)

        for factor in assessment.key_factors:
            self.assertIn(factor.severity, ("critical", "high", "moderate", "low", "advisory", "informational", "unknown"))
            self.assertTrue(len(factor.title) > 0)
            self.assertTrue(len(factor.source) > 0)
            self.assertTrue(len(factor.description) > 0)

    # ==========================================================================
    # Evidence Provenance & Limitations (15-18)
    # ==========================================================================

    def test_15_evidence_provenance(self) -> None:
        """15. Supporting evidence metrics include source, metric name, and interpretation."""
        assessment = self.service.assess(self.uk_route, self.full_live, self.full_historical)

        self.assertGreaterEqual(len(assessment.supporting_evidence), 3)
        sources = {ev.source for ev in assessment.supporting_evidence}
        self.assertTrue(any("Open-Meteo" in s for s in sources))
        self.assertTrue(any("TfL" in s for s in sources))
        self.assertTrue(any("Student" in s for s in sources))

    def test_16_data_limitations(self) -> None:
        """16. Limitations section is populated with transparent methodological notes."""
        assessment = self.service.assess(self.uk_route, self.full_live, self.full_historical)

        self.assertGreaterEqual(len(assessment.limitations), 1)
        self.assertTrue(any("Student A" in lim for lim in assessment.limitations))

    def test_17_response_schema_validation(self) -> None:
        """17. SafetyAssessment validates cleanly through Pydantic without type errors."""
        assessment = self.service.assess(self.uk_route, self.full_live, self.full_historical)

        self.assertIsInstance(assessment, SafetyAssessmentSchema)
        # Test serialization and roundtrip
        json_data = assessment.model_dump()
        roundtrip = SafetyAssessmentSchema.model_validate(json_data)
        self.assertEqual(roundtrip.status, assessment.status)

    def test_18_out_of_coverage_assessment(self) -> None:
        """18. Out-of-coverage journey produces an honest assessment with coverage constraints."""
        outside_historical = HistoricalEvidenceSchema(
            status=DataAvailabilityStatus.UNAVAILABLE,
            coverage=HistoricalCoverageSchema(
                supported=False,
                status=DataAvailabilityStatus.UNAVAILABLE,
                region="Great Britain (UK)",
                reason="Route is outside historical UK model coverage.",
            ),
        )
        assessment = self.service.assess(self.uk_route, self.full_live, outside_historical)

        self.assertEqual(assessment.status, DataAvailabilityStatus.PARTIAL)
        self.assertEqual(assessment.data_coverage.historical, DataAvailabilityStatus.UNAVAILABLE)
        self.assertIsNone(assessment.overall_score)
        self.assertIsNone(assessment.level)
        self.assertTrue(any("outside the geographic coverage" in lim.lower() for lim in assessment.limitations))


if __name__ == "__main__":
    unittest.main()

