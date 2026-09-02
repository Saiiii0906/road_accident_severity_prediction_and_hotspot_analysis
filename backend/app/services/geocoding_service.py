"""
Geocoding Service Boundary & Providers.

Provides an abstract interface and concrete implementations (e.g. OpenStreetMap Nominatim)
to resolve location query strings into verified geographic coordinates.
"""

from abc import ABC, abstractmethod
import logging
from typing import Optional

import httpx

from app.config import settings
from app.schemas.journey import GeocodedLocationSchema

logger = logging.getLogger(__name__)


# ==============================================================================
# Domain Exceptions
# ==============================================================================


class GeocodingError(Exception):
    """Base exception for all geocoding errors."""


class LocationNotFoundError(GeocodingError):
    """Raised when a location query cannot be resolved to geographic coordinates."""

    def __init__(self, message: str, query: str = "") -> None:
        super().__init__(message)
        self.query = query


class GeocodingProviderError(GeocodingError):
    """Raised when the upstream geocoding provider fails or returns a non-200 status."""


class GeocodingTimeoutError(GeocodingError):
    """Raised when the geocoding request times out."""


# ==============================================================================
# Abstract Provider Interface
# ==============================================================================


class GeocodingProvider(ABC):
    """Abstract geocoding provider interface."""

    @abstractmethod
    def geocode(self, query: str) -> GeocodedLocationSchema:
        """Resolve query string into geographic coordinates and canonical label."""


# ==============================================================================
# OpenStreetMap Nominatim Implementation
# ==============================================================================


class NominatimGeocodingProvider(GeocodingProvider):
    """OpenStreetMap Nominatim geocoder implementation."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        user_agent: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        self.base_url = settings.GEOCODING_BASE_URL if base_url is None else base_url
        self.user_agent = settings.GEOCODING_USER_AGENT if user_agent is None else user_agent
        self.timeout_seconds = (
            settings.GEOCODING_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds
        )
        self._client = http_client

    def geocode(self, query: str) -> GeocodedLocationSchema:
        """Resolve location query string via Nominatim API."""
        cleaned_query = query.strip()
        if not cleaned_query:
            raise LocationNotFoundError("Empty location query cannot be geocoded.", query=query)

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }
        params = {
            "q": cleaned_query,
            "format": "jsonv2",
            "limit": 1,
            "addressdetails": 1,
        }

        client = self._client or httpx.Client(timeout=self.timeout_seconds)
        should_close = self._client is None

        try:
            response = client.get(self.base_url, headers=headers, params=params)
        except httpx.TimeoutException as exc:
            logger.error("Nominatim geocoding timed out after %.1fs for '%s'", self.timeout_seconds, cleaned_query)
            raise GeocodingTimeoutError(
                f"Geocoding request for '{cleaned_query}' timed out after {self.timeout_seconds}s"
            ) from exc
        except httpx.RequestError as exc:
            logger.error("Nominatim network error for '%s': %s", cleaned_query, exc)
            raise GeocodingProviderError(
                f"Network error communicating with geocoder: {exc}"
            ) from exc
        finally:
            if should_close:
                client.close()

        if response.status_code != 200:
            logger.error(
                "Nominatim HTTP %d for '%s': %s",
                response.status_code,
                cleaned_query,
                response.text[:200],
            )
            raise GeocodingProviderError(
                f"Geocoding provider returned HTTP {response.status_code}"
            )

        try:
            results = response.json()
        except Exception as exc:
            logger.error("Failed to parse Nominatim JSON response: %s", exc)
            raise GeocodingProviderError("Malformed JSON response from geocoder.") from exc

        if not isinstance(results, list) or len(results) == 0:
            logger.warning("No geocoding results found for '%s'", cleaned_query)
            raise LocationNotFoundError(
                f"Location could not be resolved: '{cleaned_query}'", query=cleaned_query
            )

        top_match = results[0]
        try:
            lat = float(top_match["lat"])
            lon = float(top_match["lon"])
            display_name = str(top_match.get("display_name", cleaned_query))
        except (KeyError, ValueError, TypeError) as exc:
            logger.error("Malformed coordinate data in Nominatim result: %s", exc)
            raise GeocodingProviderError("Invalid coordinate structure returned by geocoder.") from exc

        return GeocodedLocationSchema(
            latitude=lat,
            longitude=lon,
            display_name=display_name,
        )

