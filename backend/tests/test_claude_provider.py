import json
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from app.schemas.report import AIInfrastructureReportResponse, PriorityLevel
from app.services.claude_provider import ClaudeProvider
from app.services.llm_provider import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMProvider,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMValidationError,
)


class TestClaudeProvider(unittest.TestCase):
    """Test suite for ClaudeProvider with mocked HTTP boundary."""

    def setUp(self) -> None:
        self.sample_report_dict = {
            "generatedLabel": "Generated 30 Aug 2026, 06:05 UTC",
            "signals": [
                {
                    "id": "sig-1",
                    "label": "Corridor Collision Risk",
                    "value": "24.1% Severe Ratio",
                    "note": "A1 Corridor",
                    "level": "critical",
                }
            ],
            "interventions": [
                {
                    "id": "int-1",
                    "intervention": "Roundabout Conversion",
                    "signal": "High angle impact rate",
                    "location": "Road #1 Junction 4",
                    "level": "critical",
                    "rationale": "GNN predicted risk 0.1565 indicates severe collision exposure.",
                }
            ],
            "evidence": [
                {
                    "id": "ev-1",
                    "signal": "DBSCAN Cluster Density",
                    "value": "1,240 collisions",
                    "strength": 94,
                    "relation": "Corroborates junction vulnerability",
                    "level": "critical",
                }
            ],
            "recommendations": [
                {
                    "id": "rec-1",
                    "title": "Upgrade Surface Texture",
                    "why": "Wet surface conditions exacerbate braking distances.",
                    "objective": "Reduce wet weather skidding by 40%",
                    "level": "high",
                    "supportingSignals": ["sig-1"],
                }
            ],
            "priorities": [
                {
                    "id": "p-1",
                    "intervention": "Roundabout Conversion",
                    "priority": "critical",
                    "impact": "high",
                    "effort": "high",
                }
            ],
            "summary": {
                "theme": "Corridor safety overhaul",
                "topIntervention": "Roundabout Conversion at Junction 4",
                "keySignal": "Topological GNN Risk > 0.15",
                "nextStep": "Commission detailed engineering feasibility study",
            },
            "provenance": {
                "student_a_model": "RandomForest_138_features",
                "student_b_hotspots": "DBSCAN_3705_clusters",
                "student_c_gnn": "GNN_13921_segments",
                "grounded": True,
            },
        }

    def test_provider_interface(self) -> None:
        """ClaudeProvider must implement the abstract LLMProvider interface."""
        provider = ClaudeProvider(api_key="test-key")
        self.assertIsInstance(provider, LLMProvider)

    def test_missing_api_key_raises_configuration_error(self) -> None:
        """Provider must raise LLMConfigurationError if api_key is missing."""
        provider = ClaudeProvider(api_key="")
        with self.assertRaises(LLMConfigurationError):
            provider.generate_structured_report("test prompt")

    def test_successful_tool_use_structured_response(self) -> None:
        """Provider must parse Claude tool_use block into validated Pydantic model."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [
                {
                    "type": "tool_use",
                    "name": "generate_structured_report",
                    "input": self.sample_report_dict,
                }
            ]
        }

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = mock_response

        provider = ClaudeProvider(api_key="valid-key", http_client=mock_client)
        result = provider.generate_structured_report("Generate report prompt")

        self.assertIsInstance(result, AIInfrastructureReportResponse)
        self.assertEqual(result.signals[0].level, PriorityLevel.CRITICAL)
        self.assertEqual(result.summary.topIntervention, "Roundabout Conversion at Junction 4")

    def test_authentication_error_handling(self) -> None:
        """HTTP 401/403 must raise LLMAuthenticationError and redact secret."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 401
        mock_response.text = "invalid x-api-key: sk-ant-secret-key-12345"

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = mock_response

        provider = ClaudeProvider(api_key="sk-ant-secret-key-12345", http_client=mock_client)
        with self.assertRaises(LLMAuthenticationError) as ctx:
            provider.generate_structured_report("prompt")

        self.assertNotIn("sk-ant-secret-key-12345", str(ctx.exception))

    def test_rate_limit_error_handling(self) -> None:
        """HTTP 429 must raise LLMRateLimitError."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = mock_response

        provider = ClaudeProvider(api_key="test-key", http_client=mock_client)
        with self.assertRaises(LLMRateLimitError):
            provider.generate_structured_report("prompt")

    def test_timeout_error_handling(self) -> None:
        """httpx.TimeoutException must raise LLMTimeoutError."""
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.side_effect = httpx.TimeoutException("Read timed out")

        provider = ClaudeProvider(api_key="test-key", timeout_seconds=1.0, http_client=mock_client)
        with self.assertRaises(LLMTimeoutError):
            provider.generate_structured_report("prompt")

    def test_server_error_handling(self) -> None:
        """HTTP 500 must raise LLMProviderError."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = mock_response

        provider = ClaudeProvider(api_key="test-key", http_client=mock_client)
        with self.assertRaises(LLMProviderError):
            provider.generate_structured_report("prompt")

    def test_malformed_json_raises_validation_error(self) -> None:
        """Missing or malformed tool input must raise LLMValidationError."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "Unstructured text here"}]
        }

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = mock_response

        provider = ClaudeProvider(api_key="test-key", http_client=mock_client)
        with self.assertRaises(LLMValidationError):
            provider.generate_structured_report("prompt")

    def test_schema_mismatch_raises_validation_error(self) -> None:
        """Tool input missing required schema fields must raise LLMValidationError."""
        invalid_dict = {"incomplete": "payload"}
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [
                {
                    "type": "tool_use",
                    "name": "generate_structured_report",
                    "input": invalid_dict,
                }
            ]
        }

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = mock_response

        provider = ClaudeProvider(api_key="test-key", http_client=mock_client)
        with self.assertRaises(LLMValidationError):
            provider.generate_structured_report("prompt")


if __name__ == "__main__":
    unittest.main()
