import json
import unittest
from unittest.mock import MagicMock

from fastapi import HTTPException

from app.schemas.report import (
    AIInfrastructureReportRequest,
    AIInfrastructureReportResponse,
    PriorityLevel,
    ReportProvenanceSchema,
    ReportSummarySchema,
)
from app.services.llm_provider import (
    LLMConfigurationError,
    LLMProvider,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMValidationError,
)
from app.services.llm_report_service import LLMReportService
from app.services.report_grounding_service import ReportGroundingService
from app.services.report_prompt_service import ReportPromptService


class TestLLMReportService(unittest.TestCase):
    """Test suite for LLMReportService orchestration and error mappings."""

    def setUp(self) -> None:
        self.mock_grounding_service = MagicMock(spec=ReportGroundingService)
        self.mock_provider = MagicMock(spec=LLMProvider)

        self.service = LLMReportService(
            grounding_service=self.mock_grounding_service,
            prompt_service=ReportPromptService,
            provider=self.mock_provider,
        )

        self.sample_valid_response = AIInfrastructureReportResponse(
            generatedLabel="LLM_GENERATED_LABEL_SHOULD_BE_OVERRIDDEN",
            signals=[],
            interventions=[],
            evidence=[],
            recommendations=[],
            priorities=[],
            summary=ReportSummarySchema(
                theme="Corridor overhaul",
                topIntervention="Roundabout conversion",
                keySignal="GNN Risk > 0.15",
                nextStep="Engineering audit",
            ),
            provenance=ReportProvenanceSchema(
                student_a_model="LLM_FAKE_MODEL",
                student_b_hotspots="LLM_FAKE_HOTSPOTS",
                student_c_gnn="LLM_FAKE_GNN",
                grounded=False,
            ),
        )

    def test_successful_report_orchestration(self) -> None:
        """Service must orchestrate grounding -> prompt -> provider and enforce application-owned fields."""
        real_grounding = ReportGroundingService()
        req = AIInfrastructureReportRequest(region="central")
        real_payload = real_grounding.build_grounding_payload(req)
        self.mock_grounding_service.build_grounding_payload.return_value = real_payload

        self.mock_provider.generate_structured_report.return_value = self.sample_valid_response

        response = self.service.generate_report(req)

        self.mock_grounding_service.build_grounding_payload.assert_called_once_with(req)
        self.mock_provider.generate_structured_report.assert_called_once()

        # Check application-owned timestamp and provenance override
        self.assertIn("Generated", response.generatedLabel)
        self.assertIn("UTC", response.generatedLabel)
        self.assertEqual(response.provenance.student_a_model, "RandomForestClassifier")
        self.assertEqual(response.provenance.student_b_hotspots, "DBSCAN")
        self.assertEqual(response.provenance.student_c_gnn, "RoadRiskGNN")
        self.assertTrue(response.provenance.grounded)

    def test_missing_api_key_maps_to_503(self) -> None:
        """LLMConfigurationError must map to HTTP 503 Service Unavailable."""
        real_grounding = ReportGroundingService()
        req = AIInfrastructureReportRequest(region="all")
        self.mock_grounding_service.build_grounding_payload.return_value = (
            real_grounding.build_grounding_payload(req)
        )
        self.mock_provider.generate_structured_report.side_effect = LLMConfigurationError(
            "API key missing"
        )

        with self.assertRaises(HTTPException) as ctx:
            self.service.generate_report(req)

        self.assertEqual(ctx.exception.status_code, 503)
        self.assertIn("missing API credentials", ctx.exception.detail)

    def test_timeout_maps_to_504(self) -> None:
        """LLMTimeoutError must map to HTTP 504 Gateway Timeout."""
        real_grounding = ReportGroundingService()
        req = AIInfrastructureReportRequest(region="all")
        self.mock_grounding_service.build_grounding_payload.return_value = (
            real_grounding.build_grounding_payload(req)
        )
        self.mock_provider.generate_structured_report.side_effect = LLMTimeoutError(
            "Timed out"
        )

        with self.assertRaises(HTTPException) as ctx:
            self.service.generate_report(req)

        self.assertEqual(ctx.exception.status_code, 504)
        self.assertIn("timed out", ctx.exception.detail)

    def test_rate_limit_maps_to_429(self) -> None:
        """LLMRateLimitError must map to HTTP 429 Too Many Requests."""
        real_grounding = ReportGroundingService()
        req = AIInfrastructureReportRequest(region="all")
        self.mock_grounding_service.build_grounding_payload.return_value = (
            real_grounding.build_grounding_payload(req)
        )
        self.mock_provider.generate_structured_report.side_effect = LLMRateLimitError(
            "Rate limited"
        )

        with self.assertRaises(HTTPException) as ctx:
            self.service.generate_report(req)

        self.assertEqual(ctx.exception.status_code, 429)
        self.assertIn("rate limited", ctx.exception.detail)

    def test_validation_error_maps_to_502(self) -> None:
        """LLMValidationError must map to HTTP 502 Bad Gateway."""
        real_grounding = ReportGroundingService()
        req = AIInfrastructureReportRequest(region="all")
        self.mock_grounding_service.build_grounding_payload.return_value = (
            real_grounding.build_grounding_payload(req)
        )
        self.mock_provider.generate_structured_report.side_effect = LLMValidationError(
            "Malformed output"
        )

        with self.assertRaises(HTTPException) as ctx:
            self.service.generate_report(req)

        self.assertEqual(ctx.exception.status_code, 502)
        self.assertIn("unreadable or malformed", ctx.exception.detail)


if __name__ == "__main__":
    unittest.main()

