"""Tests for Phase 4F-A: Backend Production Hardening & Configuration.

Verifies:
1. CORS configuration parsing (comma-separated string, JSON array, defaults) and headers.
2. Global unexpected-exception handler (safe HTTP 500, error_id, no leak, preserving 404 and 422).
3. Corridor matching pre-warming (BallTree spatial index pre-construction in lifespan).
4. Bounded Nominatim geocoding cache with TTL (normalization, LRU, failure exclusion).
5. OpenAPI documentation accuracy (no mock statements).
"""

from collections import OrderedDict
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import MagicMock, patch

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from app.config import Settings, settings
from app.main import app
from app.schemas.journey import GeocodedLocationSchema
from app.services.corridor_matching_service import CorridorMatchingService
from app.services.geocoding_service import (
    GeocodingProviderError,
    LocationNotFoundError,
    NominatimGeocodingProvider,
)


class TestCORSConfiguration(unittest.TestCase):
    """Verifies CORS origin validation and HTTP response headers."""

    def test_default_cors_origins(self):
        s = Settings()
        self.assertIn("http://localhost:5173", s.CORS_ORIGINS)
        self.assertIn("http://localhost:3000", s.CORS_ORIGINS)
        self.assertIn("http://127.0.0.1:5173", s.CORS_ORIGINS)

    def test_comma_separated_cors_origins(self):
        s = Settings(CORS_ORIGINS="https://example.com, https://app.example.com, http://localhost:8080")
        self.assertEqual(
            s.CORS_ORIGINS,
            ["https://example.com", "https://app.example.com", "http://localhost:8080"],
        )

    def test_json_array_cors_origins(self):
        s = Settings(CORS_ORIGINS='["https://production.domain", "https://staging.domain"]')
        self.assertEqual(
            s.CORS_ORIGINS,
            ["https://production.domain", "https://staging.domain"],
        )

    def test_cors_headers_allowed_origin(self):
        client = TestClient(app)
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:5173"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("access-control-allow-origin"),
            "http://localhost:5173",
        )

    def test_cors_headers_disallowed_origin(self):
        client = TestClient(app)
        response = client.get(
            "/health",
            headers={"Origin": "https://unauthorized-malicious-domain.com"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.headers.get("access-control-allow-origin"))


class TestGlobalExceptionHandler(unittest.TestCase):
    """Verifies safe HTTP 500 handling without leaking internals or stack traces."""

    def setUp(self):
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_unhandled_exception_returns_safe_500(self):
        # Trigger an unexpected exception by patching a route dependency
        with patch(
            "app.services.journey_service.JourneyService.analyze_journey",
            side_effect=RuntimeError("Database failure with secret_token=abcdef123456!"),
        ):
            response = self.client.post(
                "/journey/analyze",
                json={
                    "source": "London",
                    "destination": "Oxford",
                    "travel_date": "2026-06-01",
                    "travel_time": "12:00:00",
                },
            )
            self.assertEqual(response.status_code, 500)
            data = response.json()
            self.assertIn("error_id", data)
            self.assertIn("detail", data)
            self.assertTrue(data["error_id"].startswith("err-"))
            # Ensure internal exception message and token are NOT leaked
            self.assertNotIn("secret_token", data["detail"])
            self.assertNotIn("Database failure", data["detail"])
            self.assertNotIn("Traceback", str(data))

    def test_http_404_preserved(self):
        response = self.client.get("/nonexistent-route-path-xyz")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data.get("detail"), "Not Found")
        # Should not be wrapped in 500 error envelope
        self.assertNotIn("error_id", data)

    def test_validation_error_422_preserved(self):
        response = self.client.post(
            "/journey/analyze",
            json={"invalid_field": "test"},
        )
        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertIn("detail", data)
        # Should be a standard Pydantic validation list
        self.assertIsInstance(data["detail"], list)


class TestCorridorMatchingPrewarm(unittest.TestCase):
    """Verifies that corridor spatial index trees prewarm during startup."""

    def tearDown(self):
        # Restore prewarmed state if affected
        CorridorMatchingService.prewarm()

    def test_prewarm_lifecycle(self):
        CorridorMatchingService.clear_cache()
        self.assertFalse(CorridorMatchingService.is_prewarmed())

        CorridorMatchingService.prewarm()
        self.assertTrue(CorridorMatchingService.is_prewarmed())

        # Calling prewarm a second time is a safe no-op
        CorridorMatchingService.prewarm()
        self.assertTrue(CorridorMatchingService.is_prewarmed())

    def test_instance_reuses_prewarmed_trees(self):
        CorridorMatchingService.prewarm()
        service = CorridorMatchingService()
        self.assertIsNotNone(service._hotspot_tree)
        self.assertIsNotNone(service._segment_tree)
        # Verify trees match class variables
        self.assertIs(service._hotspot_tree, CorridorMatchingService._shared_hotspot_tree)
        self.assertIs(service._segment_tree, CorridorMatchingService._shared_segment_tree)


class TestGeocodingCache(unittest.TestCase):
    """Verifies bounded Nominatim geocoding cache with TTL and normalization."""

    def setUp(self):
        NominatimGeocodingProvider.clear_cache()

    def tearDown(self):
        NominatimGeocodingProvider.clear_cache()

    def test_cache_hit_with_normalized_query(self):
        mock_client = MagicMock(spec=httpx.Client)
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "lat": "51.5080",
                "lon": "-0.1281",
                "display_name": "Trafalgar Square, Westminster, London, SW1A 2DX, UK",
            }
        ]
        mock_client.get.return_value = mock_response
        provider = NominatimGeocodingProvider(http_client=mock_client)

        # First query
        res1 = provider.geocode("Trafalgar Square, London")
        self.assertEqual(res1.latitude, 51.5080)
        self.assertEqual(mock_client.get.call_count, 1)
        self.assertEqual(NominatimGeocodingProvider.get_cache_size(), 1)

        # Second query with whitespace and case variations -> should hit cache
        res2 = provider.geocode("  trafalgar  square,   LONDON  ")
        self.assertEqual(res2.latitude, 51.5080)
        self.assertEqual(mock_client.get.call_count, 1)  # No extra HTTP call
        self.assertEqual(NominatimGeocodingProvider.get_cache_size(), 1)

    def test_cache_does_not_store_failures(self):
        mock_client = MagicMock(spec=httpx.Client)
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = []  # Empty results -> LocationNotFoundError
        mock_client.get.return_value = mock_response
        provider = NominatimGeocodingProvider(http_client=mock_client)

        with self.assertRaises(LocationNotFoundError):
            provider.geocode("Totally Unknown Nowhere Place 12345")

        self.assertEqual(NominatimGeocodingProvider.get_cache_size(), 0)

        # Subsequent call attempts HTTP again
        with self.assertRaises(LocationNotFoundError):
            provider.geocode("Totally Unknown Nowhere Place 12345")

        self.assertEqual(mock_client.get.call_count, 2)

    def test_cache_ttl_expiration(self):
        mock_client = MagicMock(spec=httpx.Client)
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "lat": "51.5",
                "lon": "-0.1",
                "display_name": "London, UK",
            }
        ]
        mock_client.get.return_value = mock_response
        provider = NominatimGeocodingProvider(http_client=mock_client)

        # Query at t0
        with patch("time.time", return_value=1000.0):
            provider.geocode("London, UK")
            self.assertEqual(mock_client.get.call_count, 1)

        # Query at t0 + 10s (within 3600s TTL) -> hits cache
        with patch("time.time", return_value=1010.0):
            provider.geocode("London, UK")
            self.assertEqual(mock_client.get.call_count, 1)

        # Query at t0 + 4000s (expired) -> misses cache and fetches
        with patch("time.time", return_value=5000.0):
            provider.geocode("London, UK")
            self.assertEqual(mock_client.get.call_count, 2)

    def test_cache_eviction_when_full(self):
        # Test LRU eviction with cache_max_size = 2
        provider = NominatimGeocodingProvider(cache_max_size=2)
        mock_client = MagicMock(spec=httpx.Client)
        provider._client = mock_client

        def make_response(name, lat, lon):
            res = MagicMock(spec=httpx.Response)
            res.status_code = 200
            res.json.return_value = [{"lat": str(lat), "lon": str(lon), "display_name": name}]
            return res

        mock_client.get.side_effect = [
            make_response("Place 1", 1.0, 1.0),
            make_response("Place 2", 2.0, 2.0),
            make_response("Place 3", 3.0, 3.0),
        ]

        provider.geocode("Query 1")
        provider.geocode("Query 2")
        self.assertEqual(NominatimGeocodingProvider.get_cache_size(), 2)

        # Query 3 should evict Query 1 (the oldest)
        provider.geocode("Query 3")
        self.assertEqual(NominatimGeocodingProvider.get_cache_size(), 2)

        cache_keys = list(NominatimGeocodingProvider._cache.keys())
        self.assertNotIn("query 1", cache_keys)
        self.assertIn("query 2", cache_keys)
        self.assertIn("query 3", cache_keys)


class TestAPIDescription(unittest.TestCase):
    """Verifies that API documentation does not contain obsolete mock descriptions."""

    def test_api_description_accurate(self):
        desc = app.description.lower()
        self.assertNotIn("mock", desc)
        self.assertNotIn("simulated data", desc)
        self.assertNotIn("placeholder", desc)
        self.assertIn("student a", desc)
        self.assertIn("student b", desc)
        self.assertIn("student c", desc)
        self.assertIn("journey safety analysis", desc)
        self.assertIn("gemini", desc)


if __name__ == "__main__":
    unittest.main()
