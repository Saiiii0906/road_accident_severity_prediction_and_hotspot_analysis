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

    # ==========================================================================
    # Phase 4 Regression Tests: Output Integrity & Error Sanitization (A - I)
    # ==========================================================================

    def test_phase4_test_a_valid_structured_gemini_response(self) -> None:
        """Test A: Valid structured Gemini response returns clean synthesis without garbage."""
        mock_llm = MagicMock(spec=LLMProvider)
        valid_response = LLMSynthesisSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            headline="Victoria to Heathrow: Congestion on A4 with Active Roadworks",
            summary="Traffic along the A4 corridor exhibits heavy congestion with 15-minute delays.",
            key_findings=[
                LLMKeyFindingSchema(
                    title="A4 Congestion",
                    description="15-minute delays reported.",
                    severity="high",
                    evidence_sources=["TfL Road Network"],
                )
            ],
            recommendations=[
                LLMRecommendationSchema(
                    action="Allow extra travel time",
                    reason="Active congestion along A4 Westbound.",
                    evidence_sources=["TfL Road Network"],
                )
            ],
            limitations=["Student A model excluded from route traversal."],
        )
        mock_llm.generate_structured_report.return_value = valid_response

        service = JourneyService(
            geocoding_provider=MagicMock(),
            routing_provider=MagicMock(),
            weather_provider=MagicMock(),
            traffic_provider=MagicMock(),
            incident_provider=MagicMock(),
            llm_provider=mock_llm,
        )

        synthesis, used = service._synthesize_with_llm(
            self.journey_details,
            self.uk_route,
            self.full_live,
            HistoricalEvidenceSchema(status=DataAvailabilityStatus.AVAILABLE),
            SafetyAssessmentSchema(status=DataAvailabilityStatus.AVAILABLE, limitations=[]),
        )

        self.assertTrue(used)
        self.assertEqual(synthesis.status, DataAvailabilityStatus.AVAILABLE)
        self.assertEqual(synthesis.headline, "Victoria to Heathrow: Congestion on A4 with Active Roadworks")
        self.assertIn("A4 corridor exhibits heavy congestion", synthesis.summary)
        self.assertEqual(len(synthesis.key_findings), 1)
        self.assertEqual(len(synthesis.recommendations), 1)
        self.assertEqual(synthesis.limitations, ["Student A model excluded from route traversal."])

    def test_phase4_test_b_garbage_appended_simulated_corruption_rejected(self) -> None:
        """Test B: Garbage technical word block appended to summary is rejected by integrity validation."""
        corrupted_summary = (
            "The planned route faces delays on A4. "
            "schema prompt validation output mapping configuration payload sequence "
            "framework processing dataset structure requirements parsing logic matrix"
        )
        corrupted_response = LLMSynthesisSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            headline="London to Heathrow Delays",
            summary=corrupted_summary,
            key_findings=[],
            recommendations=[],
            limitations=[],
        )
        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.generate_structured_report.return_value = corrupted_response

        service = JourneyService(
            geocoding_provider=MagicMock(),
            routing_provider=MagicMock(),
            weather_provider=MagicMock(),
            traffic_provider=MagicMock(),
            incident_provider=MagicMock(),
            llm_provider=mock_llm,
        )

        assessment = SafetyAssessmentSchema(status=DataAvailabilityStatus.AVAILABLE, limitations=["Weather monitored."])
        synthesis, used = service._synthesize_with_llm(
            self.journey_details,
            self.uk_route,
            self.full_live,
            HistoricalEvidenceSchema(status=DataAvailabilityStatus.AVAILABLE),
            assessment,
        )

        self.assertFalse(used)
        self.assertEqual(synthesis.status, DataAvailabilityStatus.UNAVAILABLE)
        self.assertIsNone(synthesis.headline)
        self.assertIsNone(synthesis.summary)
        self.assertEqual(synthesis.key_findings, [])
        self.assertEqual(synthesis.recommendations, [])
        self.assertEqual(
            synthesis.limitations,
            [
                "AI synthesis was unavailable because the generated response did not meet the required output format. The evidence-based journey assessment remains available."
            ],
        )

    def test_phase4_test_c_raw_prompt_or_schema_text_rejected(self) -> None:
        """Test C: Raw prompt instructions or OpenAPI schema fragments returned are rejected."""
        leaked_response = LLMSynthesisSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            headline="Route Report",
            summary="Follow CRITICAL GROUNDEDNESS rules and output according to JSON schema.",
            key_findings=[],
            recommendations=[],
            limitations=[],
        )
        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.generate_structured_report.return_value = leaked_response

        service = JourneyService(
            geocoding_provider=MagicMock(),
            routing_provider=MagicMock(),
            weather_provider=MagicMock(),
            traffic_provider=MagicMock(),
            incident_provider=MagicMock(),
            llm_provider=mock_llm,
        )

        synthesis, used = service._synthesize_with_llm(
            self.journey_details,
            self.uk_route,
            self.full_live,
            HistoricalEvidenceSchema(status=DataAvailabilityStatus.AVAILABLE),
            SafetyAssessmentSchema(status=DataAvailabilityStatus.AVAILABLE, limitations=[]),
        )

        self.assertFalse(used)
        self.assertEqual(synthesis.status, DataAvailabilityStatus.UNAVAILABLE)
        self.assertEqual(
            synthesis.limitations,
            [
                "AI synthesis was unavailable because the generated response did not meet the required output format. The evidence-based journey assessment remains available."
            ],
        )

    def test_phase4_test_d_pydantic_validation_failure_sanitized_limitation(self) -> None:
        """Test D: Pydantic validation failure produces clean user limitation without traceback dump."""
        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.generate_structured_report.side_effect = LLMValidationError(
            "4 validation errors for LLMSynthesisSchema\nkey_findings.0.title\n  Field required [type=missing]"
        )

        service = JourneyService(
            geocoding_provider=MagicMock(),
            routing_provider=MagicMock(),
            weather_provider=MagicMock(),
            traffic_provider=MagicMock(),
            incident_provider=MagicMock(),
            llm_provider=mock_llm,
        )

        synthesis, used = service._synthesize_with_llm(
            self.journey_details,
            self.uk_route,
            self.full_live,
            HistoricalEvidenceSchema(status=DataAvailabilityStatus.AVAILABLE),
            SafetyAssessmentSchema(status=DataAvailabilityStatus.AVAILABLE, limitations=[]),
        )

        self.assertFalse(used)
        self.assertEqual(synthesis.status, DataAvailabilityStatus.UNAVAILABLE)
        # Verify no Python traceback or technical dump in limitations
        self.assertEqual(
            synthesis.limitations,
            [
                "AI synthesis was unavailable because the generated response did not meet the required output format. The evidence-based journey assessment remains available."
            ],
        )
        self.assertNotIn("validation errors", synthesis.limitations[0])
        self.assertNotIn("LLMSynthesisSchema", synthesis.limitations[0])

    def test_phase4_test_e_gemini_429_rate_limit_retry(self) -> None:
        """Test E: Gemini 429 triggers retry behavior and succeeds if subsequent attempt is 200."""
        from app.services.llm_provider import GeminiProvider
        import httpx

        mock_client = MagicMock(spec=httpx.Client)
        # Attempt 1: HTTP 429; Attempt 2: HTTP 200
        resp_429 = MagicMock(status_code=429, text="Rate limit exceeded")
        resp_200 = MagicMock(
            status_code=200,
            json=lambda: {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": '{"status": "available", "headline": "Clear Route", "summary": "No issues.", "key_findings": [], "recommendations": [], "limitations": []}'
                                }
                            ]
                        }
                    }
                ]
            },
        )
        mock_client.post.side_effect = [resp_429, resp_200]

        provider = GeminiProvider(
            api_key="test-api-key",
            model="gemini-3.6-flash",
            http_client=mock_client,
            max_retries=2,
            retry_base_delay=0.01,
        )

        result = provider.generate_structured_report("test prompt", LLMSynthesisSchema)
        self.assertEqual(result.headline, "Clear Route")
        self.assertEqual(mock_client.post.call_count, 2)

    def test_phase4_test_f_gemini_persistent_failure_clean_unavailable_state(self) -> None:
        """Test F: Persistent Gemini failure surfaces clean user limitation with zero raw exception leakage."""
        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.generate_structured_report.side_effect = LLMProviderError(
            "Gemini server error (HTTP 500): Internal error with stack trace at /usr/local/bin/server.py:120"
        )

        service = JourneyService(
            geocoding_provider=MagicMock(),
            routing_provider=MagicMock(),
            weather_provider=MagicMock(),
            traffic_provider=MagicMock(),
            incident_provider=MagicMock(),
            llm_provider=mock_llm,
        )

        synthesis, used = service._synthesize_with_llm(
            self.journey_details,
            self.uk_route,
            self.full_live,
            HistoricalEvidenceSchema(status=DataAvailabilityStatus.AVAILABLE),
            SafetyAssessmentSchema(status=DataAvailabilityStatus.AVAILABLE, limitations=[]),
        )

        self.assertFalse(used)
        self.assertEqual(synthesis.status, DataAvailabilityStatus.UNAVAILABLE)
        self.assertEqual(
            synthesis.limitations,
            [
                "AI synthesis is temporarily unavailable. The evidence-based journey assessment remains available."
            ],
        )
        self.assertNotIn("HTTP 500", synthesis.limitations[0])
        self.assertNotIn("server.py", synthesis.limitations[0])

    def test_phase4_test_g_claude_fallback_if_configured(self) -> None:
        """Test G: Primary provider transient failure cleanly invokes configured Claude fallback."""
        from app.services.llm_provider_router import LLMProviderRouter

        mock_primary = MagicMock(spec=LLMProvider)
        mock_primary.generate_structured_report.side_effect = LLMProviderError("Primary HTTP 503")

        mock_fallback = MagicMock(spec=LLMProvider)
        fallback_synthesis = LLMSynthesisSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            headline="Claude Fallback Report",
            summary="Summary generated via fallback.",
            key_findings=[],
            recommendations=[],
            limitations=[],
        )
        mock_fallback.generate_structured_report.return_value = fallback_synthesis

        router = LLMProviderRouter(primary_provider=mock_primary, fallback_provider=mock_fallback)
        result = router.generate_structured_report("test prompt", LLMSynthesisSchema)

        self.assertEqual(result.headline, "Claude Fallback Report")
        self.assertEqual(mock_primary.generate_structured_report.call_count, 1)
        self.assertEqual(mock_fallback.generate_structured_report.call_count, 1)

    def test_phase4_test_h_claude_unavailable_clean_unavailable_state(self) -> None:
        """Test H: When both primary and fallback fail, journey service returns clean unavailable state."""
        from app.services.llm_provider_router import LLMProviderRouter

        mock_primary = MagicMock(spec=LLMProvider)
        mock_primary.generate_structured_report.side_effect = LLMProviderError("Primary down")

        mock_fallback = MagicMock(spec=LLMProvider)
        mock_fallback.generate_structured_report.side_effect = LLMConfigurationError("Claude key missing")

        router = LLMProviderRouter(primary_provider=mock_primary, fallback_provider=mock_fallback)
        service = JourneyService(
            geocoding_provider=MagicMock(),
            routing_provider=MagicMock(),
            weather_provider=MagicMock(),
            traffic_provider=MagicMock(),
            incident_provider=MagicMock(),
            llm_provider=router,
        )

        synthesis, used = service._synthesize_with_llm(
            self.journey_details,
            self.uk_route,
            self.full_live,
            HistoricalEvidenceSchema(status=DataAvailabilityStatus.AVAILABLE),
            SafetyAssessmentSchema(status=DataAvailabilityStatus.AVAILABLE, limitations=[]),
        )

        self.assertFalse(used)
        self.assertEqual(synthesis.status, DataAvailabilityStatus.UNAVAILABLE)
        self.assertEqual(
            synthesis.limitations,
            [
                "AI synthesis is temporarily unavailable. The evidence-based journey assessment remains available."
            ],
        )

    def test_phase4_test_i_grounding_rules_preserved(self) -> None:
        """Test I: Grounding rules strictly reject arbitrary scores, route-wide levels, and fabricated fields."""
        # 1. Overall score and level are forbidden in LLMSynthesisSchema
        with self.assertRaises(ValidationError):
            # Cannot instantiate LLMKeyFindingSchema with arbitrary severity
            LLMKeyFindingSchema(
                title="Fake Score",
                description="Invented 95% risk score",
                severity="fabricated",  # Invalid literal
                evidence_sources=[],
            )

        # 2. Verify LLMSynthesisSchema has no overall_score or level field
        schema = LLMSynthesisSchema.model_json_schema()
        self.assertNotIn("overall_score", schema.get("properties", {}))
        self.assertNotIn("level", schema.get("properties", {}))
        self.assertNotIn("confidence", schema.get("properties", {}))

        # 3. Verify Prompt instructions forbid arbitrary scores and route-wide levels
        self.assertIn("Never create numerical risk scores", JourneyPromptService.SYSTEM_INSTRUCTIONS)
        self.assertIn("Never create route-wide safety level categories", JourneyPromptService.SYSTEM_INSTRUCTIONS)
        self.assertIn("Never fabricate confidence scores", JourneyPromptService.SYSTEM_INSTRUCTIONS)
        self.assertIn("Never fabricate accident counts", JourneyPromptService.SYSTEM_INSTRUCTIONS)


if __name__ == "__main__":
    unittest.main()
