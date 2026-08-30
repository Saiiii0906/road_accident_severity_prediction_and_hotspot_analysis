import json
import unittest
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.routes.report_route import get_llm_report_service
from app.schemas.report import (
    AIInfrastructureReportResponse,
    PriorityLevel,
    PriorityMatrixRowSchema,
    RecommendationSchema,
    ReportProvenanceSchema,
    ReportSummarySchema,
    RiskSignalSchema,
)
from app.services.llm_provider import (
    LLMConfigurationError,
    LLMProvider,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from app.services.llm_report_service import LLMReportService
from app.services.report_grounding_service import ReportGroundingService
from app.services.report_prompt_service import ReportPromptService


class TestReportRouteIntegration(unittest.TestCase):
    """Integration test suite for POST /api/reports/ai-infrastructure-report."""

    def setUp(self) -> None:
        self.mock_provider = MagicMock(spec=LLMProvider)
        self.grounding_service = ReportGroundingService()

        self.mock_report_service = LLMReportService(
            grounding_service=self.grounding_service,
            prompt_service=ReportPromptService,
            provider=self.mock_provider,
        )

        app.dependency_overrides[get_llm_report_service] = lambda: self.mock_report_service
        self.client = TestClient(app)

        self.valid_response_model = AIInfrastructureReportResponse(
            generatedLabel="Temporary",
            signals=[
                RiskSignalSchema(
                    id="sig-1",
                    label="Corridor Density",
                    value="1,240 collisions",
                    note="A1 Highway",
                    level=PriorityLevel.CRITICAL,
                )
            ],
            interventions=[],
            evidence=[],
            recommendations=[
                RecommendationSchema(
                    id="rec-1",
                    title="Install Speed Cameras",
                    why="Speeding is elevated",
                    objective="Reduce speeds",
                    level=PriorityLevel.HIGH,
                    supportingSignals=["sig-1"],
                )
            ],
            priorities=[],
            summary=ReportSummarySchema(
                theme="Corridor overhaul",
                topIntervention="Speed enforcement",
                keySignal="Cluster density",
                nextStep="Deploy mobile camera units",
            ),
            provenance=ReportProvenanceSchema(
                student_a_model="RandomForestClassifier",
                student_b_hotspots="DBSCAN",
                student_c_gnn="RoadRiskGNN",
                grounded=True,
            ),
        )

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_successful_report_endpoint(self) -> None:
        """Endpoint should return HTTP 200 and complete validated report."""
        self.mock_provider.generate_structured_report.return_value = self.valid_response_model

        response = self.client.post(
            "/api/reports/ai-infrastructure-report",
            json={
                "region": "all",
                "period": "last_12_months",
                "threshold": "moderate",
                "focus": "overall_safety",
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("generatedLabel", data)
        self.assertEqual(len(data["signals"]), 1)
        self.assertEqual(data["summary"]["topIntervention"], "Speed enforcement")
        self.assertTrue(data["provenance"]["grounded"])

    def test_missing_api_key_returns_503(self) -> None:
        """Endpoint should return HTTP 503 when LLM is unconfigured."""
        self.mock_provider.generate_structured_report.side_effect = LLMConfigurationError(
            "Missing key"
        )

        response = self.client.post(
            "/api/reports/ai-infrastructure-report",
            json={"region": "all"},
        )

        self.assertEqual(response.status_code, 503)
        self.assertIn("not configured", response.json()["detail"])

    def test_timeout_returns_504(self) -> None:
        """Endpoint should return HTTP 504 on provider timeout."""
        self.mock_provider.generate_structured_report.side_effect = LLMTimeoutError(
            "Timed out"
        )

        response = self.client.post(
            "/api/reports/ai-infrastructure-report",
            json={"region": "all"},
        )

        self.assertEqual(response.status_code, 504)
        self.assertIn("timed out", response.json()["detail"])

    def test_rate_limit_returns_429(self) -> None:
        """Endpoint should return HTTP 429 on provider rate limit."""
        self.mock_provider.generate_structured_report.side_effect = LLMRateLimitError(
            "Rate limit"
        )

        response = self.client.post(
            "/api/reports/ai-infrastructure-report",
            json={"region": "all"},
        )

        self.assertEqual(response.status_code, 429)
        self.assertIn("rate limited", response.json()["detail"])

    def test_upstream_provider_failure_returns_502(self) -> None:
        """Endpoint should return HTTP 502 on upstream provider failure."""
        self.mock_provider.generate_structured_report.side_effect = LLMProviderError(
            "500 Internal Error"
        )

        response = self.client.post(
            "/api/reports/ai-infrastructure-report",
            json={"region": "all"},
        )

        self.assertEqual(response.status_code, 502)
        self.assertIn("upstream", response.json()["detail"].lower())


if __name__ == "__main__":
    unittest.main()

