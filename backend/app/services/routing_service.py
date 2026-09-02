"""
Routing Service Boundary & Providers.

Provides an abstract interface and concrete implementations (e.g. OSRM)
to calculate real road driving routes, geometry LineStrings, distances,
and estimated travel durations between geocoded coordinates.
"""

from abc import ABC, abstractmethod
import logging
from typing import Optional

import httpx

from app.config import settings
from app.schemas.journey import (
    DataAvailabilityStatus,
    GeocodedLocationSchema,
    RouteGeometrySchema,
    RouteInfoSchema,
    RouteSegmentSchema,
)

logger = logging.getLogger(__name__)


# ==============================================================================
# Domain Exceptions
# ==============================================================================


class RoutingError(Exception):
    """Base exception for all routing errors."""


class RouteNotFoundError(RoutingError):
    """Raised when no navigable road route exists between the endpoints."""


class RoutingProviderError(RoutingError):
    """Raised when the upstream routing provider fails or returns a non-200 status."""


class RoutingTimeoutError(RoutingError):
    """Raised when the routing request times out."""


# ==============================================================================
# Abstract Provider Interface
# ==============================================================================


class RoutingProvider(ABC):
    """Abstract routing provider interface."""

    @abstractmethod
    def calculate_route(
        self,
        source: GeocodedLocationSchema,
        destination: GeocodedLocationSchema,
    ) -> RouteInfoSchema:
        """Calculate real road route, distance, duration, and geometry between endpoints."""


# ==============================================================================
# Open Source Routing Machine (OSRM) Implementation
# ==============================================================================


class OSRMRoutingProvider(RoutingProvider):
    """Open Source Routing Machine (OSRM) HTTP driving provider."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        self.base_url = (
            settings.ROUTING_BASE_URL if base_url is None else base_url.rstrip("/")
        )
        self.timeout_seconds = (
            settings.ROUTING_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds
        )
        self._client = http_client

    def calculate_route(
        self,
        source: GeocodedLocationSchema,
        destination: GeocodedLocationSchema,
    ) -> RouteInfoSchema:
        """Query OSRM for driving route geometry, distance, and duration."""
        url = (
            f"{self.base_url}/{source.longitude},{source.latitude};"
            f"{destination.longitude},{destination.latitude}"
        )
        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "true",
        }
        headers = {
            "Accept": "application/json",
            "User-Agent": settings.GEOCODING_USER_AGENT,
        }

        client = self._client or httpx.Client(timeout=self.timeout_seconds)
        should_close = self._client is None

        try:
            response = client.get(url, headers=headers, params=params)
        except httpx.TimeoutException as exc:
            logger.error(
                "OSRM routing request timed out after %.1fs for (%s, %s) -> (%s, %s)",
                self.timeout_seconds,
                source.latitude,
                source.longitude,
                destination.latitude,
                destination.longitude,
            )
            raise RoutingTimeoutError(
                f"Routing request timed out after {self.timeout_seconds}s"
            ) from exc
        except httpx.RequestError as exc:
            logger.error("OSRM network error: %s", exc)
            raise RoutingProviderError(f"Network error communicating with routing engine: {exc}") from exc
        finally:
            if should_close:
                client.close()

        if response.status_code != 200:
            logger.error(
                "OSRM HTTP %d: %s",
                response.status_code,
                response.text[:200],
            )
            raise RoutingProviderError(f"Routing provider returned HTTP {response.status_code}")

        try:
            data = response.json()
        except Exception as exc:
            logger.error("Failed to parse OSRM JSON response: %s", exc)
            raise RoutingProviderError("Malformed JSON response from routing provider.") from exc

        code = data.get("code")
        if code != "Ok":
            if code in ("NoRoute", "NoSegment"):
                logger.warning("OSRM reported no route between coordinates: %s", code)
                raise RouteNotFoundError(f"No viable driving route found between coordinates ({code}).")
            logger.error("OSRM returned non-Ok code: %s", code)
            raise RoutingProviderError(f"Routing provider error ({code}).")

        routes = data.get("routes", [])
        if not routes or not isinstance(routes, list):
            raise RouteNotFoundError("No routes returned by routing provider.")

        primary_route = routes[0]
        raw_distance = primary_route.get("distance", 0.0)
        raw_duration = primary_route.get("duration", 0.0)

        distance_km = round(float(raw_distance) / 1000.0, 2)
        duration_minutes = round(float(raw_duration) / 60.0, 1)

        raw_geometry = primary_route.get("geometry", {})
        geometry = RouteGeometrySchema(
            type=raw_geometry.get("type", "LineString"),
            coordinates=raw_geometry.get("coordinates", []),
        )

        # Extract major road names from steps
        segments: list[RouteSegmentSchema] = []
        seen_names: set[str] = set()
        legs = primary_route.get("legs", [])
        if legs and isinstance(legs, list):
            steps = legs[0].get("steps", [])
            for step in steps:
                step_name = step.get("name", "").strip()
                if step_name and step_name not in seen_names:
                    seen_names.add(step_name)
                    step_length = round(float(step.get("distance", 0.0)) / 1000.0, 2)
                    segments.append(
                        RouteSegmentSchema(
                            segment_id=f"seg-{len(segments) + 1}",
                            name=step_name,
                            length_km=step_length,
                        )
                    )

        return RouteInfoSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            source=source,
            destination=destination,
            distance_km=distance_km,
            duration_minutes=duration_minutes,
            geometry=geometry,
            provider="OSRM",
            segments=segments,
        )

