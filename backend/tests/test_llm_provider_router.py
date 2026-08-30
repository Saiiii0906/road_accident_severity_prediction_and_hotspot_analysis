from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.schemas.report import (
    AIInfrastructureReportResponse,
    ReportProvenanceSchema,
    ReportSummarySchema,
)
from app.services.llm_provider import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMProvider,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMValidationError,
)
from app.services.llm_provider_router import LLMProviderRouter


class TestLLMProviderRouter(unittest.TestCase):
    """Test suite for LLMProviderRouter primary and fallback failover mechanics."""

    def setUp(self) -> None:
        self.mock_gemini = MagicMock(spec=LLMProvider)
        self.mock_claude = MagicMock(spec=LLMProvider)

        self.sample_report = AIInfrastructureReportResponse(
            generatedLabel="Temporary",
            signals=[],
            interventions=[],
            evidence=[],
            recommendations=[],
            priorities=[],
            summary=ReportSummarySchema(
                theme="Safety corridor",
                topIntervention="Roundabout",
                keySignal="Cluster density",
                nextStep="Review",
            ),
            provenance=ReportProvenanceSchema(
                student_a_model="RandomForestClassifier",
                student_b_hotspots="DBSCAN",
                student_c_gnn="RoadRiskGNN",
                grounded=True,
            ),
        )

    def test_gemini_primary_success_claude_not_called(self) -> None:
        """When Gemini succeeds, Claude must not be called."""
        self.mock_gemini.generate_structured_report.return_value = self.sample_report
        router = LLMProviderRouter(
            primary_provider=self.mock_gemini, fallback_provider=self.mock_claude
        )

        res = router.generate_structured_report("prompt")

        self.assertEqual(res, self.sample_report)
        self.mock_gemini.generate_structured_report.assert_called_once()
        self.mock_claude.generate_structured_report.assert_not_called()

    def test_gemini_rate_limits_fails_over_to_claude(self) -> None:
        """When Gemini hits HTTP 429 rate limit, router must fail over to Claude."""
        self.mock_gemini.generate_structured_report.side_effect = LLMRateLimitError(
            "Rate limit"
        )
        self.mock_claude.generate_structured_report.return_value = self.sample_report

        router = LLMProviderRouter(
            primary_provider=self.mock_gemini, fallback_provider=self.mock_claude
        )
        res = router.generate_structured_report("prompt")

        self.assertEqual(res, self.sample_report)
        self.mock_gemini.generate_structured_report.assert_called_once()
        self.mock_claude.generate_structured_report.assert_called_once()

    def test_gemini_timeout_fails_over_to_claude(self) -> None:
        """When Gemini times out, router must fail over to Claude."""
        self.mock_gemini.generate_structured_report.side_effect = LLMTimeoutError(
            "Timed out"
        )
        self.mock_claude.generate_structured_report.return_value = self.sample_report

        router = LLMProviderRouter(
            primary_provider=self.mock_gemini, fallback_provider=self.mock_claude
        )
        res = router.generate_structured_report("prompt")

        self.assertEqual(res, self.sample_report)
        self.mock_gemini.generate_structured_report.assert_called_once()
        self.mock_claude.generate_structured_report.assert_called_once()

    def test_gemini_auth_error_fails_over_to_claude(self) -> None:
        """When Gemini auth fails (401/403), router must fail over to Claude."""
        self.mock_gemini.generate_structured_report.side_effect = LLMAuthenticationError(
            "Auth failed"
        )
        self.mock_claude.generate_structured_report.return_value = self.sample_report

        router = LLMProviderRouter(
            primary_provider=self.mock_gemini, fallback_provider=self.mock_claude
        )
        res = router.generate_structured_report("prompt")

        self.assertEqual(res, self.sample_report)
        self.mock_gemini.generate_structured_report.assert_called_once()
        self.mock_claude.generate_structured_report.assert_called_once()

    def test_gemini_config_missing_fails_over_to_claude(self) -> None:
        """When Gemini key is missing, router must fail over to Claude."""
        self.mock_gemini.generate_structured_report.side_effect = LLMConfigurationError(
            "No Gemini key"
        )
        self.mock_claude.generate_structured_report.return_value = self.sample_report

        router = LLMProviderRouter(
            primary_provider=self.mock_gemini, fallback_provider=self.mock_claude
        )
        res = router.generate_structured_report("prompt")

        self.assertEqual(res, self.sample_report)
        self.mock_gemini.generate_structured_report.assert_called_once()
        self.mock_claude.generate_structured_report.assert_called_once()

    def test_gemini_validation_error_does_not_fail_over(self) -> None:
        """When Gemini produces invalid schema, router must NOT fail over (contract issue)."""
        self.mock_gemini.generate_structured_report.side_effect = LLMValidationError(
            "Schema invalid"
        )

        router = LLMProviderRouter(
            primary_provider=self.mock_gemini, fallback_provider=self.mock_claude
        )

        with self.assertRaises(LLMValidationError):
            router.generate_structured_report("prompt")

        self.mock_gemini.generate_structured_report.assert_called_once()
        self.mock_claude.generate_structured_report.assert_not_called()

    def test_both_providers_fail_raises_fallback_error(self) -> None:
        """When both Gemini and Claude fail, router raises the fallback error."""
        self.mock_gemini.generate_structured_report.side_effect = LLMTimeoutError(
            "Gemini timeout"
        )
        self.mock_claude.generate_structured_report.side_effect = LLMProviderError(
            "Claude 500 error"
        )

        router = LLMProviderRouter(
            primary_provider=self.mock_gemini, fallback_provider=self.mock_claude
        )

        with self.assertRaises(LLMProviderError):
            router.generate_structured_report("prompt")

        self.mock_gemini.generate_structured_report.assert_called_once()
        self.mock_claude.generate_structured_report.assert_called_once()

    def test_claude_primary_success_gemini_not_called(self) -> None:
        """When Claude is primary and succeeds, Gemini must not be called."""
        self.mock_claude.generate_structured_report.return_value = self.sample_report
        router = LLMProviderRouter(
            primary_provider=self.mock_claude, fallback_provider=self.mock_gemini
        )

        res = router.generate_structured_report("prompt")

        self.assertEqual(res, self.sample_report)
        self.mock_claude.generate_structured_report.assert_called_once()
        self.mock_gemini.generate_structured_report.assert_not_called()

    def test_no_infinite_retry_bounds(self) -> None:
        """Exactly 1 primary call and 1 fallback call are made on failure."""
        self.mock_gemini.generate_structured_report.side_effect = LLMProviderError("Primary 500")
        self.mock_claude.generate_structured_report.side_effect = LLMProviderError("Fallback 500")

        router = LLMProviderRouter(
            primary_provider=self.mock_gemini, fallback_provider=self.mock_claude
        )

        with self.assertRaises(LLMProviderError):
            router.generate_structured_report("prompt")

        self.assertEqual(self.mock_gemini.generate_structured_report.call_count, 1)
        self.assertEqual(self.mock_claude.generate_structured_report.call_count, 1)


if __name__ == "__main__":
    unittest.main()
