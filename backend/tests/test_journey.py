from datetime import date, time
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.schemas.journey import (
    DataAvailabilityStatus,
    JourneyAnalyzeRequest,
    JourneyAnalyzeResponse,
)
from app.services.journey_service import JourneyService


class TestJourneySafetyAnalysis(unittest.TestCase):
    """Test suite for Journey Safety Analysis schemas, service, and API endpoints."""

    def setUp(self) -> None:
        self.service = JourneyService()
        self.client = TestClient(app)
        self.valid_payload = {
            "source": "London Victoria Station",
            "destination": "Heathrow Airport Terminal 5",
            "travel_date": "2026-09-02",
            "travel_time": "14:30",
        }

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

    def test_service_returns_truthful_response_structure(self) -> None:
        """Service returns complete JourneyAnalyzeResponse with truthful pending statuses."""
        req = JourneyAnalyzeRequest.model_validate(self.valid_payload)
        resp = self.service.analyze_journey(req)

        self.assertIsInstance(resp, JourneyAnalyzeResponse)
        self.assertEqual(resp.journey.source, "London Victoria Station")
        self.assertEqual(resp.journey.destination, "Heathrow Airport Terminal 5")
        self.assertEqual(resp.journey.travel_date, "2026-09-02")
        self.assertEqual(resp.journey.travel_time, "14:30")

        # Verify no fabricated data
        self.assertEqual(resp.route.status, DataAvailabilityStatus.PENDING)
        self.assertIsNone(resp.route.distance_km)
        self.assertIsNone(resp.route.duration_minutes)
        self.assertEqual(resp.route.segments, [])

        self.assertEqual(resp.live_context.status, DataAvailabilityStatus.PENDING)
        self.assertIsNone(resp.live_context.traffic)
        self.assertIsNone(resp.live_context.weather)
        self.assertEqual(resp.live_context.incidents, [])

        self.assertEqual(resp.historical_evidence.status, DataAvailabilityStatus.PENDING)
        self.assertIsNone(resp.historical_evidence.student_a)
        self.assertIsNone(resp.historical_evidence.student_b)
        self.assertIsNone(resp.historical_evidence.student_c)

        # Verify provenance flags
        self.assertFalse(resp.provenance.live_data_available)
        self.assertFalse(resp.provenance.historical_data_available)
        self.assertFalse(resp.provenance.student_a_used)
        self.assertFalse(resp.provenance.student_b_used)
        self.assertFalse(resp.provenance.student_c_used)
        self.assertFalse(resp.provenance.gemini_used)
        self.assertIsNone(resp.provenance.route_provider)

    def test_api_endpoint_post_journey_analyze_success(self) -> None:
        """POST /api/journey/analyze returns HTTP 200 with valid response payload."""
        response = self.client.post("/api/journey/analyze", json=self.valid_payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["journey"]["source"], "London Victoria Station")
        self.assertEqual(data["journey"]["destination"], "Heathrow Airport Terminal 5")
        self.assertEqual(data["route"]["status"], "pending")
        self.assertEqual(data["live_context"]["status"], "pending")
        self.assertEqual(data["historical_evidence"]["status"], "pending")
        self.assertEqual(data["safety_assessment"]["status"], "pending")
        self.assertEqual(data["llm_synthesis"]["status"], "pending")
        self.assertFalse(data["provenance"]["gemini_used"])

    def test_api_endpoint_canonical_route_success(self) -> None:
        """POST /journey/analyze (unprefixed) also succeeds."""
        response = self.client.post("/journey/analyze", json=self.valid_payload)
        self.assertEqual(response.status_code, 200)

    def test_api_endpoint_missing_source_returns_422(self) -> None:
        """Missing source returns HTTP 422 Unprocessable Entity."""
        bad_payload = dict(self.valid_payload)
        del bad_payload["source"]
        response = self.client.post("/api/journey/analyze", json=bad_payload)
        self.assertEqual(response.status_code, 422)

    def test_api_endpoint_missing_destination_returns_422(self) -> None:
        """Missing destination returns HTTP 422 Unprocessable Entity."""
        bad_payload = dict(self.valid_payload)
        del bad_payload["destination"]
        response = self.client.post("/api/journey/analyze", json=bad_payload)
        self.assertEqual(response.status_code, 422)

    def test_api_endpoint_invalid_date_returns_422(self) -> None:
        """Malformed date string returns HTTP 422 Unprocessable Entity."""
        bad_payload = dict(self.valid_payload, travel_date="invalid-date")
        response = self.client.post("/api/journey/analyze", json=bad_payload)
        self.assertEqual(response.status_code, 422)

    def test_api_endpoint_invalid_time_returns_422(self) -> None:
        """Malformed time string returns HTTP 422 Unprocessable Entity."""
        bad_payload = dict(self.valid_payload, travel_time="25:99")
        response = self.client.post("/api/journey/analyze", json=bad_payload)
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()

