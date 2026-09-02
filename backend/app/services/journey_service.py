"""
Journey Safety Analysis Service Boundary.

Orchestrates multi-source journey safety evaluation by combining route resolution,
live environmental context (weather, traffic, incidents), historical empirical model
grounding (Student B DBSCAN hotspots, Student C GNN road risk), and explainable AI synthesis.
"""

import logging
from typing import Optional

from app.schemas.journey import (
    DataAvailabilityStatus,
    HistoricalEvidenceSchema,
    IncidentContextSchema,
    JourneyAnalyzeRequest,
    JourneyAnalyzeResponse,
    JourneyDetailsSchema,
    JourneyProvenanceSchema,
    LiveContextProvidersSchema,
    LiveContextSchema,
    LLMSynthesisSchema,
    RouteInfoSchema,
    SafetyAssessmentSchema,
    TrafficContextSchema,
    WeatherContextSchema,
)
from app.services.corridor_matching_service import CorridorMatchingService
from app.services.geocoding_service import (
    GeocodingProvider,
    LocationNotFoundError,
    NominatimGeocodingProvider,
)
from app.services.incident_service import IncidentProvider, TfLIncidentProvider
from app.services.routing_service import OSRMRoutingProvider, RoutingProvider
from app.services.safety_assessment_service import SafetyAssessmentService
from app.services.traffic_service import TfLTrafficProvider, TrafficProvider
from app.services.weather_service import OpenMeteoWeatherProvider, WeatherProvider

logger = logging.getLogger(__name__)


class JourneyService:
    """Service layer orchestrating the Journey Safety Analysis pipeline."""

    def __init__(
        self,
        geocoding_provider: Optional[GeocodingProvider] = None,
        routing_provider: Optional[RoutingProvider] = None,
        weather_provider: Optional[WeatherProvider] = None,
        traffic_provider: Optional[TrafficProvider] = None,
        incident_provider: Optional[IncidentProvider] = None,
        corridor_matching_service: Optional[CorridorMatchingService] = None,
        safety_assessment_service: Optional[SafetyAssessmentService] = None,
    ) -> None:
        self.geocoder = geocoding_provider or NominatimGeocodingProvider()
        self.router = routing_provider or OSRMRoutingProvider()
        self.weather = weather_provider or OpenMeteoWeatherProvider()
        self.traffic = traffic_provider or TfLTrafficProvider()
        self.incidents = incident_provider or TfLIncidentProvider()
        self.corridor_matcher = corridor_matching_service or CorridorMatchingService()
        self.safety_assessor = safety_assessment_service or SafetyAssessmentService()

    def analyze_journey(self, request: JourneyAnalyzeRequest) -> JourneyAnalyzeResponse:
        """Process a journey request and return a structured safety assessment."""
        logger.info(
            "Analyzing journey: '%s' -> '%s' on %s at %s",
            request.source,
            request.destination,
            request.travel_date,
            request.travel_time,
        )

        journey_details = JourneyDetailsSchema(
            source=request.source,
            destination=request.destination,
            travel_date=request.travel_date.isoformat(),
            travel_time=request.travel_time.strftime("%H:%M"),
        )

        # 1. Geocode endpoints and resolve real route corridor (Phase 4A)
        route_info = self._resolve_route(request)

        # 2. Live environmental context subsystem (Phase 4B: Weather, Traffic, Incidents)
        live_context = self._fetch_live_context(request, route_info)

        # 3. Historical model evidence subsystem (Phase 4C: Students B & C spatial corridor matching)
        (
            historical_evidence,
            student_a_used,
            student_b_used,
            student_c_used,
        ) = self._fetch_historical_evidence(request, route_info)

        # 4. Deterministic safety assessment subsystem
        safety_assessment = self._compute_safety_assessment(
            route_info, live_context, historical_evidence
        )

        # 5. Multimodal LLM synthesis subsystem (Gemini pending Phase 4D)
        llm_synthesis = self._synthesize_with_llm(
            journey_details, route_info, live_context, historical_evidence, safety_assessment
        )

        # 6. Provenance & connectivity flags
        provenance = JourneyProvenanceSchema(
            route_provider=route_info.provider if route_info.status == DataAvailabilityStatus.AVAILABLE else None,
            weather_provider=live_context.providers.weather if live_context.providers else None,
            traffic_provider=live_context.providers.traffic if live_context.providers else None,
            incident_provider=live_context.providers.incidents if live_context.providers else None,
            live_data_available=live_context.status in (DataAvailabilityStatus.AVAILABLE, DataAvailabilityStatus.PARTIAL),
            historical_data_available=historical_evidence.status in (DataAvailabilityStatus.AVAILABLE, DataAvailabilityStatus.PARTIAL),
            historical_coverage_region=historical_evidence.coverage.region if historical_evidence.coverage else None,
            corridor_radius_m=historical_evidence.matching.corridor_radius_m if historical_evidence.matching else None,
            matched_hotspots_count=historical_evidence.student_b.hotspots_on_route if historical_evidence.student_b else 0,
            matched_segments_count=historical_evidence.student_c.segments_on_route if historical_evidence.student_c else 0,
            student_a_used=student_a_used,
            student_b_used=student_b_used,
            student_c_used=student_c_used,
            gemini_used=False,
        )

        return JourneyAnalyzeResponse(
            journey=journey_details,
            route=route_info,
            live_context=live_context,
            historical_evidence=historical_evidence,
            safety_assessment=safety_assessment,
            llm_synthesis=llm_synthesis,
            provenance=provenance,
        )

    def _resolve_route(self, request: JourneyAnalyzeRequest) -> RouteInfoSchema:
        """Resolve route corridor, distance, duration, and road segments via real providers."""
        # 1. Geocode origin
        logger.info("Resolving origin location: '%s'", request.source)
        try:
            source_loc = self.geocoder.geocode(request.source)
        except LocationNotFoundError as exc:
            logger.warning("Failed to resolve origin '%s': %s", request.source, exc)
            raise LocationNotFoundError(
                f"Origin location could not be resolved: '{request.source}'",
                query=request.source,
            ) from exc

        # 2. Geocode destination
        logger.info("Resolving destination location: '%s'", request.destination)
        try:
            dest_loc = self.geocoder.geocode(request.destination)
        except LocationNotFoundError as exc:
            logger.warning("Failed to resolve destination '%s': %s", request.destination, exc)
            raise LocationNotFoundError(
                f"Destination location could not be resolved: '{request.destination}'",
                query=request.destination,
            ) from exc

        # 3. Calculate route geometry, distance, and duration
        logger.info(
            "Requesting route from (%f, %f) to (%f, %f)",
            source_loc.latitude,
            source_loc.longitude,
            dest_loc.latitude,
            dest_loc.longitude,
        )
        return self.router.calculate_route(source_loc, dest_loc)

    def _fetch_live_context(
        self, request: JourneyAnalyzeRequest, route: RouteInfoSchema
    ) -> LiveContextSchema:
        """Fetch real-time traffic, weather, and active hazard data along corridor."""
        # 1. Determine representative route coordinate for weather
        coords = route.geometry.coordinates if route.geometry else []
        if coords:
            mid_idx = len(coords) // 2
            mid_lon, mid_lat = coords[mid_idx]
        elif route.source and route.destination:
            mid_lat = (route.source.latitude + route.destination.latitude) / 2.0
            mid_lon = (route.source.longitude + route.destination.longitude) / 2.0
        else:
            mid_lat, mid_lon = 51.5074, -0.1278

        # 2. Weather Subsystem (Open-Meteo)
        weather_ctx: Optional[WeatherContextSchema] = None
        weather_prov_name: Optional[str] = None
        try:
            weather_ctx = self.weather.get_weather(
                lat=mid_lat,
                lon=mid_lon,
                travel_date=request.travel_date,
                travel_time=request.travel_time,
            )
            if weather_ctx.status == DataAvailabilityStatus.AVAILABLE:
                weather_prov_name = "Open-Meteo"
        except Exception as exc:
            logger.error("Weather provider query failed: %s", exc)
            weather_ctx = WeatherContextSchema(
                status=DataAvailabilityStatus.UNAVAILABLE,
                condition=None,
                description=f"Weather provider error: {exc}",
            )

        # 3. Traffic Subsystem (TfL / Open Road Network)
        traffic_ctx: Optional[TrafficContextSchema] = None
        traffic_prov_name: Optional[str] = None
        try:
            traffic_ctx = self.traffic.get_traffic(route)
            if traffic_ctx.status == DataAvailabilityStatus.AVAILABLE:
                traffic_prov_name = "TfL"
        except Exception as exc:
            logger.error("Traffic provider query failed: %s", exc)
            traffic_ctx = TrafficContextSchema(
                status=DataAvailabilityStatus.UNAVAILABLE,
                description=f"Traffic provider error: {exc}",
            )

        # 4. Incidents Subsystem (TfL Disruptions)
        incident_items: list[IncidentContextSchema] = []
        incident_status = DataAvailabilityStatus.UNAVAILABLE
        incident_prov_name: Optional[str] = None
        try:
            incident_status, incident_items = self.incidents.get_incidents(route)
            if incident_status == DataAvailabilityStatus.AVAILABLE:
                incident_prov_name = "TfL"
        except Exception as exc:
            logger.error("Incident provider query failed: %s", exc)
            incident_status = DataAvailabilityStatus.UNAVAILABLE
            incident_items = []

        # 5. Determine composite status
        active_statuses = [
            weather_ctx.status if weather_ctx else DataAvailabilityStatus.UNAVAILABLE,
            traffic_ctx.status if traffic_ctx else DataAvailabilityStatus.UNAVAILABLE,
            incident_status,
        ]
        available_count = sum(1 for s in active_statuses if s == DataAvailabilityStatus.AVAILABLE)

        if available_count == len(active_statuses):
            composite_status = DataAvailabilityStatus.AVAILABLE
        elif available_count > 0:
            composite_status = DataAvailabilityStatus.PARTIAL
        else:
            composite_status = DataAvailabilityStatus.UNAVAILABLE

        providers = LiveContextProvidersSchema(
            weather=weather_prov_name,
            traffic=traffic_prov_name,
            incidents=incident_prov_name,
        )

        return LiveContextSchema(
            status=composite_status,
            weather=weather_ctx,
            traffic=traffic_ctx,
            incidents=incident_items,
            providers=providers,
        )

    def _fetch_historical_evidence(
        self, request: JourneyAnalyzeRequest, route: RouteInfoSchema
    ) -> tuple[HistoricalEvidenceSchema, bool, bool, bool]:
        """Spatially match journey corridor against Student B hotspots and Student C risk segments."""
        return self.corridor_matcher.evaluate_historical_evidence(route)

    def _compute_safety_assessment(
        self,
        route: RouteInfoSchema,
        live: LiveContextSchema,
        historical: HistoricalEvidenceSchema,
    ) -> SafetyAssessmentSchema:
        """Compute deterministic safety classification and index."""
        return self.safety_assessor.assess(route, live, historical)

    def _synthesize_with_llm(
        self,
        journey: JourneyDetailsSchema,
        route: RouteInfoSchema,
        live: LiveContextSchema,
        historical: HistoricalEvidenceSchema,
        assessment: SafetyAssessmentSchema,
    ) -> LLMSynthesisSchema:
        """Generate structured AI decision-support explanation and safety precautions."""
        # Phase 4C: Gemini synthesis pending Phase 4D
        return LLMSynthesisSchema(
            status=DataAvailabilityStatus.PENDING,
            summary=None,
            recommendations=[],
        )
