"""
Traffic Service Boundary & Providers.

Provides an abstract interface and concrete implementations (e.g. Transport for London Road API)
to evaluate real-time road corridor traffic congestion and flow status.
"""

from abc import ABC, abstractmethod
import json
import logging
import re
from typing import Optional

import httpx

from app.config import settings
from app.schemas.journey import DataAvailabilityStatus, RouteInfoSchema, TrafficContextSchema

logger = logging.getLogger(__name__)


# ==============================================================================
# Domain Exceptions
# ==============================================================================


class TrafficError(Exception):
    """Base exception for traffic provider errors."""


class TrafficProviderError(TrafficError):
    """Raised when upstream traffic provider returns an error or malformed payload."""


class TrafficTimeoutError(TrafficError):
    """Raised when the traffic provider request times out."""


# ==============================================================================
# Abstract Provider Interface
# ==============================================================================


class TrafficProvider(ABC):
    """Abstract traffic status provider interface."""

    @abstractmethod
    def get_traffic(self, route: RouteInfoSchema) -> TrafficContextSchema:
        """Evaluate live traffic congestion along the route's monitored corridors."""


# ==============================================================================
# Transport for London (TfL) Implementation
# ==============================================================================


def _extract_corridor_code(text: str) -> Optional[str]:
    """Extract standard UK road designation (e.g. 'A4', 'A40', 'M4') from road name."""
    match = re.search(r"\b([AM]\d+)\b", text, re.IGNORECASE)
    return match.group(1).lower() if match else None


def _bbox_intersects(b1: tuple[float, float, float, float], b2: tuple[float, float, float, float]) -> bool:
    """Check whether two (min_lon, min_lat, max_lon, max_lat) bounding boxes overlap."""
    min_lon1, min_lat1, max_lon1, max_lat1 = b1
    min_lon2, min_lat2, max_lon2, max_lat2 = b2
    return not (
        max_lon1 < min_lon2 or min_lon1 > max_lon2 or max_lat1 < min_lat2 or min_lat1 > max_lat2
    )


class TfLTrafficProvider(TrafficProvider):
    """Transport for London (TfL) live road corridor network client."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        self.base_url = settings.TRAFFIC_BASE_URL if base_url is None else base_url
        self.timeout_seconds = (
            settings.TRAFFIC_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds
        )
        self._client = http_client

    def get_traffic(self, route: RouteInfoSchema) -> TrafficContextSchema:
        """Query TfL for live congestion and exceptional delay indicators along corridor."""
        # Check if route geometry exists to compute bounding box
        coords = route.geometry.coordinates if route.geometry else []
        if not coords:
            return TrafficContextSchema(
                status=DataAvailabilityStatus.UNAVAILABLE,
                description="Route geometry unavailable to evaluate live traffic.",
            )

        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        route_bbox = (min(lons) - 0.01, min(lats) - 0.01, max(lons) + 0.01, max(lats) + 0.01)

        # Extract road designations from segments
        route_corridor_codes = set()
        for seg in route.segments:
            if seg.name:
                code = _extract_corridor_code(seg.name)
                if code:
                    route_corridor_codes.add(code)

        client = self._client or httpx.Client(timeout=self.timeout_seconds)
        should_close = self._client is None

        try:
            response = client.get(
                self.base_url,
                headers={"Accept": "application/json", "User-Agent": settings.GEOCODING_USER_AGENT},
            )
        except httpx.TimeoutException as exc:
            logger.error("TfL traffic request timed out after %.1fs", self.timeout_seconds)
            raise TrafficTimeoutError(
                f"Traffic provider timed out after {self.timeout_seconds}s"
            ) from exc
        except httpx.RequestError as exc:
            logger.error("TfL network failure: %s", exc)
            raise TrafficProviderError(f"Network error querying traffic provider: {exc}") from exc
        finally:
            if should_close:
                client.close()

        if response.status_code != 200:
            logger.error("TfL returned HTTP %d: %s", response.status_code, response.text[:200])
            raise TrafficProviderError(
                f"Traffic provider returned HTTP {response.status_code}"
            )

        try:
            roads = response.json()
        except Exception as exc:
            logger.error("Failed to parse TfL JSON: %s", exc)
            raise TrafficProviderError("Malformed JSON response from traffic provider.") from exc

        if not isinstance(roads, list):
            raise TrafficProviderError("Unexpected response shape from traffic provider.")

        # Search for matching corridor either by designation or bounding box intersection
        matched_corridor = None
        for road in roads:
            road_id = str(road.get("id", "")).lower()
            display_name = str(road.get("displayName", ""))

            # 1. Direct corridor code match (e.g. 'a4')
            if road_id in route_corridor_codes or any(c in display_name.lower() for c in route_corridor_codes):
                matched_corridor = road
                break

            # 2. Geometric bounds overlap
            raw_bounds = road.get("bounds")
            if raw_bounds:
                try:
                    parsed_bounds = json.loads(raw_bounds)
                    c_bbox = (
                        parsed_bounds[0][0],
                        parsed_bounds[0][1],
                        parsed_bounds[1][0],
                        parsed_bounds[1][1],
                    )
                    if _bbox_intersects(route_bbox, c_bbox):
                        matched_corridor = road
                        break
                except Exception:
                    continue

        if not matched_corridor:
            logger.info("No TfL monitored road corridor intersects the route geometry.")
            return TrafficContextSchema(
                status=DataAvailabilityStatus.UNAVAILABLE,
                congestion_level=None,
                delay_minutes=None,
                description="No monitored live traffic corridor coverage for this route.",
                corridor_monitored=None,
            )

        severity = str(matched_corridor.get("statusSeverity", "Good")).lower()
        severity_desc = str(
            matched_corridor.get("statusSeverityDescription", "No Exceptional Delays")
        )
        corridor_name = str(matched_corridor.get("displayName", matched_corridor.get("id", "")))

        # Map to standard congestion scale
        if any(w in severity for w in ("closure", "blocked", "severe", "serious")):
            congestion = "severe"
            delay_est = 25.0
        elif any(w in severity for w in ("moderate", "slow", "delays")):
            congestion = "moderate"
            delay_est = 10.0
        else:
            congestion = "low"
            delay_est = 0.0

        return TrafficContextSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            congestion_level=congestion,
            delay_minutes=delay_est,
            description=f"{corridor_name}: {severity_desc}",
            corridor_monitored=corridor_name,
        )

