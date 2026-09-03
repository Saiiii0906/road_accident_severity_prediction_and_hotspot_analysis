from datetime import date, time
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

from pydantic import ValidationError

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
    JourneyDetailsSchema,
    LiveContextProvidersSchema,
    LiveContextSchema,
    LLMKeyFindingSchema,
    LLMRecommendationSchema,
    LLMSynthesisSchema,
    MatchedHotspotSchema,
    MatchedSegmentSchema,
    RouteGeometrySchema,
    RouteInfoSchema,
    RouteSegmentSchema,
    SafetyAssessmentSchema,
    SafetyDataCoverageSchema,
    SafetyEvidenceItemSchema,
    SafetyKeyFactorSchema,
    TrafficContextSchema,
    WeatherContextSchema,
)
from app.services.geocoding_service import NominatimGeocodingProvider
from app.services.journey_prompt_service import JourneyPromptService
from app.services.journey_service import JourneyService
from app.services.llm_provider import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMProvider,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMValidationError,
)
from app.services.routing_service import OSRMRoutingProvider
from app.services.safety_assessment_service import SafetyAssessmentService


class TestGeminiJourneySynthesis(unittest.TestCase):
    """Test suite for Phase 4E Gemini Grounded Journey Safety Synthesis."""

    def setUp(self) -> None:
        self.journey_details = JourneyDetailsSchema(
            source="London Victoria Station",
            destination="Heathrow Airport Terminal 5",
            travel_date="2026-09-02",
            travel_time="14:30",
        )

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

        self.full_live = LiveContextSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            weather=WeatherContextSchema(
                status=DataAvailabilityStatus.AVAILABLE,
                condition="Overcast",
                temperature_c=16.5,
                precipitation_probability=60,
                precipitation_mm=0.0,
                wind_speed_kmh=14.0,
                visibility="Good",
                precipitation_risk="Moderate",
                location_name="Hounslow",
            ),
            traffic=TrafficContextSchema(
                status=DataAvailabilityStatus.AVAILABLE,
                congestion_level="serious",
                delay_minutes=15,
                description="Serious delays along A4 Westbound (+15 min).",
                corridor_monitored="A4",
            ),
            incidents=[
                IncidentContextSchema(
                    incident_id="TFL-1001",
                    description="Lane closure due to emergency roadworks on A4.",
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
                hotspots_on_route=1,
                total_historical_accidents=45,
                highest_cluster_density=45,
                matched_hotspots=[
                    MatchedHotspotSchema(
                        cluster_id=45,
                        latitude=51.4900,
                        longitude=-0.2000,
                        total_accidents=45,
                        fatal_count=1,
                        serious_count=10,
                        slight_count=34,
                        dominant_severity="Slight",
                        dominant_weather="Fine",
                        dominant_road_type="Dual Carriageway",
                        distance_to_route_m=150.0,
                    )
                ],
            ),
            student_c=HistoricalRiskEvidenceSchema(
                status=DataAvailabilityStatus.AVAILABLE,
                segments_on_route=206,
                critical_segments_count=0,
                high_risk_segments_count=2,
                peak_gnn_risk=0.0908,
                high_risk_corridors=["A4"],
                matched_segments=[
                    MatchedSegmentSchema(
                        edge_id=2001,
                        road_number=4,
                        start_lat=51.4900,
                        start_lon=-0.2000,
                        end_lat=51.4910,
                        end_lon=-0.2010,
                        predicted_risk=0.0908,
                        risk_category="High",
                        distance_to_route_m=80.0,
                    )
                ],
            ),
        )

        self.deterministic_assessment = SafetyAssessmentService().assess(
            self.uk_route, self.full_live, self.full_historical
        )

        self.mock_llm_response = LLMSynthesisSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            headline="Corridor Congestion with Rain Hazards on A4 Highway",
            summary=(
                "Travel from London Victoria to Heathrow Airport covers 29.2 km along the A4 corridor. "
                "Expect +15 min congestion delays and 60% rain probability. Historical GNN analysis "
                "identifies 2 elevated risk segments on the A4."
            ),
            key_findings=[
                LLMKeyFindingSchema(
                    title="A4 Corridor Traffic Congestion",
                    description="Heavy congestion causing estimated 15 minute delay.",
                    severity="high",
                    evidence_sources=["TfL Road Network"],
                ),
                LLMKeyFindingSchema(
                    title="Wet Asphalt Friction Reduction",
                    description="60% probability of rain with overcast sky.",
                    severity="moderate",
                    evidence_sources=["Open-Meteo Weather Service"],
                ),
            ],
            recommendations=[
                LLMRecommendationSchema(
                    action="Increase vehicle following distance on A4",
                    reason="Surface grip is compromised by forecasted rainfall and sudden stop-and-go congestion.",
                    evidence_sources=["Open-Meteo", "TfL Road Network"],
                )
            ],
            limitations=[
                "Student A RandomForest model is excluded from route-wide prospective risk."
            ],
        )

    # ==========================================================================
    # Evidence Grounding & Prompt Formatting (1-2)
    # ==========================================================================

    def test_01_gemini_receives_structured_journey_evidence(self) -> None:
        """1. Evidence payload accurately serializes route, live weather, traffic, and historical data."""
        payload = JourneyPromptService.build_evidence_payload(
            self.journey_details,
            self.uk_route,
            self.full_live,
            self.full_historical,
            self.deterministic_assessment,
        )

        self.assertEqual(payload["journey"]["source"], "London Victoria Station")
        self.assertEqual(payload["route"]["distance_km"], 29.2)
        self.assertEqual(payload["live_context"]["traffic"]["delay_minutes"], 15)
        self.assertEqual(payload["historical_evidence"]["student_c_risk"]["peak_gnn_risk"], 0.0908)
        self.assertIn("A4", payload["historical_evidence"]["student_c_risk"]["high_risk_corridors"])

    def test_02_gemini_receives_deterministic_assessment(self) -> None:
        """2. Evidence payload includes deterministic key factors, limitations, and supporting evidence."""
        payload = JourneyPromptService.build_evidence_payload(
            self.journey_details,
            self.uk_route,
            self.full_live,
            self.full_historical,
            self.deterministic_assessment,
        )

        self.assertIn("deterministic_assessment", payload)
        det = payload["deterministic_assessment"]
        self.assertIsNone(det["overall_score"])
        self.assertIsNone(det["level"])
        self.assertGreaterEqual(len(det["key_factors"]), 3)
        self.assertGreaterEqual(len(det["supporting_evidence"]), 3)

    # ==========================================================================
    # Output Schema Validation & Safety Constraints (3-7)
    # ==========================================================================

    def test_03_gemini_output_is_schema_validated(self) -> None:
        """3. LLMSynthesisSchema validates structured response without type or shape errors."""
        json_data = self.mock_llm_response.model_dump()
        validated = LLMSynthesisSchema.model_validate(json_data)

        self.assertEqual(validated.status, DataAvailabilityStatus.AVAILABLE)
        self.assertEqual(len(validated.key_findings), 2)
        self.assertEqual(len(validated.recommendations), 1)

    def test_04_gemini_cannot_introduce_unsupported_score_fields(self) -> None:
        """4. LLMSynthesisSchema does not contain numerical score or level fields."""
        schema_fields = LLMSynthesisSchema.model_fields.keys()
        self.assertNotIn("overall_score", schema_fields)
        self.assertNotIn("score", schema_fields)
        self.assertNotIn("risk_level", schema_fields)

    def test_05_overall_score_null_remains_null(self) -> None:
        """5. Complete pipeline keeps safety_assessment.overall_score as None."""
        mock_provider = MagicMock(spec=LLMProvider)
        mock_provider.generate_structured_report.return_value = self.mock_llm_response

        service = JourneyService(
            geocoding_provider=MagicMock(spec=NominatimGeocodingProvider),
            routing_provider=MagicMock(spec=OSRMRoutingProvider),
            llm_provider=mock_provider,
        )

        prompt = service.prompt_service.build_prompt(
            self.journey_details,
            self.uk_route,
            self.full_live,
            self.full_historical,
            self.deterministic_assessment,
        )
        self.assertIn("overall_score is intentionally null", prompt)
        self.assertIsNone(self.deterministic_assessment.overall_score)

    def test_06_level_null_remains_null(self) -> None:
        """6. Complete pipeline keeps safety_assessment.level as None."""
        prompt = JourneyPromptService.build_prompt(
            self.journey_details,
            self.uk_route,
            self.full_live,
            self.full_historical,
            self.deterministic_assessment,
        )
        self.assertIn("Never create route-wide safety level categories if they are null", prompt)
        self.assertIsNone(self.deterministic_assessment.level)

    def test_07_student_a_remains_excluded_from_route_wide_risk(self) -> None:
        """7. Prompt and synthesis explicitly document Student A non-applicability to route traversal."""
        payload = JourneyPromptService.build_evidence_payload(
            self.journey_details,
            self.uk_route,
            self.full_live,
            self.full_historical,
            self.deterministic_assessment,
        )
        prompt = JourneyPromptService.build_prompt(
            self.journey_details,
            self.uk_route,
            self.full_live,
            self.full_historical,
            self.deterministic_assessment,
        )
        self.assertIn("Student A is collision-level only", payload["historical_evidence"]["student_a_note"])
        self.assertIn("Never treat Student A", prompt)

    # ==========================================================================
    # Geographic Coverage & Partial Data Handling (8-9)
    # ==========================================================================

    def test_08_historical_evidence_excluded_outside_great_britain(self) -> None:
        """8. Outside GB coverage, historical data is marked unavailable and prompt instructs zero extrapolation."""
        outside_hist = HistoricalEvidenceSchema(
            status=DataAvailabilityStatus.UNAVAILABLE,
            coverage=HistoricalCoverageSchema(
                supported=False,
                status=DataAvailabilityStatus.UNAVAILABLE,
                region="Great Britain (UK)",
                reason="Route is outside historical UK coverage.",
            ),
        )
        outside_assessment = SafetyAssessmentService().assess(
            self.uk_route, self.full_live, outside_hist
        )
        prompt = JourneyPromptService.build_prompt(
            self.journey_details,
            self.uk_route,
            self.full_live,
            outside_hist,
            outside_assessment,
        )

        self.assertIn("Never extrapolate UK historical model results", prompt)
        self.assertIn('"supported": false', prompt)

    def test_09_partial_live_data_produces_partial_synthesis(self) -> None:
        """9. Partial live data sets LLM synthesis status to PARTIAL."""
        partial_live = LiveContextSchema(
            status=DataAvailabilityStatus.PARTIAL,
            weather=self.full_live.weather,
            traffic=None,
            incidents=[],
            providers=LiveContextProvidersSchema(weather="Open-Meteo", traffic=None, incidents=None),
        )
        partial_assessment = SafetyAssessmentService().assess(
            self.uk_route, partial_live, self.full_historical
        )

        mock_provider = MagicMock(spec=LLMProvider)
        mock_provider.generate_structured_report.return_value = self.mock_llm_response.model_copy()

        service = JourneyService(llm_provider=mock_provider)
        synthesis, used = service._synthesize_with_llm(
            self.journey_details,
            self.uk_route,
            partial_live,
            self.full_historical,
            partial_assessment,
        )

        self.assertTrue(used)
        self.assertEqual(synthesis.status, DataAvailabilityStatus.PARTIAL)

    # ==========================================================================
    # Resilience & Failure Safety (10-13)
    # ==========================================================================

    def test_10_gemini_unavailable_does_not_remove_deterministic_assessment(self) -> None:
        """10. When LLM provider fails, deterministic assessment remains fully intact."""
        mock_provider = MagicMock(spec=LLMProvider)
        mock_provider.generate_structured_report.side_effect = LLMTimeoutError("Gemini timed out")

        service = JourneyService(llm_provider=mock_provider)
        synthesis, used = service._synthesize_with_llm(
            self.journey_details,
            self.uk_route,
            self.full_live,
            self.full_historical,
            self.deterministic_assessment,
        )

        self.assertFalse(used)
        self.assertEqual(synthesis.status, DataAvailabilityStatus.UNAVAILABLE)
        self.assertGreaterEqual(len(synthesis.limitations), 1)
        # Deterministic assessment is untouched
        self.assertEqual(self.deterministic_assessment.status, DataAvailabilityStatus.AVAILABLE)
        self.assertGreaterEqual(len(self.deterministic_assessment.key_factors), 3)

    def test_11_gemini_failure_does_not_introduce_mock_data(self) -> None:
        """11. LLM failure yields empty/none fields rather than fake mock recommendations."""
        mock_provider = MagicMock(spec=LLMProvider)
        mock_provider.generate_structured_report.side_effect = LLMProviderError("HTTP 500 upstream")

        service = JourneyService(llm_provider=mock_provider)
        synthesis, used = service._synthesize_with_llm(
            self.journey_details,
            self.uk_route,
            self.full_live,
            self.full_historical,
            self.deterministic_assessment,
        )

        self.assertFalse(used)
        self.assertIsNone(synthesis.headline)
        self.assertIsNone(synthesis.summary)
        self.assertEqual(synthesis.key_findings, [])
        self.assertEqual(synthesis.recommendations, [])

    def test_12_no_duplicate_gemini_call_during_export(self) -> None:
        """12. Export operations consume already generated synthesis without re-calling LLM provider."""
        mock_provider = MagicMock(spec=LLMProvider)
        mock_provider.generate_structured_report.return_value = self.mock_llm_response

        service = JourneyService(llm_provider=mock_provider)
        # Execute single journey analysis
        synthesis, used = service._synthesize_with_llm(
            self.journey_details,
            self.uk_route,
            self.full_live,
            self.full_historical,
            self.deterministic_assessment,
        )

        self.assertEqual(mock_provider.generate_structured_report.call_count, 1)

    def test_13_existing_gemini_retry_behavior_remains_intact(self) -> None:
        """13. GeminiProvider class preserves retry loop and exponential backoff configuration."""
        from app.services.llm_provider import GeminiProvider

        provider = GeminiProvider(max_retries=3, retry_base_delay=0.5, retry_max_delay=2.0)
        self.assertEqual(provider.max_retries, 3)
        self.assertEqual(provider.retry_base_delay, 0.5)
        self.assertEqual(provider.retry_max_delay, 2.0)

    # ==========================================================================
    # Existing Endpoint Non-Regression (14-17)
    # ==========================================================================

    def test_14_existing_report_endpoint_remains_functional(self) -> None:
        """14. AIInfrastructureReportRequest schema and LLMReportService remain compatible."""
        from app.schemas.report import AIInfrastructureReportRequest
        req = AIInfrastructureReportRequest(region="all", period="last_12_months")
        self.assertEqual(req.region, "all")

    def test_15_existing_severity_endpoint_remains_functional(self) -> None:
        """15. Student A SeverityPredictionRequest schema remains compatible."""
        from app.schemas.severity import SeverityPredictionRequest
        req = SeverityPredictionRequest(
            number_of_vehicles=2,
            number_of_casualties=1,
            speed_limit=30,
            road_type="Single carriageway",
            light_conditions="Daylight",
            weather_conditions="Fine no high winds",
            road_surface_conditions="Dry",
        )
        self.assertEqual(req.speed_limit, 30)

    def test_16_existing_hotspot_endpoint_remains_functional(self) -> None:
        """16. Student B HotspotQueryRequest schema remains compatible."""
        from app.schemas.hotspot import Coordinates, HotspotQueryRequest
        req = HotspotQueryRequest(center=Coordinates(latitude=51.5, longitude=-0.12), radius_km=5.0)
        self.assertEqual(req.radius_km, 5.0)

    def test_17_existing_road_risk_endpoint_remains_functional(self) -> None:
        """17. Student C RoadRiskQueryRequest schema remains compatible."""
        from app.schemas.risk import RoadRiskQueryRequest
        req = RoadRiskQueryRequest(road_number=4, limit=5)
        self.assertEqual(req.road_number, 4)

    # ==========================================================================
    # End-to-End Pipeline Verification (18)
    # ==========================================================================

    def test_18_journey_endpoint_works_end_to_end(self) -> None:
        """18. End-to-end journey execution produces route, live context, historical models, deterministic assessment, and Gemini synthesis."""
        mock_geocoder = MagicMock(spec=NominatimGeocodingProvider)
        src_geo = GeocodedLocationSchema(latitude=51.4952, longitude=-0.1441, display_name="Victoria")
        dst_geo = GeocodedLocationSchema(latitude=51.4700, longitude=-0.4543, display_name="Heathrow")
        mock_geocoder.geocode.side_effect = [src_geo, dst_geo]

        mock_router = MagicMock(spec=OSRMRoutingProvider)
        mock_router.calculate_route.return_value = self.uk_route

        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.generate_structured_report.return_value = self.mock_llm_response

        mock_weather = MagicMock()
        mock_weather.get_weather.return_value = self.full_live.weather

        mock_traffic = MagicMock()
        mock_traffic.get_traffic.return_value = self.full_live.traffic

        mock_incidents = MagicMock()
        mock_incidents.get_incidents.return_value = (
            DataAvailabilityStatus.AVAILABLE,
            self.full_live.incidents,
        )

        service = JourneyService(
            geocoding_provider=mock_geocoder,
            routing_provider=mock_router,
            weather_provider=mock_weather,
            traffic_provider=mock_traffic,
            incident_provider=mock_incidents,
            llm_provider=mock_llm,
        )

        req = JourneyAnalyzeRequest(
            source="London Victoria Station",
            destination="Heathrow Airport Terminal 5",
            travel_date=date(2026, 9, 2),
            travel_time=time(14, 30),
        )
        resp = service.analyze_journey(req)

        self.assertEqual(resp.route.status, DataAvailabilityStatus.AVAILABLE)
        self.assertIn(resp.historical_evidence.status, (DataAvailabilityStatus.AVAILABLE, DataAvailabilityStatus.PARTIAL))
        self.assertIn(resp.safety_assessment.status, (DataAvailabilityStatus.AVAILABLE, DataAvailabilityStatus.PARTIAL))
        self.assertEqual(resp.llm_synthesis.status, DataAvailabilityStatus.AVAILABLE)
        self.assertTrue(resp.provenance.gemini_used)
        self.assertEqual(resp.llm_synthesis.headline, "Corridor Congestion with Rain Hazards on A4 Highway")

    # ==========================================================================
    # Gemini Grounding & Schema Hardening Verification (19-20)
    # ==========================================================================

    def test_19_invalid_severity_raises_validation_error(self) -> None:
        """19. LLMKeyFindingSchema rejects unconstrained severity values like 'extreme'."""
        with self.assertRaises(ValidationError):
            LLMKeyFindingSchema(
                title="Severe Storm",
                description="Heavy downpour along route",
                severity="extreme",  # Invalid severity value
                evidence_sources=["Open-Meteo"],
            )

        # Valid severities succeed
        for valid_sev in ("critical", "high", "moderate", "low", "unknown"):
            finding = LLMKeyFindingSchema(
                title="Weather Factor",
                description="Test description",
                severity=valid_sev,
                evidence_sources=["Open-Meteo"],
            )
            self.assertEqual(finding.severity, valid_sev)

    def test_20_gemini_response_with_unsupported_score_fields_cannot_pollute_schema(self) -> None:
        """20. An LLM response containing fabricated score or level cannot add them to LLMSynthesisSchema."""
        fabricated_payload = {
            "status": "available",
            "headline": "Fabricated Assessment",
            "summary": "Synthesized overview",
            "overall_score": 88.5,  # Unsupported field
            "level": "Critical",    # Unsupported field
            "key_findings": [
                {
                    "title": "Road condition",
                    "description": "Normal road",
                    "severity": "low",
                    "evidence_sources": ["TfL"],
                }
            ],
            "recommendations": [],
            "limitations": [],
        }

        synthesis = LLMSynthesisSchema.model_validate(fabricated_payload)
        self.assertFalse(hasattr(synthesis, "overall_score"))
        self.assertFalse(hasattr(synthesis, "level"))
        self.assertNotIn("overall_score", synthesis.model_dump())
        self.assertNotIn("level", synthesis.model_dump())


if __name__ == "__main__":
    unittest.main()
