"""
Weather Service Boundary & Providers.

Provides an abstract interface and concrete implementations (e.g. Open-Meteo)
to retrieve real-time and forecasted atmospheric conditions along road corridors.
"""

from abc import ABC, abstractmethod
from datetime import date, datetime, time, timezone
import logging
from typing import Optional

import httpx

from app.config import settings
from app.schemas.journey import DataAvailabilityStatus, WeatherContextSchema

logger = logging.getLogger(__name__)


# ==============================================================================
# Domain Exceptions
# ==============================================================================


class WeatherError(Exception):
    """Base exception for all weather provider errors."""


class WeatherDateOutOfRangeError(WeatherError):
    """Raised when the requested date exceeds provider's historical or forecast window."""


class WeatherProviderError(WeatherError):
    """Raised when the upstream weather provider returns a non-200 status or malformed data."""


class WeatherTimeoutError(WeatherError):
    """Raised when the weather request times out."""


# ==============================================================================
# Abstract Provider Interface
# ==============================================================================


class WeatherProvider(ABC):
    """Abstract weather provider interface."""

    @abstractmethod
    def get_weather(
        self,
        lat: float,
        lon: float,
        travel_date: date,
        travel_time: time,
    ) -> WeatherContextSchema:
        """Fetch atmospheric conditions for given geographic coordinate and date/time."""


# ==============================================================================
# Open-Meteo Implementation
# ==============================================================================

# WMO Weather Code Mappings (WMO 4677 Standard)
WMO_CODE_MAP: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def _classify_precipitation_risk(weather_code: int, precip_mm: float) -> str:
    """Derive descriptive hazard rating from WMO code and precipitation depth."""
    if weather_code in (65, 67, 75, 82, 86, 95, 96, 99) or precip_mm >= 5.0:
        return "Severe"
    if weather_code in (53, 55, 63, 73, 81) or precip_mm >= 1.0:
        return "Moderate"
    if weather_code in (51, 61, 71, 80) or precip_mm > 0.0:
        return "Low"
    return "None"


def _classify_visibility(visibility_meters: Optional[float]) -> str:
    """Classify visibility distance in accordance with meteorological standards."""
    if visibility_meters is None:
        return "Unknown"
    if visibility_meters >= 10000:
        return "Good (>10 km)"
    if visibility_meters >= 4000:
        return "Moderate (4-10 km)"
    if visibility_meters >= 1000:
        return "Poor (1-4 km)"
    return "Very Poor (<1 km, Fog hazard)"


class OpenMeteoWeatherProvider(WeatherProvider):
    """Real Open-Meteo weather API client with hourly resolution."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        self.base_url = settings.WEATHER_BASE_URL if base_url is None else base_url
        self.timeout_seconds = (
            settings.WEATHER_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds
        )
        self._client = http_client

    def get_weather(
        self,
        lat: float,
        lon: float,
        travel_date: date,
        travel_time: time,
    ) -> WeatherContextSchema:
        """Fetch real atmospheric forecast for requested location and travel date/time."""
        today = datetime.now(timezone.utc).date()
        days_ahead = (travel_date - today).days

        # Open-Meteo free forecast horizon is bounded to 16 days
        if days_ahead > 16:
            logger.warning(
                "Requested travel date %s is %d days in the future (exceeds 16-day forecast horizon)",
                travel_date,
                days_ahead,
            )
            return WeatherContextSchema(
                status=DataAvailabilityStatus.UNAVAILABLE,
                condition=None,
                temperature_c=None,
                precipitation_probability=None,
                precipitation_mm=None,
                wind_speed_kmh=None,
                visibility=None,
                precipitation_risk="Forecast horizon exceeded (>16 days)",
                queried_time=f"{travel_date.isoformat()}T{travel_time.strftime('%H:%M')}",
                location_name=f"Lat {lat:.4f}, Lon {lon:.4f}",
            )

        target_hour_str = f"{travel_date.isoformat()}T{travel_time.hour:02d}:00"

        params = {
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "hourly": "temperature_2m,precipitation_probability,precipitation,weather_code,visibility,wind_speed_10m",
            "start_date": travel_date.isoformat(),
            "end_date": travel_date.isoformat(),
            "timezone": "auto",
        }
        headers = {
            "Accept": "application/json",
            "User-Agent": settings.GEOCODING_USER_AGENT,
        }

        client = self._client or httpx.Client(timeout=self.timeout_seconds)
        should_close = self._client is None

        try:
            response = client.get(self.base_url, params=params, headers=headers)
        except httpx.TimeoutException as exc:
            logger.error("Open-Meteo weather request timed out for (%f, %f)", lat, lon)
            raise WeatherTimeoutError(
                f"Weather provider timed out after {self.timeout_seconds}s"
            ) from exc
        except httpx.RequestError as exc:
            logger.error("Open-Meteo network failure: %s", exc)
            raise WeatherProviderError(f"Network error querying weather provider: {exc}") from exc
        finally:
            if should_close:
                client.close()

        if response.status_code != 200:
            logger.error(
                "Open-Meteo returned HTTP %d for (%f, %f): %s",
                response.status_code,
                lat,
                lon,
                response.text[:200],
            )
            raise WeatherProviderError(
                f"Weather provider returned HTTP {response.status_code}"
            )

        try:
            data = response.json()
            hourly = data.get("hourly", {})
            times = hourly.get("time", [])
        except Exception as exc:
            logger.error("Failed to parse Open-Meteo JSON: %s", exc)
            raise WeatherProviderError("Malformed JSON response from weather provider.") from exc

        if not times or target_hour_str not in times:
            logger.warning(
                "Target hour %s not found in Open-Meteo times for date %s",
                target_hour_str,
                travel_date,
            )
            # Fall back to nearest available hour in the day if present
            if times:
                idx = 0
            else:
                return WeatherContextSchema(
                    status=DataAvailabilityStatus.UNAVAILABLE,
                    condition=None,
                    queried_time=target_hour_str,
                    location_name=f"Lat {lat:.4f}, Lon {lon:.4f}",
                )
        else:
            idx = times.index(target_hour_str)

        try:
            temp = float(hourly["temperature_2m"][idx])
            precip_prob = (
                int(hourly["precipitation_probability"][idx])
                if hourly.get("precipitation_probability")
                else 0
            )
            precip_mm = (
                float(hourly["precipitation"][idx]) if hourly.get("precipitation") else 0.0
            )
            wmo_code = int(hourly["weather_code"][idx]) if hourly.get("weather_code") else 0
            visibility_raw = (
                float(hourly["visibility"][idx])
                if hourly.get("visibility") and hourly["visibility"][idx] is not None
                else None
            )
            wind_kmh = (
                float(hourly["wind_speed_10m"][idx])
                if hourly.get("wind_speed_10m")
                else None
            )
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            logger.error("Malformed weather metric in Open-Meteo response: %s", exc)
            raise WeatherProviderError("Invalid weather metric structure from provider.") from exc

        condition_text = WMO_CODE_MAP.get(wmo_code, f"Weather Code {wmo_code}")
        precip_risk = _classify_precipitation_risk(wmo_code, precip_mm)
        visibility_text = _classify_visibility(visibility_raw)

        return WeatherContextSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            condition=condition_text,
            temperature_c=temp,
            precipitation_probability=precip_prob,
            precipitation_mm=precip_mm,
            wind_speed_kmh=wind_kmh,
            visibility=visibility_text,
            precipitation_risk=precip_risk,
            queried_time=target_hour_str,
            location_name=f"Corridor Midpoint ({lat:.4f}, {lon:.4f})",
        )

