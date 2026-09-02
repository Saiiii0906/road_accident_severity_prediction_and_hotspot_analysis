from datetime import date, datetime, time, timezone
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.schemas.journey import (
    DataAvailabilityStatus,
    GeocodedLocationSchema,
    IncidentContextSchema,
    JourneyAnalyzeRequest,
    JourneyAnalyzeResponse,
    RouteGeometrySchema,
    RouteInfoSchema,
    RouteSegmentSchema,
    TrafficContextSchema,
    WeatherContextSchema,
)
from app.services.incident_service import (
    IncidentProviderError,
    IncidentTimeoutError,
    TfLIncidentProvider,
)
from app.services.journey_service import JourneyService
from app.services.traffic_service import (
    TfLTrafficProvider,
    TrafficProviderError,
    TrafficTimeoutError,
)
from app.services.weather_service import (
    OpenMeteoWeatherProvider,
    WeatherProviderError,
    WeatherTimeoutError,
)


class TestLiveContextSubsystem(unittest.TestCase):
    """Test suite covering weather, traffic, incidents, and multi-source live context."""

    def setUp(self) -> None:
        self.sample_route = RouteInfoSchema(
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
            segments=[
                RouteSegmentSchema(segment_id="1", name="A4", length_km=15.0),
                RouteSegmentSchema(segment_id="2", name="M4", length_km=14.2),
            ],
        )
        self.travel_date = date(2026, 9, 2)
        self.travel_time = time(14, 30)

    # ==========================================================================
    # Weather Unit Tests (1-5)
    # ==========================================================================

    def test_01_weather_success(self) -> None:
        """1. Open-Meteo success returns parsed weather metrics matching requested hour."""
        mock_client = MagicMock(spec=httpx.Client)
        mock_resp = MagicMock(status_code=200)
        target_time = "2026-09-02T14:00"
        mock_resp.json.return_value = {
            "hourly": {
                "time": [target_time],
                "temperature_2m": [18.2],
                "precipitation_probability": [25],
                "precipitation": [0.0],
                "weather_code": [3],
                "visibility": [25000.0],
                "wind_speed_10m": [12.5],
            }
        }
        mock_client.get.return_value = mock_resp

        provider = OpenMeteoWeatherProvider(http_client=mock_client)
        res = provider.get_weather(51.49, -0.25, self.travel_date, self.travel_time)

        self.assertEqual(res.status, DataAvailabilityStatus.AVAILABLE)
        self.assertEqual(res.temperature_c, 18.2)
        self.assertEqual(res.precipitation_probability, 25)
        self.assertEqual(res.precipitation_mm, 0.0)
        self.assertEqual(res.condition, "Overcast")
        self.assertEqual(res.wind_speed_kmh, 12.5)
        self.assertIn("Good", res.visibility or "")

    def test_02_weather_no_data(self) -> None:
        """2. Empty time array returns unavailable weather status."""
        mock_client = MagicMock(spec=httpx.Client)
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"hourly": {"time": []}}
        mock_client.get.return_value = mock_resp

        provider = OpenMeteoWeatherProvider(http_client=mock_client)
        res = provider.get_weather(51.49, -0.25, self.travel_date, self.travel_time)

        self.assertEqual(res.status, DataAvailabilityStatus.UNAVAILABLE)
        self.assertIsNone(res.condition)

    def test_03_weather_timeout(self) -> None:
        """3. Upstream timeout raises WeatherTimeoutError."""
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.side_effect = httpx.TimeoutException("Connection timed out")

        provider = OpenMeteoWeatherProvider(http_client=mock_client)
        with self.assertRaises(WeatherTimeoutError):
            provider.get_weather(51.49, -0.25, self.travel_date, self.travel_time)

    def test_04_weather_provider_http_failure(self) -> None:
        """4. Upstream HTTP 500 error raises WeatherProviderError."""
        mock_client = MagicMock(spec=httpx.Client)
        mock_resp = MagicMock(status_code=500, text="Internal Server Error")
        mock_client.get.return_value = mock_resp

        provider = OpenMeteoWeatherProvider(http_client=mock_client)
        with self.assertRaises(WeatherProviderError):
            provider.get_weather(51.49, -0.25, self.travel_date, self.travel_time)

    def test_05_weather_unsupported_future_date(self) -> None:
        """5. Date beyond 16 days returns unavailable status with horizon note."""
        far_future_date = date(2030, 1, 1)
        provider = OpenMeteoWeatherProvider()
        res = provider.get_weather(51.49, -0.25, far_future_date, self.travel_time)

        self.assertEqual(res.status, DataAvailabilityStatus.UNAVAILABLE)
        self.assertIn("horizon", (res.precipitation_risk or "").lower())

    # ==========================================================================
    # Traffic Unit Tests (6-8)
    # ==========================================================================

    def test_06_traffic_success(self) -> None:
        """6. TfL traffic query successfully matches route corridor (e.g. A4)."""
        mock_client = MagicMock(spec=httpx.Client)
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = [
            {
                "id": "a4",
                "displayName": "A4",
                "statusSeverity": "Good",
                "statusSeverityDescription": "No Exceptional Delays",
                "bounds": "[[-0.50,51.44],[-0.15,51.50]]",
            }
        ]
        mock_client.get.return_value = mock_resp

        provider = TfLTrafficProvider(http_client=mock_client)
        res = provider.get_traffic(self.sample_route)

        self.assertEqual(res.status, DataAvailabilityStatus.AVAILABLE)
        self.assertEqual(res.congestion_level, "low")
        self.assertEqual(res.corridor_monitored, "A4")
        self.assertIn("No Exceptional Delays", res.description or "")

    def test_07_traffic_unavailable_for_unmonitored_route(self) -> None:
        """7. Route without matching monitored corridor returns unavailable status."""
        mock_client = MagicMock(spec=httpx.Client)
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = [
            {
                "id": "a1",
                "displayName": "A1",
                "statusSeverity": "Good",
                "statusSeverityDescription": "No Delays",
                "bounds": "[[1.0, 52.0], [2.0, 53.0]]",
            }
        ]
        mock_client.get.return_value = mock_resp

        provider = TfLTrafficProvider(http_client=mock_client)
        res = provider.get_traffic(self.sample_route)

        self.assertEqual(res.status, DataAvailabilityStatus.UNAVAILABLE)
        self.assertIn("No monitored", res.description or "")

    def test_08_traffic_timeout(self) -> None:
        """8. Upstream traffic timeout raises TrafficTimeoutError."""
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.side_effect = httpx.TimeoutException("Read timed out")

        provider = TfLTrafficProvider(http_client=mock_client)
        with self.assertRaises(TrafficTimeoutError):
            provider.get_traffic(self.sample_route)

    # ==========================================================================
    # Incidents Unit Tests (9-11)
    # ==========================================================================

    def test_09_incidents_success(self) -> None:
        """9. Active disruptions matching the corridor bounding box are returned."""
        mock_client = MagicMock(spec=httpx.Client)
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = [
            {
                "id": "TIMS-1001",
                "location": "[A4] Great West Road",
                "category": "Works",
                "severity": "Moderate",
                "comments": "Lane closure on A4 eastbound.",
                "point": "[-0.25, 51.49]",
            },
            {
                "id": "TIMS-1002",
                "location": "Edinburgh Bypass",
                "category": "Works",
                "severity": "Low",
                "comments": "Far away disruption",
                "point": "[-3.20, 55.90]",
            },
        ]
        mock_client.get.return_value = mock_resp

        provider = TfLIncidentProvider(http_client=mock_client)
        status, incidents = provider.get_incidents(self.sample_route)

        self.assertEqual(status, DataAvailabilityStatus.AVAILABLE)
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0].incident_id, "TIMS-1001")
        self.assertEqual(incidents[0].category, "Works")

    def test_10_incidents_empty_when_no_active_disruptions(self) -> None:
        """10. When no disruptions match the corridor, returns available with empty list."""
        mock_client = MagicMock(spec=httpx.Client)
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = []
        mock_client.get.return_value = mock_resp

        provider = TfLIncidentProvider(http_client=mock_client)
        status, incidents = provider.get_incidents(self.sample_route)

        self.assertEqual(status, DataAvailabilityStatus.AVAILABLE)
        self.assertEqual(incidents, [])

    def test_11_incidents_timeout(self) -> None:
        """11. Disruption provider timeout raises IncidentTimeoutError."""
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.side_effect = httpx.TimeoutException("Read timed out")

        provider = TfLIncidentProvider(http_client=mock_client)
        with self.assertRaises(IncidentTimeoutError):
            provider.get_incidents(self.sample_route)

    # ==========================================================================
    # Journey Integration Tests (12-21)
    # ==========================================================================

    def test_12_live_context_available(self) -> None:
        """12. When weather, traffic, and incidents succeed, live_context status is AVAILABLE."""
        mock_weather = MagicMock()
        mock_weather.get_weather.return_value = WeatherContextSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            condition="Clear sky",
            temperature_c=21.0,
        )
        mock_traffic = MagicMock()
        mock_traffic.get_traffic.return_value = TrafficContextSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            congestion_level="low",
            description="A4: No Delays",
        )
        mock_incidents = MagicMock()
        mock_incidents.get_incidents.return_value = (
            DataAvailabilityStatus.AVAILABLE,
            [IncidentContextSchema(incident_id="INC-1", description="Roadworks")],
        )

        service = JourneyService(
            geocoding_provider=MagicMock(),
            routing_provider=MagicMock(),
            weather_provider=mock_weather,
            traffic_provider=mock_traffic,
            incident_provider=mock_incidents,
        )
        service._resolve_route = MagicMock(return_value=self.sample_route)

        req = JourneyAnalyzeRequest(
            source="Victoria",
            destination="Heathrow",
            travel_date=self.travel_date,
            travel_time=self.travel_time,
        )
        resp = service.analyze_journey(req)

        self.assertEqual(resp.live_context.status, DataAvailabilityStatus.AVAILABLE)
        self.assertEqual(resp.live_context.weather.condition, "Clear sky")
        self.assertEqual(resp.live_context.traffic.congestion_level, "low")
        self.assertEqual(len(resp.live_context.incidents), 1)
        self.assertTrue(resp.provenance.live_data_available)

    def test_13_live_context_partial(self) -> None:
        """13. When some providers succeed and others fail, live_context status is PARTIAL."""
        mock_weather = MagicMock()
        mock_weather.get_weather.return_value = WeatherContextSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            condition="Overcast",
            temperature_c=17.5,
        )
        mock_traffic = MagicMock()
        mock_traffic.get_traffic.return_value = TrafficContextSchema(
            status=DataAvailabilityStatus.UNAVAILABLE,
            description="Traffic provider down",
        )
        mock_incidents = MagicMock()
        mock_incidents.get_incidents.return_value = (DataAvailabilityStatus.UNAVAILABLE, [])

        service = JourneyService(
            geocoding_provider=MagicMock(),
            routing_provider=MagicMock(),
            weather_provider=mock_weather,
            traffic_provider=mock_traffic,
            incident_provider=mock_incidents,
        )
        service._resolve_route = MagicMock(return_value=self.sample_route)

        req = JourneyAnalyzeRequest(
            source="Victoria",
            destination="Heathrow",
            travel_date=self.travel_date,
            travel_time=self.travel_time,
        )
        resp = service.analyze_journey(req)

        self.assertEqual(resp.live_context.status, DataAvailabilityStatus.PARTIAL)
        self.assertTrue(resp.provenance.live_data_available)
        self.assertEqual(resp.provenance.weather_provider, "Open-Meteo")
        self.assertIsNone(resp.provenance.traffic_provider)

    def test_14_live_context_unavailable(self) -> None:
        """14. When all live providers fail, live_context status is UNAVAILABLE."""
        mock_weather = MagicMock()
        mock_weather.get_weather.side_effect = WeatherTimeoutError("Timeout")
        mock_traffic = MagicMock()
        mock_traffic.get_traffic.side_effect = TrafficTimeoutError("Timeout")
        mock_incidents = MagicMock()
        mock_incidents.get_incidents.side_effect = IncidentTimeoutError("Timeout")

        service = JourneyService(
            geocoding_provider=MagicMock(),
            routing_provider=MagicMock(),
            weather_provider=mock_weather,
            traffic_provider=mock_traffic,
            incident_provider=mock_incidents,
        )
        service._resolve_route = MagicMock(return_value=self.sample_route)

        req = JourneyAnalyzeRequest(
            source="Victoria",
            destination="Heathrow",
            travel_date=self.travel_date,
            travel_time=self.travel_time,
        )
        resp = service.analyze_journey(req)

        self.assertEqual(resp.live_context.status, DataAvailabilityStatus.UNAVAILABLE)
        self.assertFalse(resp.provenance.live_data_available)

    def test_15_provider_provenance(self) -> None:
        """15. Provenance records exact provider names for successful integrations."""
        mock_weather = MagicMock()
        mock_weather.get_weather.return_value = WeatherContextSchema(
            status=DataAvailabilityStatus.AVAILABLE, condition="Clear", temperature_c=20.0
        )
        mock_traffic = MagicMock()
        mock_traffic.get_traffic.return_value = TrafficContextSchema(
            status=DataAvailabilityStatus.AVAILABLE, congestion_level="low"
        )
        mock_incidents = MagicMock()
        mock_incidents.get_incidents.return_value = (DataAvailabilityStatus.AVAILABLE, [])

        service = JourneyService(
            geocoding_provider=MagicMock(),
            routing_provider=MagicMock(),
            weather_provider=mock_weather,
            traffic_provider=mock_traffic,
            incident_provider=mock_incidents,
        )
        service._resolve_route = MagicMock(return_value=self.sample_route)

        req = JourneyAnalyzeRequest(
            source="Victoria",
            destination="Heathrow",
            travel_date=self.travel_date,
            travel_time=self.travel_time,
        )
        resp = service.analyze_journey(req)

        self.assertEqual(resp.provenance.weather_provider, "Open-Meteo")
        self.assertEqual(resp.provenance.traffic_provider, "TfL")
        self.assertEqual(resp.provenance.incident_provider, "TfL")

    def _create_mock_providers(self):
        weather = MagicMock()
        weather.get_weather.return_value = WeatherContextSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            condition="Clear sky",
            temperature_c=20.0,
        )
        traffic = MagicMock()
        traffic.get_traffic.return_value = TrafficContextSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            congestion_level="low",
            description="A4: Good",
        )
        incidents = MagicMock()
        incidents.get_incidents.return_value = (DataAvailabilityStatus.AVAILABLE, [])
        return weather, traffic, incidents

    def test_16_requested_date_time_forwarded(self) -> None:
        """16. Requested travel date and time are passed directly to weather provider."""
        weather, traffic, incidents = self._create_mock_providers()

        service = JourneyService(
            geocoding_provider=MagicMock(),
            routing_provider=MagicMock(),
            weather_provider=weather,
            traffic_provider=traffic,
            incident_provider=incidents,
        )
        service._resolve_route = MagicMock(return_value=self.sample_route)

        req = JourneyAnalyzeRequest(
            source="Victoria",
            destination="Heathrow",
            travel_date=self.travel_date,
            travel_time=self.travel_time,
        )
        service.analyze_journey(req)

        args, kwargs = weather.get_weather.call_args
        self.assertEqual(kwargs["travel_date"], self.travel_date)
        self.assertEqual(kwargs["travel_time"], self.travel_time)

    def test_17_route_aware_location_used(self) -> None:
        """17. Weather queries the corridor midpoint coordinate rather than random city."""
        weather, traffic, incidents = self._create_mock_providers()

        service = JourneyService(
            geocoding_provider=MagicMock(),
            routing_provider=MagicMock(),
            weather_provider=weather,
            traffic_provider=traffic,
            incident_provider=incidents,
        )
        service._resolve_route = MagicMock(return_value=self.sample_route)

        req = JourneyAnalyzeRequest(
            source="Victoria",
            destination="Heathrow",
            travel_date=self.travel_date,
            travel_time=self.travel_time,
        )
        service.analyze_journey(req)

        args, kwargs = weather.get_weather.call_args
        # Midpoint of 4 coordinates is coordinates[2] = [-0.3000, 51.4850]
        self.assertAlmostEqual(kwargs["lat"], 51.4850)
        self.assertAlmostEqual(kwargs["lon"], -0.3000)

    def test_18_provider_failure_does_not_fabricate(self) -> None:
        """18. When provider fails, status is unavailable without fake values."""
        weather, traffic, incidents = self._create_mock_providers()
        weather.get_weather.side_effect = WeatherProviderError("Failed")

        service = JourneyService(
            geocoding_provider=MagicMock(),
            routing_provider=MagicMock(),
            weather_provider=weather,
            traffic_provider=traffic,
            incident_provider=incidents,
        )
        service._resolve_route = MagicMock(return_value=self.sample_route)

        req = JourneyAnalyzeRequest(
            source="Victoria",
            destination="Heathrow",
            travel_date=self.travel_date,
            travel_time=self.travel_time,
        )
        resp = service.analyze_journey(req)

        self.assertEqual(resp.live_context.weather.status, DataAvailabilityStatus.UNAVAILABLE)
        self.assertIsNone(resp.live_context.weather.temperature_c)
        self.assertIsNone(resp.live_context.weather.condition)

    def test_19_no_fake_traffic_from_osrm_duration(self) -> None:
        """19. OSRM duration is NOT used as live traffic."""
        weather, traffic, incidents = self._create_mock_providers()
        traffic.get_traffic.return_value = TrafficContextSchema(
            status=DataAvailabilityStatus.UNAVAILABLE,
            congestion_level=None,
            description="No monitored corridor",
        )

        service = JourneyService(
            geocoding_provider=MagicMock(),
            routing_provider=MagicMock(),
            weather_provider=weather,
            traffic_provider=traffic,
            incident_provider=incidents,
        )
        service._resolve_route = MagicMock(return_value=self.sample_route)

        req = JourneyAnalyzeRequest(
            source="Victoria",
            destination="Heathrow",
            travel_date=self.travel_date,
            travel_time=self.travel_time,
        )
        resp = service.analyze_journey(req)

        # Traffic should not inherit OSRM's 34.4 min duration as live congestion
        self.assertEqual(resp.live_context.traffic.status, DataAvailabilityStatus.UNAVAILABLE)
        self.assertIsNone(resp.live_context.traffic.congestion_level)

    def test_20_no_fabricated_weather(self) -> None:
        """20. Missing weather provider results in unavailable status without invented temps."""
        weather, traffic, incidents = self._create_mock_providers()
        weather.get_weather.return_value = WeatherContextSchema(
            status=DataAvailabilityStatus.UNAVAILABLE, condition=None, temperature_c=None
        )

        service = JourneyService(
            geocoding_provider=MagicMock(),
            routing_provider=MagicMock(),
            weather_provider=weather,
            traffic_provider=traffic,
            incident_provider=incidents,
        )
        service._resolve_route = MagicMock(return_value=self.sample_route)

        req = JourneyAnalyzeRequest(
            source="Victoria",
            destination="Heathrow",
            travel_date=self.travel_date,
            travel_time=self.travel_time,
        )
        resp = service.analyze_journey(req)

        self.assertIsNone(resp.live_context.weather.temperature_c)

    def test_21_no_fabricated_incidents(self) -> None:
        """21. Disruption provider returning none results in empty list, not fake accidents."""
        weather, traffic, incidents = self._create_mock_providers()
        incidents.get_incidents.return_value = (DataAvailabilityStatus.AVAILABLE, [])

        service = JourneyService(
            geocoding_provider=MagicMock(),
            routing_provider=MagicMock(),
            weather_provider=weather,
            traffic_provider=traffic,
            incident_provider=incidents,
        )
        service._resolve_route = MagicMock(return_value=self.sample_route)

        req = JourneyAnalyzeRequest(
            source="Victoria",
            destination="Heathrow",
            travel_date=self.travel_date,
            travel_time=self.travel_time,
        )
        resp = service.analyze_journey(req)

        self.assertEqual(resp.live_context.incidents, [])


if __name__ == "__main__":
    unittest.main()
