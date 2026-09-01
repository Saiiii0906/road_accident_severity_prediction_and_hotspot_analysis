"""
LLM Provider Abstraction Layer.

Defines the core interface and Gemini 2.5/Flash implementation for
generating validated structured JSON reports from grounded prompts.
"""

from abc import ABC, abstractmethod
from copy import deepcopy
import json
import logging
from typing import Any, Optional, Type, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.config import settings
from app.schemas.report import AIInfrastructureReportResponse

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# ==============================================================================
# Typed Provider Exceptions
# ==============================================================================


class LLMBaseError(Exception):
    """Base exception for all LLM provider failures."""


class LLMConfigurationError(LLMBaseError):
    """Raised when API key or model configuration is missing or invalid."""


class LLMAuthenticationError(LLMBaseError):
    """Raised when API key is rejected by the provider."""


class LLMTimeoutError(LLMBaseError):
    """Raised when the LLM provider call times out."""


class LLMRateLimitError(LLMBaseError):
    """Raised when LLM quota or rate limits are exceeded."""


class LLMProviderError(LLMBaseError):
    """Raised when the LLM provider encounters an internal error or 5xx response."""


class LLMValidationError(LLMBaseError):
    """Raised when LLM output cannot be parsed or fails Pydantic schema validation."""


# ==============================================================================
# Abstract Provider Interface
# ==============================================================================


class LLMProvider(ABC):
    """Abstract interface for structured LLM report generation."""

    @abstractmethod
    def generate_structured_report(
        self,
        prompt: str,
        schema_cls: Type[T] = AIInfrastructureReportResponse,
    ) -> T:
        """Submit grounded prompt and return a validated Pydantic model instance."""


# ==============================================================================
# Google Gemini Schema Adapter & Provider Implementation
# ==============================================================================


def _gemini_compatible_schema(schema_cls: Type[BaseModel]) -> dict[str, Any]:
    """Convert Pydantic JSON schema to Gemini-compatible OpenAPI subset schema.

    Gemini OpenAPI subset rules:
    - No $defs or $ref: all references are inlined recursively.
    - No anyOf: optional/nullable fields (anyOf with null) become {..., 'nullable': True}.
    - Supported keys: 'type', 'format', 'description', 'nullable', 'enum', 'properties', 'required', 'items'.
    - Stripped schema metadata: 'title', 'default', 'minLength', 'maxLength', 'minimum', 'maximum', '$defs', '$ref', 'additionalProperties'.
    """
    raw_schema = schema_cls.model_json_schema()
    definitions = raw_schema.pop("$defs", {})

    def resolve(node: Any) -> Any:
        if isinstance(node, dict):
            # 1. Resolve $ref references
            if "$ref" in node:
                ref_name = node["$ref"].split("/")[-1]
                if ref_name in definitions:
                    resolved = deepcopy(definitions[ref_name])
                    return resolve(resolved)
                return {}

            # 2. Handle anyOf (e.g. nullable fields like anyOf: [Schema, {'type': 'null'}])
            if "anyOf" in node:
                variants = node["anyOf"]
                non_null_variants = [
                    v for v in variants if isinstance(v, dict) and v.get("type") != "null"
                ]
                is_nullable = any(
                    isinstance(v, dict) and v.get("type") == "null" for v in variants
                )
                if non_null_variants:
                    base_variant = resolve(non_null_variants[0])
                    if isinstance(base_variant, dict):
                        if is_nullable:
                            base_variant["nullable"] = True
                        if "description" in node and "description" not in base_variant:
                            base_variant["description"] = node["description"]
                        return base_variant

            # 3. Clean and map supported keys
            clean: dict[str, Any] = {}
            for key, val in node.items():
                if key in {
                    "$defs",
                    "$ref",
                    "title",
                    "default",
                    "minLength",
                    "maxLength",
                    "minimum",
                    "maximum",
                    "pattern",
                    "additionalProperties",
                }:
                    continue
                if key == "properties" and isinstance(val, dict):
                    clean["properties"] = {
                        p_key: resolve(p_val) for p_key, p_val in val.items()
                    }
                else:
                    clean[key] = resolve(val)

            return clean

        if isinstance(node, list):
            return [resolve(item) for item in node]

        return node

    return resolve(raw_schema)


import time

class GeminiProvider(LLMProvider):
    """Google Gemini implementation for structured JSON report generation."""

    DEFAULT_API_BASE: str = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        timeout_seconds: Optional[float] = None,
        http_client: Optional[httpx.Client] = None,
        max_retries: Optional[int] = None,
        retry_base_delay: Optional[float] = None,
        retry_max_delay: Optional[float] = None,
    ) -> None:
        self.api_key = settings.GEMINI_API_KEY if api_key is None else api_key
        self.model = settings.GEMINI_MODEL if model is None else model
        self.temperature = (
            settings.LLM_TEMPERATURE if temperature is None else temperature
        )
        self.timeout_seconds = (
            settings.LLM_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds
        )
        self.max_retries = (
            getattr(settings, "LLM_MAX_RETRIES", 2) if max_retries is None else max_retries
        )
        self.retry_base_delay = (
            getattr(settings, "LLM_RETRY_BASE_DELAY", 1.0)
            if retry_base_delay is None
            else retry_base_delay
        )
        self.retry_max_delay = (
            getattr(settings, "LLM_RETRY_MAX_DELAY", 4.0)
            if retry_max_delay is None
            else retry_max_delay
        )
        self._client = http_client

    def _sanitize_error(self, message: str) -> str:
        """Strip any accidental key leakage from error strings."""
        if self.api_key and self.api_key in message:
            return message.replace(self.api_key, "[REDACTED_API_KEY]")
        return message

    def generate_structured_report(
        self,
        prompt: str,
        schema_cls: Type[T] = AIInfrastructureReportResponse,
    ) -> T:
        """Generate structured JSON conforming to schema_cls via Gemini Developer API."""
        if not self.api_key or not self.api_key.strip():
            raise LLMConfigurationError(
                "GEMINI_API_KEY is not configured in the application environment."
            )

        # Convert Pydantic schema to Gemini-compatible OpenAPI subset
        gemini_schema = _gemini_compatible_schema(schema_cls)

        url = f"{self.DEFAULT_API_BASE}/{self.model}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }

        # Build payload with structured JSON configuration
        payload: dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": self.temperature,
                "response_mime_type": "application/json",
                "response_schema": gemini_schema,
            },
        }

        client = self._client or httpx.Client(timeout=self.timeout_seconds)
        should_close = self._client is None

        max_attempts = 1 + max(0, self.max_retries)
        last_response: Optional[httpx.Response] = None

        try:
            for attempt in range(max_attempts):
                try:
                    response = client.post(url, headers=headers, json=payload)
                except httpx.TimeoutException as exc:
                    if attempt < max_attempts - 1:
                        delay = min(
                            self.retry_base_delay * (2**attempt), self.retry_max_delay
                        )
                        logger.warning(
                            "Gemini API request timed out (attempt %d/%d). Retrying in %.1fs...",
                            attempt + 1,
                            max_attempts,
                            delay,
                        )
                        if delay > 0:
                            time.sleep(delay)
                        continue
                    logger.error("Gemini API call timed out after %.1fs", self.timeout_seconds)
                    raise LLMTimeoutError(
                        f"Gemini API request timed out after {self.timeout_seconds}s"
                    ) from exc
                except httpx.RequestError as exc:
                    sanitized = self._sanitize_error(str(exc))
                    if attempt < max_attempts - 1:
                        delay = min(
                            self.retry_base_delay * (2**attempt), self.retry_max_delay
                        )
                        logger.warning(
                            "Gemini network error: %s (attempt %d/%d). Retrying in %.1fs...",
                            sanitized,
                            attempt + 1,
                            max_attempts,
                            delay,
                        )
                        if delay > 0:
                            time.sleep(delay)
                        continue
                    logger.error("Gemini network error: %s", sanitized)
                    raise LLMProviderError(
                        f"Network error communicating with Gemini: {sanitized}"
                    ) from exc

                # If successful (HTTP 200), break and process candidates
                if response.status_code == 200:
                    last_response = response
                    break

                # Non-200 responses
                status_code = response.status_code
                error_text = self._sanitize_error(response.text)

                # Non-retryable errors
                if status_code in (401, 403) or (
                    status_code == 400 and "API_KEY_INVALID" in error_text
                ):
                    raise LLMAuthenticationError(
                        f"Gemini authentication failed (HTTP {status_code}). Please verify GEMINI_API_KEY."
                    )
                if status_code == 404:
                    raise LLMProviderError(
                        f"Gemini model '{self.model}' not found or unavailable (HTTP 404): {error_text}"
                    )
                if status_code == 400:
                    raise LLMProviderError(
                        f"Gemini API error (HTTP 400): {error_text}"
                    )

                # Transient errors: 429, 500, 502, 503, 504
                if status_code in (429, 500, 502, 503, 504):
                    if attempt < max_attempts - 1:
                        delay = min(
                            self.retry_base_delay * (2**attempt), self.retry_max_delay
                        )
                        logger.warning(
                            "Gemini returned transient HTTP %d (attempt %d/%d). Retrying in %.1fs...",
                            status_code,
                            attempt + 1,
                            max_attempts,
                            delay,
                        )
                        if delay > 0:
                            time.sleep(delay)
                        continue

                    # Retries exhausted for transient error
                    if status_code == 429:
                        raise LLMRateLimitError(
                            "Gemini API rate limit or quota exceeded (HTTP 429)."
                        )
                    if status_code >= 500:
                        raise LLMProviderError(
                            f"Gemini server error (HTTP {status_code}): {error_text}"
                        )
                    raise LLMProviderError(
                        f"Gemini API error (HTTP {status_code}): {error_text}"
                    )

                # Any other unexpected status code: do not retry
                raise LLMProviderError(
                    f"Gemini API error (HTTP {status_code}): {error_text}"
                )
        finally:
            if should_close:
                client.close()

        if last_response is None or last_response.status_code != 200:
            raise LLMProviderError("Gemini API call failed without a valid response.")

        # Parse candidates
        try:
            res_data = last_response.json()
            candidates = res_data.get("candidates", [])
            if not candidates:
                raise LLMValidationError("Gemini returned an empty response with no candidates.")

            content_parts = candidates[0].get("content", {}).get("parts", [])
            if not content_parts or "text" not in content_parts[0]:
                raise LLMValidationError("Gemini response missing text part.")

            raw_text = content_parts[0]["text"]
            parsed_json = json.loads(raw_text)
        except (json.JSONDecodeError, KeyError, IndexError) as exc:
            logger.error("Failed to parse Gemini JSON output: %s", exc)
            raise LLMValidationError(
                f"Gemini response could not be parsed as valid JSON: {exc}"
            ) from exc

        # Validate with Pydantic schema
        try:
            return schema_cls.model_validate(parsed_json)
        except ValidationError as val_exc:
            logger.error("Pydantic validation failed on Gemini output: %s", val_exc)
            raise LLMValidationError(
                f"Gemini output failed schema validation: {val_exc}"
            ) from val_exc
