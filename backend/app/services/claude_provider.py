"""
Anthropic Claude LLM Provider Implementation.

Implements the LLMProvider abstraction using Anthropic Messages API
with native structured tool-calling for deterministic schema compliance.
"""

import json
import logging
from typing import Any, Optional, Type, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.config import settings
from app.schemas.report import AIInfrastructureReportResponse
from app.services.llm_provider import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMProvider,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMValidationError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class ClaudeProvider(LLMProvider):
    """Anthropic Claude provider for validated structured JSON report generation."""

    API_URL: str = "https://api.anthropic.com/v1/messages"
    ANTHROPIC_VERSION: str = "2023-06-01"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        timeout_seconds: Optional[float] = None,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        self.api_key = settings.CLAUDE_API_KEY if api_key is None else api_key
        self.model = settings.CLAUDE_MODEL if model is None else model
        self.temperature = (
            settings.LLM_TEMPERATURE if temperature is None else temperature
        )
        self.timeout_seconds = (
            settings.LLM_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds
        )
        self._client = http_client

    def _sanitize_error(self, message: str) -> str:
        """Strip sensitive Claude API keys from error messages."""
        if self.api_key and self.api_key in message:
            return message.replace(self.api_key, "[REDACTED_CLAUDE_KEY]")
        return message

    def generate_structured_report(
        self,
        prompt: str,
        schema_cls: Type[T] = AIInfrastructureReportResponse,
    ) -> T:
        """Generate structured report adhering to schema_cls via Anthropic Messages API."""
        if not self.api_key or not self.api_key.strip():
            raise LLMConfigurationError(
                "CLAUDE_API_KEY is not configured in the application environment."
            )

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.ANTHROPIC_VERSION,
            "content-type": "application/json",
        }

        # Structure report output using Anthropic tool calling schema
        tool_name = "generate_structured_report"
        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": 4096,
            "temperature": self.temperature,
            "tools": [
                {
                    "name": tool_name,
                    "description": "Output structured AI Infrastructure decision support report.",
                    "input_schema": schema_cls.model_json_schema(),
                }
            ],
            "tool_choice": {"type": "tool", "name": tool_name},
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        }

        client = self._client or httpx.Client(timeout=self.timeout_seconds)
        should_close = self._client is None

        try:
            response = client.post(self.API_URL, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            logger.error("Claude API call timed out after %.1fs", self.timeout_seconds)
            raise LLMTimeoutError(
                f"Claude API request timed out after {self.timeout_seconds}s"
            ) from exc
        except httpx.RequestError as exc:
            sanitized = self._sanitize_error(str(exc))
            logger.error("Claude network error: %s", sanitized)
            raise LLMProviderError(f"Network error communicating with Claude: {sanitized}") from exc
        finally:
            if should_close:
                client.close()

        # Handle HTTP status codes
        if response.status_code != 200:
            status_code = response.status_code
            error_text = self._sanitize_error(response.text)

            if status_code in (401, 403):
                raise LLMAuthenticationError(
                    f"Claude authentication failed (HTTP {status_code}). Please verify CLAUDE_API_KEY."
                )
            if status_code == 429:
                raise LLMRateLimitError(
                    "Claude API rate limit or quota exceeded (HTTP 429)."
                )
            if status_code >= 500:
                raise LLMProviderError(
                    f"Claude server error (HTTP {status_code}): {error_text}"
                )

            raise LLMProviderError(
                f"Claude API error (HTTP {status_code}): {error_text}"
            )

        # Parse response content
        try:
            res_data = response.json()
            content_blocks = res_data.get("content", [])
            parsed_data: Optional[dict[str, Any]] = None

            for block in content_blocks:
                if block.get("type") == "tool_use" and block.get("name") == tool_name:
                    parsed_data = block.get("input")
                    break
                elif block.get("type") == "text":
                    try:
                        parsed_data = json.loads(block.get("text", ""))
                    except Exception:
                        pass

            if parsed_data is None:
                raise LLMValidationError("Claude returned a response without valid structured output.")
        except Exception as exc:
            logger.error("Failed to extract Claude structured output: %s", exc)
            raise LLMValidationError(f"Claude output parsing failed: {exc}") from exc

        # Validate with Pydantic
        try:
            return schema_cls.model_validate(parsed_data)
        except ValidationError as val_exc:
            logger.error("Pydantic validation failed on Claude output: %s", val_exc)
            raise LLMValidationError(
                f"Claude output failed schema validation: {val_exc}"
            ) from val_exc
