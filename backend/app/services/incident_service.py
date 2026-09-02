"""
Road Incident & Disruption Service Boundary & Providers.

Provides an abstract interface and concrete implementations (e.g. Transport for London Disruptions API)
to identify active road accidents, roadworks, closures, and disruptions along the evaluated route.
"""

from abc import ABC, abstractmethod
import json
import logging
import re
from typing import Optional

import httpx

from app.config import settings
from app.schemas.journey import DataAvailabilityStatus, IncidentContextSchema, RouteInfoSchema

logger = logging.getLogger(__name__)


# ==============================================================================
# Domain Exceptions
# ==============================================================================


class IncidentError(Exception):
    """Base exception for incident provider errors."""


class IncidentProviderError(IncidentError):
    """Raised when upstream incident provider returns an error or malformed payload."""


class IncidentTimeoutError(IncidentError):
    """Raised when the incident provider request times out."""


# ==============================================================================
# Abstract Provider Interface
# ==============================================================================


class IncidentProvider(ABC):
    """Abstract road disruption and incident provider interface."""

    @abstractmethod
    def get_incidents(
        self, route: RouteInfoSchema
    ) -> tuple[DataAvailabilityStatus, list[IncidentContextSchema]]:
        """Retrieve active disruptions intersecting the specified route corridor."""


# ==============================================================================
# Transport for London (TfL) Disruptions Implementation
# ==============================================================================


def _parse_point(point_val: object) -> Optional[tuple[float, float]]:
    """Parse a [lon, lat] string or list into numeric tuple."""
    if isinstance(point_val, (list, tuple)) and len(point_val) >= 2:
        try:
            return float(point_val[0]), float(point_val[1])
        except (ValueError, TypeError):
            return None
    if isinstance(point_val, str) and point_val.startswith("["):
        try:
            parsed = json.loads(point_val)
            if isinstance(parsed, list) and len(parsed) >= 2:
                return float(parsed[0]), float(parsed[1])
        except Exception:
            return None
    return None


class TfLIncidentProvider(IncidentProvider):
    """Transport for London (TfL) live disruptions API client."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        self.base_url = settings.INCIDENT_BASE_URL if base_url is None else base_url
        self.timeout_seconds = (
            settings.INCIDENT_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds
        )
        self._client = http_client

    def get_incidents(
        self, route: RouteInfoSchema
    ) -> tuple[DataAvailabilityStatus, list[IncidentContextSchema]]:
        """Query TfL for active incidents and filter those along the route corridor."""
        coords = route.geometry.coordinates if route.geometry else []
        if not coords:
            return DataAvailabilityStatus.UNAVAILABLE, []

        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        # Bounding box with 0.02 degree corridor buffer (~2km)
        min_lon, max_lon = min(lons) - 0.02, max(lons) + 0.02
        min_lat, max_lat = min(lats) - 0.02, max(lats) + 0.02

        # Extract major road names
        route_road_names = {seg.name.lower() for seg in route.segments if seg.name}

        client = self._client or httpx.Client(timeout=self.timeout_seconds)
        should_close = self._client is None

        try:
            response = client.get(
                self.base_url,
                headers={"Accept": "application/json", "User-Agent": settings.GEOCODING_USER_AGENT},
            )
        except httpx.TimeoutException as exc:
            logger.error("TfL disruptions request timed out after %.1fs", self.timeout_seconds)
            raise IncidentTimeoutError(
                f"Incident provider timed out after {self.timeout_seconds}s"
            ) from exc
        except httpx.RequestError as exc:
            logger.error("TfL disruptions network failure: %s", exc)
            raise IncidentProviderError(f"Network error querying incident provider: {exc}") from exc
        finally:
            if should_close:
                client.close()

        if response.status_code != 200:
            logger.error(
                "TfL disruptions returned HTTP %d: %s", response.status_code, response.text[:200]
            )
            raise IncidentProviderError(
                f"Incident provider returned HTTP {response.status_code}"
            )

        try:
            disruptions = response.json()
        except Exception as exc:
            logger.error("Failed to parse TfL disruptions JSON: %s", exc)
            raise IncidentProviderError("Malformed JSON response from incident provider.") from exc

        if not isinstance(disruptions, list):
            raise IncidentProviderError("Unexpected response shape from incident provider.")

        matched_incidents: list[IncidentContextSchema] = []

        for item in disruptions:
            disruption_id = str(item.get("id", ""))
            location_text = str(item.get("location", ""))
            category = str(item.get("category", "General"))
            severity = str(item.get("severity", "Moderate"))
            comments = str(item.get("comments", location_text)).strip()
            point_raw = item.get("point")

            pt = _parse_point(point_raw)
            point_in_corridor = False
            if pt:
                pt_lon, pt_lat = pt
                if min_lon <= pt_lon <= max_lon and min_lat <= pt_lat <= max_lat:
                    point_in_corridor = True

            # Match either by spatial coordinate in bounding box or matching road name in location
            name_match = any(road in location_text.lower() for road in route_road_names if len(road) > 2)

            if point_in_corridor or name_match:
                # Clean description
                desc = comments if comments else location_text
                # Truncate overly verbose comments to clean summary
                if len(desc) > 160:
                    desc = desc[:157] + "..."

                matched_incidents.append(
                    IncidentContextSchema(
                        incident_id=disruption_id,
                        description=desc,
                        severity=severity,
                        category=category,
                        location=location_text[:80] if location_text else None,
                    )
                )

                if len(matched_incidents) >= 5:
                    break

        return DataAvailabilityStatus.AVAILABLE, matched_incidents

