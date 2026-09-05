"""
Unit and Integration Test Suite for Phase 5 Provider & Geographic Scoping.

Tests:
- TEST A: London TfL eligibility (London route is eligible; provider can be invoked).
- TEST B: Paris TfL ineligibility (Paris route is not eligible; provider is never called).
- TEST C: Paris does not become zero incidents (represented as unavailable/unsupported).
- TEST D: London empty result (eligible + 0 disruptions returned is distinguishable from unsupported).
- TEST E: Provider failure in eligible geography (fails gracefully without raw tracebacks).
- TEST F: Historical GB scope (London accesses Student B/C; Paris receives unavailable).
- TEST G: Deterministic assessment with partial data (status partial, overall_score None, level None).
- TEST H: Gemini grounding (unsupported state fed to synthesis; instructions forbid claiming zero incidents).
- TEST I: Existing London journey regression (full London Victoria -> Heathrow pipeline intact).
"""

from datetime import date, time
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.schemas.journey import (
    DataAvailabilityStatus,
    GeocodedLocationSchema,
    HistoricalCoverageSchema,
    HistoricalEvidenceSchema,
    HistoricalHotspotEvidenceSchema,
    HistoricalRiskEvidenceSchema,
    IncidentContextSchema,
    JourneyAnalyzeRequest,
    JourneyDetailsSchema,
    LiveContextProvidersSchema,
    LiveContextSchema,
    LLMSynthesisSchema,
    ProviderCoverageStatus,
    RouteGeometrySchema,
    RouteInfoSchema,
    RouteSegmentSchema,
    SafetyAssessmentSchema,
    TrafficContextSchema,
    WeatherContextSchema,
)
from app.services.corridor_matching_service import CorridorMatchingService
from app.services.incident_service import IncidentProvider, IncidentProviderError
from app.services.journey_prompt_service import JourneyPromptService
from app.services.journey_service import JourneyService
from app.services.llm_provider import LLMProvider
from app.services.provider_coverage_service import ProviderCoverageService
from app.services.routing_service import RoutingProvider
from app.services.safety_assessment_service import SafetyAssessmentService
from app.services.traffic_service import TrafficProvider, TrafficProviderError
from app.services.weather_service import WeatherProvider


class TestProviderAndGeographicScoping(unittest.TestCase):
    """Test suite covering Phase 5 Provider and Geographic Scoping."""

    def setUp(self) -> None:
        # London Route: Victoria Station -> Heathrow Airport (Fully inside Greater London)
        self.london_route = RouteInfoSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            source=GeocodedLocationSchema(
                latitude=51.4952, longitude=-0.1441, display_name="Victoria Station, London, UK"
            ),
            destination=GeocodedLocationSchema(
                latitude=51.4700, longitude=-0.4543, display_name="Heathrow Airport, London, UK"
            ),
            distance_km=29.2,
            duration_minutes=35.0,
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

        # Paris Route: Gare du Nord -> Eiffel Tower (Entirely outside London & outside Great Britain)
        self.paris_route = RouteInfoSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            source=GeocodedLocationSchema(
                latitude=48.8809, longitude=2.3553, display_name="Gare du Nord, Paris, France"
            ),
            destination=GeocodedLocationSchema(
                latitude=48.8584, longitude=2.2945, display_name="Eiffel Tower, Paris, France"
            ),
            distance_km=6.8,
            duration_minutes=22.0,
            geometry=RouteGeometrySchema(
                type="LineString",
                coordinates=[
                    [2.3553, 48.8809],
                    [2.3200, 48.8700],
                    [2.2945, 48.8584],
                ],
            ),
            provider="OSRM",
            segments=[RouteSegmentSchema(name="Boulevard Haussmann", length_km=3.0)],
        )

        # London -> Birmingham Route: Euston -> New Street (Cross-Geographic: partially traverses Greater London)
        self.birmingham_route = RouteInfoSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            source=GeocodedLocationSchema(
                latitude=51.5281, longitude=-0.1337, display_name="Euston Station, London, UK"
            ),
            destination=GeocodedLocationSchema(
                latitude=52.4778, longitude=-1.8986, display_name="New Street Station, Birmingham, UK"
            ),
            distance_km=190.5,
            duration_minutes=140.0,
            geometry=RouteGeometrySchema(
                type="LineString",
                coordinates=[
                    [-0.1337, 51.5281],  # Inside London
                    [-0.2400, 51.5800],  # Inside London
                    [-0.7000, 52.0000],  # Outside London
                    [-1.5000, 52.3500],  # Outside London
                    [-1.8986, 52.4778],  # Outside London (Birmingham)
                ],
            ),
            provider="OSRM",
            segments=[
                RouteSegmentSchema(name="M1", length_km=80.0),
                RouteSegmentSchema(name="M6", length_km=60.0),
            ],
        )

        self.travel_date = date(2026, 9, 5)
        self.travel_time = time(14, 30)

        self.mock_weather = MagicMock(spec=WeatherProvider)
        self.mock_weather.get_weather.return_value = WeatherContextSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            coverage_status=ProviderCoverageStatus.SUPPORTED,
            condition="Overcast",
            temperature_c=18.0,
            precipitation_probability=20,
            precipitation_risk="Low",
            location_name="Queried Location",
        )

        self.mock_traffic = MagicMock(spec=TrafficProvider)
        self.mock_traffic.get_traffic.return_value = TrafficContextSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            coverage_status=ProviderCoverageStatus.SUPPORTED,
            congestion_level="moderate",
            delay_minutes=10.0,
            description="A4: Moderate Delays",
            corridor_monitored="A4",
        )

        self.mock_incidents = MagicMock(spec=IncidentProvider)
        self.mock_incidents.get_incidents.return_value = (
            DataAvailabilityStatus.AVAILABLE,
            [
                IncidentContextSchema(
                    incident_id="TFL-2001",
                    description="Lane closure on A4 westbound due to roadworks.",
                    severity="Moderate",
                    category="Works",
                    location="A4 Westbound",
                )
            ],
        )

        self.mock_llm = MagicMock(spec=LLMProvider)
        self.mock_llm.generate_structured_report.return_value = LLMSynthesisSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            headline="Journey Overview",
            summary="Grounded summary of journey conditions.",
            key_findings=[],
            recommendations=[],
            limitations=[],
        )

    # ==========================================================================
    # TEST A: London TfL Eligibility
    # ==========================================================================
    def test_a_london_tfl_eligibility(self) -> None:
        """TEST A: London route is eligible for TfL traffic/disruptions and invokes providers."""
        is_eligible, coverage_status, reason = ProviderCoverageService.check_tfl_eligibility(
            self.london_route
        )
        self.assertTrue(is_eligible)
        self.assertEqual(coverage_status, ProviderCoverageStatus.SUPPORTED)
        self.assertIn("Greater London", reason)

        # Execute live context via JourneyService
        service = JourneyService(
            weather_provider=self.mock_weather,
            traffic_provider=self.mock_traffic,
            incident_provider=self.mock_incidents,
            llm_provider=self.mock_llm,
        )
        req = JourneyAnalyzeRequest(
            source="London Victoria Station",
            destination="Heathrow Airport",
            travel_date=self.travel_date,
            travel_time=self.travel_time,
        )
        live = service._fetch_live_context(req, self.london_route)

        self.assertEqual(live.traffic.status, DataAvailabilityStatus.AVAILABLE)
        self.assertEqual(live.traffic.coverage_status, ProviderCoverageStatus.SUPPORTED)
        self.assertEqual(live.incidents_status, DataAvailabilityStatus.AVAILABLE)
        self.assertEqual(live.incidents_coverage, ProviderCoverageStatus.SUPPORTED)
        self.assertEqual(len(live.incidents), 1)
        self.assertTrue(live.traffic_queried)
        self.assertTrue(live.incident_queried)
        self.mock_traffic.get_traffic.assert_called_once_with(self.london_route)
        self.mock_incidents.get_incidents.assert_called_once_with(self.london_route)

    # ==========================================================================
    # TEST B: Paris TfL Ineligibility
    # ==========================================================================
    def test_b_paris_tfl_ineligibility(self) -> None:
        """TEST B: Paris route is NOT eligible for TfL; TfL providers are NEVER invoked."""
        is_eligible, coverage_status, reason = ProviderCoverageService.check_tfl_eligibility(
            self.paris_route
        )
        self.assertFalse(is_eligible)
        self.assertEqual(coverage_status, ProviderCoverageStatus.UNSUPPORTED_FOR_GEOGRAPHY)
        self.assertIn("outside Greater London", reason)

        service = JourneyService(
            weather_provider=self.mock_weather,
            traffic_provider=self.mock_traffic,
            incident_provider=self.mock_incidents,
            llm_provider=self.mock_llm,
        )
        req = JourneyAnalyzeRequest(
            source="Gare du Nord, Paris",
            destination="Eiffel Tower, Paris",
            travel_date=self.travel_date,
            travel_time=self.travel_time,
        )
        live = service._fetch_live_context(req, self.paris_route)

        # TfL providers must NOT have been called
        self.mock_traffic.get_traffic.assert_not_called()
        self.mock_incidents.get_incidents.assert_not_called()
        self.assertFalse(live.traffic_queried)
        self.assertFalse(live.incident_queried)

    # ==========================================================================
    # TEST C: Paris Does NOT Become Zero Incidents
    # ==========================================================================
    def test_c_paris_does_not_become_zero_incidents(self) -> None:
        """TEST C: Unsupported TfL coverage in Paris is marked UNAVAILABLE, never zero incidents."""
        service = JourneyService(
            weather_provider=self.mock_weather,
            traffic_provider=self.mock_traffic,
            incident_provider=self.mock_incidents,
            llm_provider=self.mock_llm,
        )
        req = JourneyAnalyzeRequest(
            source="Gare du Nord, Paris",
            destination="Eiffel Tower, Paris",
            travel_date=self.travel_date,
            travel_time=self.travel_time,
        )
        live = service._fetch_live_context(req, self.paris_route)

        self.assertEqual(live.traffic.status, DataAvailabilityStatus.UNAVAILABLE)
        self.assertEqual(live.traffic.coverage_status, ProviderCoverageStatus.UNSUPPORTED_FOR_GEOGRAPHY)
        self.assertIn("unavailable for this geography", live.traffic.description.lower())

        self.assertEqual(live.incidents_status, DataAvailabilityStatus.UNAVAILABLE)
        self.assertEqual(live.incidents_coverage, ProviderCoverageStatus.UNSUPPORTED_FOR_GEOGRAPHY)
        self.assertIn("unavailable for this geography", live.incidents_description.lower())
        self.assertEqual(live.incidents, [])

        # In deterministic safety assessment, it must NOT add a "0 detected" supporting evidence item
        historical = HistoricalEvidenceSchema(status=DataAvailabilityStatus.UNAVAILABLE)
        assessment = SafetyAssessmentService().assess(self.paris_route, live, historical)

        for item in assessment.supporting_evidence:
            self.assertNotEqual(item.metric, "active_disruptions_count")

        # Must record clear limitations for unsupported feeds
        tfl_limitations = [lim for lim in assessment.limitations if "TfL" in lim or "geography" in lim]
        self.assertTrue(any("disruption" in lim.lower() for lim in tfl_limitations))
        self.assertTrue(any("traffic" in lim.lower() for lim in tfl_limitations))

    # ==========================================================================
    # TEST D: London Empty Result vs Unsupported Coverage
    # ==========================================================================
    def test_d_london_empty_result_distinguishable_from_unsupported(self) -> None:
        """TEST D: London route returning 0 disruptions is AVAILABLE & RETURNED_NO_RESULTS, distinct from unsupported."""
        self.mock_incidents.get_incidents.return_value = (DataAvailabilityStatus.AVAILABLE, [])

        service = JourneyService(
            weather_provider=self.mock_weather,
            traffic_provider=self.mock_traffic,
            incident_provider=self.mock_incidents,
            llm_provider=self.mock_llm,
        )
        req = JourneyAnalyzeRequest(
            source="London Victoria Station",
            destination="Heathrow Airport",
            travel_date=self.travel_date,
            travel_time=self.travel_time,
        )
        live = service._fetch_live_context(req, self.london_route)

        # London with 0 disruptions: AVAILABLE, RETURNED_NO_RESULTS
        self.assertEqual(live.incidents_status, DataAvailabilityStatus.AVAILABLE)
        self.assertEqual(live.incidents_coverage, ProviderCoverageStatus.RETURNED_NO_RESULTS)
        self.assertTrue(live.incident_queried)

        # Assess deterministic evaluation
        historical = HistoricalEvidenceSchema(status=DataAvailabilityStatus.AVAILABLE)
        assessment = SafetyAssessmentService().assess(self.london_route, live, historical)

        # For London, 0 disruptions legitimately returned creates a supporting evidence note
        evidence_metrics = {item.metric: item.value for item in assessment.supporting_evidence}
        self.assertIn("active_disruptions_count", evidence_metrics)
        self.assertEqual(evidence_metrics["active_disruptions_count"], "0 detected")

    # ==========================================================================
    # TEST E: Provider Failure in Eligible Geography
    # ==========================================================================
    def test_e_provider_failure_gracefully_handled(self) -> None:
        """TEST E: Provider network failure in eligible London route marks FAILED without raw exceptions."""
        self.mock_traffic.get_traffic.side_effect = TrafficProviderError("HTTP 502 Bad Gateway")
        self.mock_incidents.get_incidents.side_effect = IncidentProviderError("Connection refused")

        service = JourneyService(
            weather_provider=self.mock_weather,
            traffic_provider=self.mock_traffic,
            incident_provider=self.mock_incidents,
            llm_provider=self.mock_llm,
        )
        req = JourneyAnalyzeRequest(
            source="London Victoria Station",
            destination="Heathrow Airport",
            travel_date=self.travel_date,
            travel_time=self.travel_time,
        )
        live = service._fetch_live_context(req, self.london_route)

        self.assertEqual(live.traffic.status, DataAvailabilityStatus.UNAVAILABLE)
        self.assertEqual(live.traffic.coverage_status, ProviderCoverageStatus.FAILED)
        self.assertTrue(live.traffic_queried)

        self.assertEqual(live.incidents_status, DataAvailabilityStatus.UNAVAILABLE)
        self.assertEqual(live.incidents_coverage, ProviderCoverageStatus.FAILED)
        self.assertTrue(live.incident_queried)

        assessment = SafetyAssessmentService().assess(
            self.london_route, live, HistoricalEvidenceSchema(status=DataAvailabilityStatus.AVAILABLE)
        )
        # Verify no raw exception strings leaked into user-facing limitations
        for lim in assessment.limitations:
            self.assertNotIn("HTTP 502", lim)
            self.assertNotIn("Connection refused", lim)

    # ==========================================================================
    # TEST F: Historical GB Scope
    # ==========================================================================
    def test_f_historical_gb_scope(self) -> None:
        """TEST F: London/GB route accesses historical models; Paris route is rejected as out-of-coverage."""
        matcher = CorridorMatchingService()

        # London route evaluation
        is_supported_uk, cov_status_uk, _ = matcher.check_coverage(self.london_route)
        self.assertTrue(is_supported_uk)
        self.assertEqual(cov_status_uk, DataAvailabilityStatus.AVAILABLE)

        # Paris route evaluation
        is_supported_paris, cov_status_paris, _ = matcher.check_coverage(self.paris_route)
        self.assertFalse(is_supported_paris)
        self.assertEqual(cov_status_paris, DataAvailabilityStatus.UNAVAILABLE)

        evidence_paris, _, b_used, c_used = matcher.evaluate_historical_evidence(self.paris_route)
        self.assertEqual(evidence_paris.status, DataAvailabilityStatus.UNAVAILABLE)
        self.assertFalse(b_used)
        self.assertFalse(c_used)
        self.assertEqual(evidence_paris.student_b.hotspots_on_route, 0)
        self.assertEqual(evidence_paris.student_c.segments_on_route, 0)

    # ==========================================================================
    # TEST G: Deterministic Assessment with Partial Data
    # ==========================================================================
    def test_g_deterministic_assessment_with_partial_data(self) -> None:
        """TEST G: Unsupported live feeds + available weather yield PARTIAL assessment with null overall_score."""
        live_paris = LiveContextSchema(
            status=DataAvailabilityStatus.PARTIAL,
            weather=self.mock_weather.get_weather.return_value,
            traffic=TrafficContextSchema(
                status=DataAvailabilityStatus.UNAVAILABLE,
                coverage_status=ProviderCoverageStatus.UNSUPPORTED_FOR_GEOGRAPHY,
                description="TfL traffic data unavailable for this geography.",
            ),
            incidents=[],
            incidents_status=DataAvailabilityStatus.UNAVAILABLE,
            incidents_coverage=ProviderCoverageStatus.UNSUPPORTED_FOR_GEOGRAPHY,
            incidents_description="TfL disruption data unavailable for this geography.",
            providers=LiveContextProvidersSchema(weather="Open-Meteo", traffic=None, incidents=None),
        )
        historical_paris = HistoricalEvidenceSchema(
            status=DataAvailabilityStatus.UNAVAILABLE,
            coverage=HistoricalCoverageSchema(
                supported=False,
                status=DataAvailabilityStatus.UNAVAILABLE,
                region="Great Britain (UK)",
                reason="Route is outside historical UK model coverage.",
            ),
        )

        assessment = SafetyAssessmentService().assess(
            self.paris_route, live_paris, historical_paris
        )

        self.assertEqual(assessment.status, DataAvailabilityStatus.PARTIAL)
        self.assertIsNone(assessment.overall_score)
        self.assertIsNone(assessment.level)
        self.assertEqual(assessment.data_coverage.weather, DataAvailabilityStatus.AVAILABLE)
        self.assertEqual(assessment.data_coverage.traffic, DataAvailabilityStatus.UNAVAILABLE)
        self.assertEqual(assessment.data_coverage.incidents, DataAvailabilityStatus.UNAVAILABLE)
        self.assertEqual(assessment.data_coverage.historical, DataAvailabilityStatus.UNAVAILABLE)

    # ==========================================================================
    # TEST H: Gemini Grounding for Unsupported Provider
    # ==========================================================================
    def test_h_gemini_grounding_unsupported_provider(self) -> None:
        """TEST H: Grounded evidence payload explicitly marks unsupported providers; prompt forbids assuming zero."""
        journey_details = JourneyDetailsSchema(
            source="Gare du Nord",
            destination="Eiffel Tower",
            travel_date="2026-09-05",
            travel_time="14:30",
        )
        live_paris = LiveContextSchema(
            status=DataAvailabilityStatus.PARTIAL,
            weather=self.mock_weather.get_weather.return_value,
            traffic=TrafficContextSchema(
                status=DataAvailabilityStatus.UNAVAILABLE,
                coverage_status=ProviderCoverageStatus.UNSUPPORTED_FOR_GEOGRAPHY,
                description="TfL traffic data unavailable for this geography.",
            ),
            incidents=[],
            incidents_status=DataAvailabilityStatus.UNAVAILABLE,
            incidents_coverage=ProviderCoverageStatus.UNSUPPORTED_FOR_GEOGRAPHY,
            incidents_description="TfL disruption data unavailable for this geography.",
        )
        historical_paris = HistoricalEvidenceSchema(status=DataAvailabilityStatus.UNAVAILABLE)
        assessment_paris = SafetyAssessmentSchema(status=DataAvailabilityStatus.PARTIAL)

        payload = JourneyPromptService.build_evidence_payload(
            journey_details, self.paris_route, live_paris, historical_paris, assessment_paris
        )

        # Verify structured payload represents unsupported geography
        self.assertEqual(
            payload["live_context"]["traffic"]["coverage_status"],
            ProviderCoverageStatus.UNSUPPORTED_FOR_GEOGRAPHY.value,
        )
        self.assertEqual(
            payload["live_context"]["incidents"]["coverage_status"],
            ProviderCoverageStatus.UNSUPPORTED_FOR_GEOGRAPHY.value,
        )
        self.assertEqual(payload["live_context"]["incidents"]["active_count"], 0)

        # Verify instructions explicitly forbid claiming zero incidents for unsupported geography
        instructions = JourneyPromptService.SYSTEM_INSTRUCTIONS
        self.assertIn("provider_unsupported_for_geography", instructions)
        self.assertIn("NEVER interpret this as 'no incidents'", instructions)
        self.assertIn("Never claim or imply that a non-UK route (e.g. Paris) has no incidents", instructions)

    # ==========================================================================
    # TEST I: Existing London Journey Regression
    # ==========================================================================
    def test_i_london_journey_regression(self) -> None:
        """TEST I: Complete London Victoria -> Heathrow journey operates with all providers connected."""
        mock_router = MagicMock(spec=RoutingProvider)
        mock_router.calculate_route.return_value = self.london_route

        service = JourneyService(
            geocoding_provider=MagicMock(),
            routing_provider=mock_router,
            weather_provider=self.mock_weather,
            traffic_provider=self.mock_traffic,
            incident_provider=self.mock_incidents,
            llm_provider=self.mock_llm,
        )

        req = JourneyAnalyzeRequest(
            source="London Victoria Station",
            destination="Heathrow Airport Terminal 5",
            travel_date=self.travel_date,
            travel_time=self.travel_time,
        )

        with patch.object(service, "_resolve_route", return_value=self.london_route):
            response = service.analyze_journey(req)

        self.assertEqual(response.route.distance_km, 29.2)
        self.assertEqual(response.live_context.traffic.congestion_level, "moderate")
        self.assertEqual(len(response.live_context.incidents), 1)
        self.assertEqual(response.provenance.traffic_provider, "TfL")
        self.assertEqual(response.provenance.incident_provider, "TfL")
        self.assertEqual(response.provenance.weather_provider, "Open-Meteo")
        self.assertTrue(response.provenance.traffic_queried)
        self.assertTrue(response.provenance.incident_queried)
        self.assertTrue(response.provenance.weather_queried)
        self.assertEqual(
            response.provenance.traffic_coverage_status, ProviderCoverageStatus.SUPPORTED
        )
        self.assertEqual(
            response.provenance.incident_coverage_status, ProviderCoverageStatus.SUPPORTED
        )

    # ==========================================================================
    # TEST J: London -> Birmingham Partial TfL Coverage
    # ==========================================================================
    def test_j_london_birmingham_partial_coverage(self) -> None:
        """TEST J: London -> Birmingham route is detected as PARTIALLY_SUPPORTED for TfL."""
        is_eligible, coverage_status, reason = ProviderCoverageService.check_tfl_eligibility(
            self.birmingham_route
        )
        self.assertTrue(is_eligible)
        self.assertEqual(coverage_status, ProviderCoverageStatus.PARTIALLY_SUPPORTED)
        self.assertIn("partially traverses Greater London", reason)

        service = JourneyService(
            weather_provider=self.mock_weather,
            traffic_provider=self.mock_traffic,
            incident_provider=self.mock_incidents,
            llm_provider=self.mock_llm,
        )
        req = JourneyAnalyzeRequest(
            source="Euston Station, London",
            destination="New Street Station, Birmingham",
            travel_date=self.travel_date,
            travel_time=self.travel_time,
        )
        live = service._fetch_live_context(req, self.birmingham_route)

        # Provider is queried for London portion
        self.assertTrue(live.traffic_queried)
        self.assertTrue(live.incident_queried)

        # Traffic status must be PARTIAL and coverage PARTIALLY_SUPPORTED
        self.assertEqual(live.traffic.status, DataAvailabilityStatus.PARTIAL)
        self.assertEqual(live.traffic.coverage_status, ProviderCoverageStatus.PARTIALLY_SUPPORTED)
        self.assertIn("Greater London portion of this route only", live.traffic.description)

        # Incidents status must be PARTIAL and coverage PARTIALLY_SUPPORTED
        self.assertEqual(live.incidents_status, DataAvailabilityStatus.PARTIAL)
        self.assertEqual(live.incidents_coverage, ProviderCoverageStatus.PARTIALLY_SUPPORTED)
        self.assertIn("London portion", live.incidents_description)

    # ==========================================================================
    # TEST K: Partial TfL Coverage Deterministic Assessment
    # ==========================================================================
    def test_k_partial_tfl_coverage_deterministic_assessment(self) -> None:
        """TEST K: Partial TfL coverage does not produce route-wide claims and records explicit limitations."""
        service = JourneyService(
            weather_provider=self.mock_weather,
            traffic_provider=self.mock_traffic,
            incident_provider=self.mock_incidents,
            llm_provider=self.mock_llm,
        )
        req = JourneyAnalyzeRequest(
            source="Euston Station, London",
            destination="New Street Station, Birmingham",
            travel_date=self.travel_date,
            travel_time=self.travel_time,
        )
        # 1. When incidents are detected on the London portion
        live_with_incidents = service._fetch_live_context(req, self.birmingham_route)
        historical = HistoricalEvidenceSchema(status=DataAvailabilityStatus.AVAILABLE)

        assessment = SafetyAssessmentService().assess(
            self.birmingham_route, live_with_incidents, historical
        )

        # Assessment status must be PARTIAL
        self.assertEqual(assessment.status, DataAvailabilityStatus.PARTIAL)
        self.assertIsNone(assessment.overall_score)
        self.assertIsNone(assessment.level)

        # Limitations must explicitly explain partial coverage for both traffic and disruptions
        traffic_partial_lim = [l for l in assessment.limitations if "traffic" in l.lower() and "partial" in l.lower()]
        self.assertTrue(len(traffic_partial_lim) > 0)
        self.assertIn("Greater London portion", traffic_partial_lim[0])

        incident_partial_lim = [l for l in assessment.limitations if "disruption" in l.lower() and "partial" in l.lower()]
        self.assertTrue(len(incident_partial_lim) > 0)
        self.assertIn("Greater London portion", incident_partial_lim[0])

        # Factors and evidence must be tagged as London portion only, never full-route
        factor_titles = [f.title for f in assessment.key_factors]
        self.assertIn("Corridor Traffic Flow (London Portion Only)", factor_titles)
        self.assertIn("Active Road Hazards & Disruptions (London Portion Only)", factor_titles)

        evidence_metrics = {item.metric: item.value for item in assessment.supporting_evidence}
        self.assertIn("traffic_congestion_london_portion", evidence_metrics)
        self.assertIn("active_disruptions_london_portion", evidence_metrics)
        self.assertNotIn("active_disruptions_count", evidence_metrics)

        # 2. When ZERO disruptions are returned for the London portion:
        # It must NOT produce route-wide "0 detected" active_disruptions_count!
        self.mock_incidents.get_incidents.return_value = (DataAvailabilityStatus.AVAILABLE, [])
        live_zero_incidents = service._fetch_live_context(req, self.birmingham_route)
        assessment_zero = SafetyAssessmentService().assess(
            self.birmingham_route, live_zero_incidents, historical
        )

        metrics_zero = {item.metric: item.value for item in assessment_zero.supporting_evidence}
        self.assertNotIn("active_disruptions_count", metrics_zero)
        self.assertIn("active_disruptions_london_portion", metrics_zero)
        self.assertEqual(metrics_zero["active_disruptions_london_portion"], "0 detected (London portion)")

        # Summary must NOT say full-route "0 disruptions"
        self.assertNotIn("Live context: weather: Overcast (20% rain), traffic: moderate, 0 disruptions.", assessment_zero.summary)
        self.assertIn("London portion", assessment_zero.summary)

    # ==========================================================================
    # TEST L: Gemini Receives Partial Coverage State
    # ==========================================================================
    def test_l_gemini_receives_partial_coverage_state(self) -> None:
        """TEST L: Gemini evidence payload contains provider_partially_supported and instructions forbid extrapolation."""
        journey_details = JourneyDetailsSchema(
            source="London Euston",
            destination="Birmingham New Street",
            travel_date="2026-09-05",
            travel_time="14:30",
        )
        service = JourneyService(
            weather_provider=self.mock_weather,
            traffic_provider=self.mock_traffic,
            incident_provider=self.mock_incidents,
            llm_provider=self.mock_llm,
        )
        req = JourneyAnalyzeRequest(
            source="London Euston",
            destination="Birmingham New Street",
            travel_date=self.travel_date,
            travel_time=self.travel_time,
        )
        live = service._fetch_live_context(req, self.birmingham_route)
        historical = HistoricalEvidenceSchema(status=DataAvailabilityStatus.AVAILABLE)
        assessment = SafetyAssessmentService().assess(self.birmingham_route, live, historical)

        payload = JourneyPromptService.build_evidence_payload(
            journey_details, self.birmingham_route, live, historical, assessment
        )

        self.assertEqual(
            payload["live_context"]["traffic"]["coverage_status"],
            ProviderCoverageStatus.PARTIALLY_SUPPORTED.value,
        )
        self.assertEqual(
            payload["live_context"]["incidents"]["coverage_status"],
            ProviderCoverageStatus.PARTIALLY_SUPPORTED.value,
        )
        self.assertEqual(payload["live_context"]["traffic"]["status"], "partial")
        self.assertEqual(payload["live_context"]["incidents"]["status"], "partial")

        # Instruction Rule 18 must be present
        instructions = JourneyPromptService.SYSTEM_INSTRUCTIONS
        self.assertIn("provider_partially_supported", instructions)
        self.assertIn("applies ONLY to the London portion", instructions)
        self.assertIn("NEVER claim or imply route-wide clear roads, zero incidents, or smooth traffic", instructions)


if __name__ == "__main__":
    unittest.main()

