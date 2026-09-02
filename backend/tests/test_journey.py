from datetime import date, time
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.schemas.journey import (
    DataAvailabilityStatus,
    GeocodedLocationSchema,
    JourneyAnalyzeRequest,
    JourneyAnalyzeResponse,
    RouteGeometrySchema,
    RouteInfoSchema,
)
from app.services.geocoding_service import (
    GeocodingProviderError,
    GeocodingTimeoutError,
    LocationNotFoundError,
    NominatimGeocodingProvider,
)
from app.services.journey_service import JourneyService
from app.services.routing_service import (
    OSRMRoutingProvider,
    RouteNotFoundError,
    RoutingProviderError,
    RoutingTimeoutError,
)


class TestJourneySafetyAnalysis(unittest.TestCase):
    """Test suite for Journey Safety Analysis schemas, providers, and integration."""

    def setUp(self) -> None:
        self.valid_payload = {
            "source": "London Victoria Station",
            "destination": "Heathrow Airport Terminal 5",
            "travel_date": "2026-09-02",
            "travel_time": "14:30",
        }

    # ==========================================================================
    # Request Schema Validation Tests
    # ==========================================================================

    def test_valid_request_schema(self) -> None:
        """Valid parameters parse cleanly into JourneyAnalyzeRequest model."""
        req = JourneyAnalyzeRequest(
            source="London Victoria",
            destination="Heathrow Airport",
            travel_date=date(2026, 9, 2),
            travel_time=time(14, 30),
        )
        self.assertEqual(req.source, "London Victoria")
        self.assertEqual(req.destination, "Heathrow Airport")
        self.assertEqual(req.travel_date, date(2026, 9, 2))
        self.assertEqual(req.travel_time, time(14, 30))

    def test_missing_source_fails_validation(self) -> None:
        """Missing or blank source raises validation error."""
        with self.assertRaises(ValidationError):
            JourneyAnalyzeRequest(
                source="",
                destination="Heathrow Airport",
                travel_date=date(2026, 9, 2),
                travel_time=time(14, 30),
            )

    def test_whitespace_only_source_fails_validation(self) -> None:
        """Whitespace-only source raises validation error."""
        with self.assertRaises(ValidationError):
            JourneyAnalyzeRequest(
                source="   ",
                destination="Heathrow Airport",
                travel_date=date(2026, 9, 2),
                travel_time=time(14, 30),
            )

    def test_missing_destination_fails_validation(self) -> None:
        """Missing or blank destination raises validation error."""
        with self.assertRaises(ValidationError):
            JourneyAnalyzeRequest(
                source="London Victoria",
                destination="",
                travel_date=date(2026, 9, 2),
                travel_time=time(14, 30),
            )

    # ==========================================================================
    # A. Geocoding Unit Tests (1-6)
    # ==========================================================================

    def test_01_successful_source_geocoding(self) -> None:
        """1. Successful source geocoding returns parsed coordinates and label."""
        mock_client = MagicMock(spec=httpx.Client)
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = [
            {
                "lat": "51.4952",
                "lon": "-0.1441",
                "display_name": "Victoria Station, London, UK",
            }
        ]
        mock_client.get.return_value = mock_resp

        provider = NominatimGeocodingProvider(http_client=mock_client)
        result = provider.geocode("London Victoria Station")

        self.assertAlmostEqual(result.latitude, 51.4952)
        self.assertAlmostEqual(result.longitude, -0.1441)
        self.assertIn("Victoria", result.display_name)

    def test_02_successful_destination_geocoding(self) -> None:
        """2. Successful destination geocoding returns coordinates and label."""
        mock_client = MagicMock(spec=httpx.Client)
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = [
            {
                "lat": "51.4700",
                "lon": "-0.4543",
                "display_name": "Heathrow Airport, London, UK",
            }
        ]
        mock_client.get.return_value = mock_resp

        provider = NominatimGeocodingProvider(http_client=mock_client)
        result = provider.geocode("Heathrow Airport Terminal 5")

        self.assertAlmostEqual(result.latitude, 51.4700)
        self.assertAlmostEqual(result.longitude, -0.4543)

    def test_03_no_geocoding_result_raises_not_found(self) -> None:
        """3. No results returned by geocoder raises LocationNotFoundError."""
        mock_client = MagicMock(spec=httpx.Client)
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = []
        mock_client.get.return_value = mock_resp

        provider = NominatimGeocodingProvider(http_client=mock_client)
        with self.assertRaises(LocationNotFoundError):
            provider.geocode("xyz123nonexistentplace")

    def test_04_geocoding_provider_http_error(self) -> None:
        """4. Upstream HTTP error raises GeocodingProviderError."""
        mock_client = MagicMock(spec=httpx.Client)
        mock_resp = MagicMock(status_code=500, text="Internal Server Error")
        mock_client.get.return_value = mock_resp

        provider = NominatimGeocodingProvider(http_client=mock_client)
        with self.assertRaises(GeocodingProviderError):
            provider.geocode("London")

    def test_05_geocoding_provider_timeout(self) -> None:
        """5. Request timeout raises GeocodingTimeoutError."""
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.side_effect = httpx.TimeoutException("Read timed out")

        provider = NominatimGeocodingProvider(http_client=mock_client)
        with self.assertRaises(GeocodingTimeoutError):
            provider.geocode("London")

    def test_06_malformed_geocoding_response(self) -> None:
        """6. Malformed JSON structure raises GeocodingProviderError."""
        mock_client = MagicMock(spec=httpx.Client)
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = [{"invalid_key": 123}]
        mock_client.get.return_value = mock_resp

        provider = NominatimGeocodingProvider(http_client=mock_client)
        with self.assertRaises(GeocodingProviderError):
            provider.geocode("London")

    # ==========================================================================
    # B. Routing Unit Tests (7-11)
    # ==========================================================================

    def test_07_successful_routing(self) -> None:
        """7. Successful routing parses distance, duration, geometry, and segments."""
        mock_client = MagicMock(spec=httpx.Client)
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {
            "code": "Ok",
            "routes": [
                {
                    "distance": 29200.0,
                    "duration": 2100.0,
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[-0.1441, 51.4952], [-0.4543, 51.4700]],
                    },
                    "legs": [
                        {
                            "steps": [
                                {"name": "Vauxhall Bridge Road", "distance": 1200.0},
                                {"name": "M4", "distance": 28000.0},
                            ]
                        }
                    ],
                }
            ],
        }
        mock_client.get.return_value = mock_resp

        provider = OSRMRoutingProvider(http_client=mock_client)
        src = GeocodedLocationSchema(latitude=51.4952, longitude=-0.1441, display_name="Victoria")
        dst = GeocodedLocationSchema(latitude=51.4700, longitude=-0.4543, display_name="Heathrow")

        res = provider.calculate_route(src, dst)
        self.assertEqual(res.status, DataAvailabilityStatus.AVAILABLE)
        self.assertEqual(res.distance_km, 29.2)
        self.assertEqual(res.duration_minutes, 35.0)
        self.assertIsNotNone(res.geometry)
        self.assertEqual(len(res.geometry.coordinates), 2)
        self.assertEqual(len(res.segments), 2)
        self.assertEqual(res.segments[0].name, "Vauxhall Bridge Road")
        self.assertEqual(res.provider, "OSRM")

    def test_08_routing_provider_http_error(self) -> None:
        """8. Routing provider HTTP 500 error raises RoutingProviderError."""
        mock_client = MagicMock(spec=httpx.Client)
        mock_resp = MagicMock(status_code=500, text="Internal Server Error")
        mock_client.get.return_value = mock_resp

        provider = OSRMRoutingProvider(http_client=mock_client)
        src = GeocodedLocationSchema(latitude=51.4952, longitude=-0.1441, display_name="Victoria")
        dst = GeocodedLocationSchema(latitude=51.4700, longitude=-0.4543, display_name="Heathrow")

        with self.assertRaises(RoutingProviderError):
            provider.calculate_route(src, dst)

    def test_09_routing_timeout(self) -> None:
        """9. Routing request timeout raises RoutingTimeoutError."""
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.side_effect = httpx.TimeoutException("Read timed out")

        provider = OSRMRoutingProvider(http_client=mock_client)
        src = GeocodedLocationSchema(latitude=51.4952, longitude=-0.1441, display_name="Victoria")
        dst = GeocodedLocationSchema(latitude=51.4700, longitude=-0.4543, display_name="Heathrow")

        with self.assertRaises(RoutingTimeoutError):
            provider.calculate_route(src, dst)

    def test_10_malformed_routing_response(self) -> None:
        """10. Malformed routing JSON raises RoutingProviderError."""
        mock_client = MagicMock(spec=httpx.Client)
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"code": "Ok", "routes": []}
        mock_client.get.return_value = mock_resp

        provider = OSRMRoutingProvider(http_client=mock_client)
        src = GeocodedLocationSchema(latitude=51.4952, longitude=-0.1441, display_name="Victoria")
        dst = GeocodedLocationSchema(latitude=51.4700, longitude=-0.4543, display_name="Heathrow")

        with self.assertRaises(RouteNotFoundError):
            provider.calculate_route(src, dst)

    def test_11_geometry_normalization(self) -> None:
        """11. GeoJSON LineString geometry is normalized into RouteGeometrySchema."""
        coords = [[-0.1441, 51.4952], [-0.2, 51.48], [-0.4543, 51.4700]]
        geom = RouteGeometrySchema(type="LineString", coordinates=coords)
        self.assertEqual(geom.type, "LineString")
        self.assertEqual(len(geom.coordinates), 3)
        self.assertEqual(geom.coordinates[0], [-0.1441, 51.4952])

    # ==========================================================================
    # C. Journey Integration Tests (12-20)
    # ==========================================================================

    def test_12_successful_journey_with_real_provider_shape(self) -> None:
        """12. Successful journey execution populates route and preserved sections."""
        mock_geocoder = MagicMock(spec=NominatimGeocodingProvider)
        mock_geocoder.geocode.side_effect = [
            GeocodedLocationSchema(latitude=51.4952, longitude=-0.1441, display_name="Victoria Station"),
            GeocodedLocationSchema(latitude=51.4700, longitude=-0.4543, display_name="Heathrow Terminal 5"),
        ]
        mock_router = MagicMock(spec=OSRMRoutingProvider)
        mock_router.calculate_route.return_value = RouteInfoSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            source=GeocodedLocationSchema(latitude=51.4952, longitude=-0.1441, display_name="Victoria Station"),
            destination=GeocodedLocationSchema(latitude=51.4700, longitude=-0.4543, display_name="Heathrow Terminal 5"),
            distance_km=29.2,
            duration_minutes=35.0,
            geometry=RouteGeometrySchema(type="LineString", coordinates=[[-0.1441, 51.4952], [-0.4543, 51.4700]]),
            provider="OSRM",
            segments=[],
        )

        service = JourneyService(geocoding_provider=mock_geocoder, routing_provider=mock_router)
        req = JourneyAnalyzeRequest.model_validate(self.valid_payload)
        resp = service.analyze_journey(req)

        self.assertIsInstance(resp, JourneyAnalyzeResponse)
        self.assertEqual(resp.route.status, DataAvailabilityStatus.AVAILABLE)
        self.assertEqual(resp.route.distance_km, 29.2)
        self.assertEqual(resp.route.duration_minutes, 35.0)
        self.assertEqual(resp.route.provider, "OSRM")

    def test_13_source_geocoding_failure(self) -> None:
        """13. Source geocoding failure raises LocationNotFoundError."""
        mock_geocoder = MagicMock(spec=NominatimGeocodingProvider)
        mock_geocoder.geocode.side_effect = LocationNotFoundError("Origin not found")
        mock_router = MagicMock(spec=OSRMRoutingProvider)

        service = JourneyService(geocoding_provider=mock_geocoder, routing_provider=mock_router)
        req = JourneyAnalyzeRequest.model_validate(self.valid_payload)

        with self.assertRaises(LocationNotFoundError):
            service.analyze_journey(req)
        # Verify routing was never attempted
        mock_router.calculate_route.assert_not_called()

    def test_14_destination_geocoding_failure(self) -> None:
        """14. Destination geocoding failure raises LocationNotFoundError."""
        mock_geocoder = MagicMock(spec=NominatimGeocodingProvider)
        mock_geocoder.geocode.side_effect = [
            GeocodedLocationSchema(latitude=51.4952, longitude=-0.1441, display_name="Victoria Station"),
            LocationNotFoundError("Destination not found"),
        ]
        mock_router = MagicMock(spec=OSRMRoutingProvider)

        service = JourneyService(geocoding_provider=mock_geocoder, routing_provider=mock_router)
        req = JourneyAnalyzeRequest.model_validate(self.valid_payload)

        with self.assertRaises(LocationNotFoundError):
            service.analyze_journey(req)
        mock_router.calculate_route.assert_not_called()

    def test_15_routing_failure(self) -> None:
        """15. Routing failure raises RouteNotFoundError."""
        mock_geocoder = MagicMock(spec=NominatimGeocodingProvider)
        mock_geocoder.geocode.side_effect = [
            GeocodedLocationSchema(latitude=51.4952, longitude=-0.1441, display_name="Victoria Station"),
            GeocodedLocationSchema(latitude=51.4700, longitude=-0.4543, display_name="Heathrow Terminal 5"),
        ]
        mock_router = MagicMock(spec=OSRMRoutingProvider)
        mock_router.calculate_route.side_effect = RouteNotFoundError("No route found")

        service = JourneyService(geocoding_provider=mock_geocoder, routing_provider=mock_router)
        req = JourneyAnalyzeRequest.model_validate(self.valid_payload)

        with self.assertRaises(RouteNotFoundError):
            service.analyze_journey(req)

    def test_16_no_fabricated_coordinates(self) -> None:
        """16. When routing is computed, coordinates come exclusively from geocoder."""
        mock_geocoder = MagicMock(spec=NominatimGeocodingProvider)
        src_geo = GeocodedLocationSchema(latitude=51.4952, longitude=-0.1441, display_name="Victoria")
        dst_geo = GeocodedLocationSchema(latitude=51.4700, longitude=-0.4543, display_name="Heathrow")
        mock_geocoder.geocode.side_effect = [src_geo, dst_geo]

        mock_router = MagicMock(spec=OSRMRoutingProvider)
        mock_router.calculate_route.return_value = RouteInfoSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            source=src_geo,
            destination=dst_geo,
            distance_km=29.2,
            duration_minutes=35.0,
            geometry=RouteGeometrySchema(type="LineString", coordinates=[]),
            provider="OSRM",
        )

        service = JourneyService(geocoding_provider=mock_geocoder, routing_provider=mock_router)
        req = JourneyAnalyzeRequest.model_validate(self.valid_payload)
        resp = service.analyze_journey(req)

        self.assertEqual(resp.route.source.latitude, 51.4952)
        self.assertEqual(resp.route.destination.latitude, 51.4700)

    def test_17_no_fabricated_distance(self) -> None:
        """17. Distance is derived strictly from provider response."""
        mock_geocoder = MagicMock(spec=NominatimGeocodingProvider)
        src_geo = GeocodedLocationSchema(latitude=51.4952, longitude=-0.1441, display_name="Victoria")
        dst_geo = GeocodedLocationSchema(latitude=51.4700, longitude=-0.4543, display_name="Heathrow")
        mock_geocoder.geocode.side_effect = [src_geo, dst_geo]

        mock_router = MagicMock(spec=OSRMRoutingProvider)
        mock_router.calculate_route.return_value = RouteInfoSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            source=src_geo,
            destination=dst_geo,
            distance_km=42.75,
            duration_minutes=48.2,
            geometry=RouteGeometrySchema(type="LineString", coordinates=[]),
            provider="OSRM",
        )

        service = JourneyService(geocoding_provider=mock_geocoder, routing_provider=mock_router)
        req = JourneyAnalyzeRequest.model_validate(self.valid_payload)
        resp = service.analyze_journey(req)

        self.assertEqual(resp.route.distance_km, 42.75)

    def test_18_no_fabricated_duration(self) -> None:
        """18. Duration is derived strictly from provider response."""
        mock_geocoder = MagicMock(spec=NominatimGeocodingProvider)
        src_geo = GeocodedLocationSchema(latitude=51.4952, longitude=-0.1441, display_name="Victoria")
        dst_geo = GeocodedLocationSchema(latitude=51.4700, longitude=-0.4543, display_name="Heathrow")
        mock_geocoder.geocode.side_effect = [src_geo, dst_geo]

        mock_router = MagicMock(spec=OSRMRoutingProvider)
        mock_router.calculate_route.return_value = RouteInfoSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            source=src_geo,
            destination=dst_geo,
            distance_km=42.75,
            duration_minutes=48.2,
            geometry=RouteGeometrySchema(type="LineString", coordinates=[]),
            provider="OSRM",
        )

        service = JourneyService(geocoding_provider=mock_geocoder, routing_provider=mock_router)
        req = JourneyAnalyzeRequest.model_validate(self.valid_payload)
        resp = service.analyze_journey(req)

        self.assertEqual(resp.route.duration_minutes, 48.2)

    def test_19_route_provider_provenance(self) -> None:
        """19. Provenance reflects actual routing provider while other flags remain False."""
        mock_geocoder = MagicMock(spec=NominatimGeocodingProvider)
        src_geo = GeocodedLocationSchema(latitude=51.4952, longitude=-0.1441, display_name="Victoria")
        dst_geo = GeocodedLocationSchema(latitude=51.4700, longitude=-0.4543, display_name="Heathrow")
        mock_geocoder.geocode.side_effect = [src_geo, dst_geo]

        mock_router = MagicMock(spec=OSRMRoutingProvider)
        mock_router.calculate_route.return_value = RouteInfoSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            source=src_geo,
            destination=dst_geo,
            distance_km=29.2,
            duration_minutes=35.0,
            geometry=RouteGeometrySchema(type="LineString", coordinates=[]),
            provider="OSRM",
        )

        service = JourneyService(geocoding_provider=mock_geocoder, routing_provider=mock_router)
        req = JourneyAnalyzeRequest.model_validate(self.valid_payload)
        resp = service.analyze_journey(req)

        self.assertEqual(resp.provenance.route_provider, "OSRM")
        self.assertFalse(resp.provenance.live_data_available)
        self.assertFalse(resp.provenance.historical_data_available)
        self.assertFalse(resp.provenance.student_a_used)
        self.assertFalse(resp.provenance.student_b_used)
        self.assertFalse(resp.provenance.student_c_used)
        self.assertFalse(resp.provenance.gemini_used)

    def test_20_pending_states_for_unintegrated_sections(self) -> None:
        """20. Live context, historical evidence, and LLM synthesis truthfully remain pending."""
        mock_geocoder = MagicMock(spec=NominatimGeocodingProvider)
        src_geo = GeocodedLocationSchema(latitude=51.4952, longitude=-0.1441, display_name="Victoria")
        dst_geo = GeocodedLocationSchema(latitude=51.4700, longitude=-0.4543, display_name="Heathrow")
        mock_geocoder.geocode.side_effect = [src_geo, dst_geo]

        mock_router = MagicMock(spec=OSRMRoutingProvider)
        mock_router.calculate_route.return_value = RouteInfoSchema(
            status=DataAvailabilityStatus.AVAILABLE,
            source=src_geo,
            destination=dst_geo,
            distance_km=29.2,
            duration_minutes=35.0,
            geometry=RouteGeometrySchema(type="LineString", coordinates=[]),
            provider="OSRM",
        )

        service = JourneyService(geocoding_provider=mock_geocoder, routing_provider=mock_router)
        req = JourneyAnalyzeRequest.model_validate(self.valid_payload)
        resp = service.analyze_journey(req)

        self.assertEqual(resp.live_context.status, DataAvailabilityStatus.PENDING)
        self.assertEqual(resp.historical_evidence.status, DataAvailabilityStatus.PENDING)
        self.assertEqual(resp.safety_assessment.status, DataAvailabilityStatus.PENDING)
        self.assertEqual(resp.llm_synthesis.status, DataAvailabilityStatus.PENDING)


if __name__ == "__main__":
    unittest.main()
