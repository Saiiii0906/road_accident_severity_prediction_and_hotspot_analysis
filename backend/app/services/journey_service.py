"""
Journey Safety Analysis Service Boundary.

Orchestrates multi-source journey safety evaluation by combining route resolution,
live environmental context, historical ML model evidence (Students A, B, C),
and grounded Gemini synthesis.
"""

import logging
from typing import Optional

from app.schemas.journey import (
    DataAvailabilityStatus,
    HistoricalEvidenceSchema,
    JourneyAnalyzeRequest,
    JourneyAnalyzeResponse,
    JourneyDetailsSchema,
    JourneyProvenanceSchema,
    LiveContextSchema,
    LLMSynthesisSchema,
    RouteInfoSchema,
    SafetyAssessmentSchema,
)
from app.services.geocoding_service import (
    GeocodingProvider,
    LocationNotFoundError,
    NominatimGeocodingProvider,
)
from app.services.routing_service import (
    OSRMRoutingProvider,
    RoutingProvider,
)

logger = logging.getLogger(__name__)


class JourneyService:
    """Service layer orchestrating the Journey Safety Analysis pipeline."""

    def __init__(
        self,
        geocoding_provider: Optional[GeocodingProvider] = None,
        routing_provider: Optional[RoutingProvider] = None,
    ) -> None:
        self.geocoder = geocoding_provider or NominatimGeocodingProvider()
        self.router = routing_provider or OSRMRoutingProvider()

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

        # 1. Geocode endpoints and resolve real route corridor
        route_info = self._resolve_route(request)

        # 2. Live context subsystem (to be connected in Phase 4B)
        live_context = self._fetch_live_context(request, route_info)

        # 3. Historical model evidence subsystem (Students A, B, C to be connected in Phase 4C)
        historical_evidence = self._fetch_historical_evidence(request, route_info)

        # 4. Deterministic safety assessment subsystem
        safety_assessment = self._compute_safety_assessment(
            route_info, live_context, historical_evidence
        )

        # 5. Multimodal LLM synthesis subsystem (Gemini to be connected in Phase 4D)
        llm_synthesis = self._synthesize_with_llm(
            journey_details, route_info, live_context, historical_evidence, safety_assessment
        )

        # 6. Provenance & connectivity flags
        provenance = JourneyProvenanceSchema(
            route_provider=route_info.provider,
            live_data_available=False,
            historical_data_available=False,
            student_a_used=False,
            student_b_used=False,
            student_c_used=False,
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
        # Phase 4A: Real live environmental context pending Phase 4B
        return LiveContextSchema(
            status=DataAvailabilityStatus.PENDING,
            traffic=None,
            weather=None,
            incidents=[],
        )

    def _fetch_historical_evidence(
        self, request: JourneyAnalyzeRequest, route: RouteInfoSchema
    ) -> HistoricalEvidenceSchema:
        """Evaluate route against Student A (severity), B (hotspots), and C (GNN risk)."""
        # Phase 4A: Historical corridor alignment pending Phase 4C
        return HistoricalEvidenceSchema(
            status=DataAvailabilityStatus.PENDING,
            student_a=None,
            student_b=None,
            student_c=None,
        )

    def _compute_safety_assessment(
        self,
        route: RouteInfoSchema,
        live: LiveContextSchema,
        historical: HistoricalEvidenceSchema,
    ) -> SafetyAssessmentSchema:
        """Compute deterministic safety classification and index."""
        summary = (
            f"Route corridor resolved ({route.distance_km} km, ~{route.duration_minutes} min). "
            "Live environmental context and historical accident modeling will be incorporated in subsequent phases."
            if route.status == DataAvailabilityStatus.AVAILABLE and route.distance_km is not None
            else "Route corridor resolution pending or unavailable."
        )
        return SafetyAssessmentSchema(
            status=DataAvailabilityStatus.PENDING,
            overall_score=None,
            level=None,
            summary=summary,
        )

    def _synthesize_with_llm(
        self,
        journey: JourneyDetailsSchema,
        route: RouteInfoSchema,
        live: LiveContextSchema,
        historical: HistoricalEvidenceSchema,
        assessment: SafetyAssessmentSchema,
    ) -> LLMSynthesisSchema:
        """Generate structured AI decision-support explanation and safety precautions."""
        # Phase 4A: Gemini synthesis pending Phase 4D
        return LLMSynthesisSchema(
            status=DataAvailabilityStatus.PENDING,
            summary=None,
            recommendations=[],
        )
