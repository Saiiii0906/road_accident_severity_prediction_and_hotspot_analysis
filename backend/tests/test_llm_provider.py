import json
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx

from app.schemas.report import AIInfrastructureReportResponse, PriorityLevel
from app.services.llm_provider import (
    GeminiProvider,
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMProvider,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMValidationError,
    _gemini_compatible_schema,
)


class TestGeminiProvider(unittest.TestCase):
    """Test suite for GeminiProvider with mocked HTTP boundary."""

    def setUp(self) -> None:
        self.sample_report_dict = {
            "generatedLabel": "Generated 30 Aug 2026, 01:50 UTC",
            "signals": [
                {
                    "id": "sig-1",
                    "label": "Elevated Junction Risk",
                    "value": "18.4% Severe Ratio",
                    "note": "A1 Corridor",
                    "level": "critical",
                }
            ],
            "interventions": [
                {
                    "id": "int-1",
                    "intervention": "Roundabout Geometry Upgrade",
                    "signal": "High angle collisions",
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
                    "intervention": "Roundabout Geometry Upgrade",
                    "priority": "critical",
                    "impact": "high",
                    "effort": "high",
                }
            ],
            "summary": {
                "theme": "Corridor safety overhaul",
                "topIntervention": "Roundabout Geometry Upgrade at Junction 4",
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

    def test_gemini_compatible_schema_inlining(self) -> None:
        """Schema converter must remove $defs, $ref, and anyOf, and preserve property fields."""
        schema = _gemini_compatible_schema(AIInfrastructureReportResponse)
        schema_json = json.dumps(schema)

        self.assertNotIn("$defs", schema_json)
        self.assertNotIn("$ref", schema_json)
        self.assertNotIn("anyOf", schema_json)

        # Check top-level required and properties
        self.assertEqual(schema.get("type"), "object")
        self.assertIn("summary", schema.get("properties", {}))
        self.assertIn("theme", schema["properties"]["summary"]["properties"])

        # Check recommendations preserve field named 'title'
        rec_properties = schema["properties"]["recommendations"]["items"]["properties"]
        self.assertIn("title", rec_properties)
        self.assertIn("why", rec_properties)

        # Check nullable provenance is correctly transformed
        self.assertTrue(schema["properties"]["provenance"].get("nullable"))

    def test_provider_interface(self) -> None:
        """GeminiProvider must implement the abstract LLMProvider interface."""
        provider = GeminiProvider(api_key="test-key")
        self.assertIsInstance(provider, LLMProvider)

    def test_missing_api_key_raises_configuration_error(self) -> None:
        """Provider must raise LLMConfigurationError if api_key is missing."""
        provider = GeminiProvider(api_key="")
        with self.assertRaises(LLMConfigurationError):
            provider.generate_structured_report("test prompt")

    def test_successful_structured_report_generation(self) -> None:
        """Provider must parse Gemini candidate response into validated Pydantic model."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": json.dumps(self.sample_report_dict)}]
                    }
                }
            ]
        }

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = mock_response

        provider = GeminiProvider(api_key="valid-key", http_client=mock_client)
        result = provider.generate_structured_report("Generate report prompt")

        self.assertIsInstance(result, AIInfrastructureReportResponse)
        self.assertEqual(result.signals[0].level, PriorityLevel.CRITICAL)
        self.assertEqual(result.summary.topIntervention, "Roundabout Geometry Upgrade at Junction 4")

    def test_authentication_error_handling(self) -> None:
        """HTTP 401/403 must raise LLMAuthenticationError immediately without retrying."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 403
        mock_response.text = "API_KEY_INVALID with key secret_key_12345"

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = mock_response

        provider = GeminiProvider(
            api_key="secret_key_12345",
            http_client=mock_client,
            max_retries=2,
            retry_base_delay=0.0,
        )
        with self.assertRaises(LLMAuthenticationError) as ctx:
            provider.generate_structured_report("prompt")

        self.assertNotIn("secret_key_12345", str(ctx.exception))
        self.assertEqual(mock_client.post.call_count, 1)

    def test_bad_request_400_no_retry(self) -> None:
        """HTTP 400 client error must raise LLMProviderError immediately without retrying."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 400
        mock_response.text = "Invalid JSON schema in request"

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = mock_response

        provider = GeminiProvider(
            api_key="test-key",
            http_client=mock_client,
            max_retries=2,
            retry_base_delay=0.0,
        )
        with self.assertRaises(LLMProviderError):
            provider.generate_structured_report("prompt")

        self.assertEqual(mock_client.post.call_count, 1)

    def test_transient_503_retry_and_succeed(self) -> None:
        """HTTP 503 on first attempt followed by HTTP 200 on retry must succeed."""
        fail_response = MagicMock(spec=httpx.Response)
        fail_response.status_code = 503
        fail_response.text = "Service temporarily unavailable"

        success_response = MagicMock(spec=httpx.Response)
        success_response.status_code = 200
        success_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": json.dumps(self.sample_report_dict)}]
                    }
                }
            ]
        }

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.side_effect = [fail_response, success_response]

        provider = GeminiProvider(
            api_key="test-key",
            http_client=mock_client,
            max_retries=2,
            retry_base_delay=0.0,
        )
        result = provider.generate_structured_report("prompt")

        self.assertIsInstance(result, AIInfrastructureReportResponse)
        self.assertEqual(mock_client.post.call_count, 2)

    def test_transient_503_retry_exhaustion_raises_provider_error(self) -> None:
        """HTTP 503 on all attempts must exhaust retries and raise LLMProviderError."""
        fail_response = MagicMock(spec=httpx.Response)
        fail_response.status_code = 503
        fail_response.text = "High demand spike"

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = fail_response

        provider = GeminiProvider(
            api_key="test-key",
            http_client=mock_client,
            max_retries=2,
            retry_base_delay=0.0,
        )
        with self.assertRaises(LLMProviderError):
            provider.generate_structured_report("prompt")

        self.assertEqual(mock_client.post.call_count, 3)

    def test_rate_limit_429_retry_exhaustion_raises_rate_limit_error(self) -> None:
        """HTTP 429 on all attempts must raise LLMRateLimitError upon retry exhaustion."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 429
        mock_response.text = "Quota exceeded"

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = mock_response

        provider = GeminiProvider(
            api_key="test-key",
            http_client=mock_client,
            max_retries=2,
            retry_base_delay=0.0,
        )
        with self.assertRaises(LLMRateLimitError):
            provider.generate_structured_report("prompt")

        self.assertEqual(mock_client.post.call_count, 3)

    def test_timeout_retry_and_succeed(self) -> None:
        """Timeout on first attempt followed by success on retry must succeed."""
        success_response = MagicMock(spec=httpx.Response)
        success_response.status_code = 200
        success_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": json.dumps(self.sample_report_dict)}]
                    }
                }
            ]
        }

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.side_effect = [
            httpx.TimeoutException("Read timed out"),
            success_response,
        ]

        provider = GeminiProvider(
            api_key="test-key",
            http_client=mock_client,
            max_retries=2,
            retry_base_delay=0.0,
        )
        result = provider.generate_structured_report("prompt")

        self.assertIsInstance(result, AIInfrastructureReportResponse)
        self.assertEqual(mock_client.post.call_count, 2)

    def test_timeout_retry_exhaustion_raises_timeout_error(self) -> None:
        """httpx.TimeoutException on all attempts must raise LLMTimeoutError."""
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.side_effect = httpx.TimeoutException("Read timed out")

        provider = GeminiProvider(
            api_key="test-key",
            timeout_seconds=1.0,
            http_client=mock_client,
            max_retries=2,
            retry_base_delay=0.0,
        )
        with self.assertRaises(LLMTimeoutError):
            provider.generate_structured_report("prompt")

        self.assertEqual(mock_client.post.call_count, 3)

    def test_network_error_retry_exhaustion_raises_provider_error(self) -> None:
        """httpx.RequestError on all attempts must raise LLMProviderError."""
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.side_effect = httpx.RequestError("Connection reset by peer")

        provider = GeminiProvider(
            api_key="test-key",
            http_client=mock_client,
            max_retries=2,
            retry_base_delay=0.0,
        )
        with self.assertRaises(LLMProviderError):
            provider.generate_structured_report("prompt")

        self.assertEqual(mock_client.post.call_count, 3)

    def test_malformed_json_response_raises_validation_error(self) -> None:
        """Non-JSON text candidate output must raise LLMValidationError."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "I am not JSON"}]}}]
        }

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = mock_response

        provider = GeminiProvider(api_key="test-key", http_client=mock_client)
        with self.assertRaises(LLMValidationError):
            provider.generate_structured_report("prompt")

    def test_schema_mismatch_raises_validation_error(self) -> None:
        """JSON output missing required schema fields must raise LLMValidationError."""
        invalid_dict = {"incomplete": "data"}
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": json.dumps(invalid_dict)}]}}]
        }

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = mock_response

        provider = GeminiProvider(api_key="test-key", http_client=mock_client)
        with self.assertRaises(LLMValidationError):
            provider.generate_structured_report("prompt")


if __name__ == "__main__":
    unittest.main()
