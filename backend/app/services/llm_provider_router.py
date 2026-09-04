"""
LLM Provider Router with Deterministic Fallback.

Coordinates primary and secondary LLM providers with safe, bounded failover.
"""

import logging
from typing import Optional, Type, TypeVar

from pydantic import BaseModel

from app.config import settings
from app.schemas.report import AIInfrastructureReportResponse
from app.services.claude_provider import ClaudeProvider
from app.services.llm_provider import (
    GeminiProvider,
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

FAILOVER_EXCEPTIONS = (
    LLMConfigurationError,
    LLMAuthenticationError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMProviderError,
)


class LLMProviderRouter(LLMProvider):
    """Multi-provider LLM router supporting primary execution with fallback."""

    def __init__(
        self,
        primary_provider: Optional[LLMProvider] = None,
        fallback_provider: Optional[LLMProvider] = None,
    ) -> None:
        if primary_provider is not None:
            self.primary = primary_provider
            self.fallback = fallback_provider or ClaudeProvider()
        else:
            primary_choice = (settings.LLM_PRIMARY_PROVIDER or "gemini").lower()
            if primary_choice == "claude":
                self.primary = ClaudeProvider()
                self.fallback = fallback_provider or GeminiProvider()
            else:
                self.primary = GeminiProvider()
                self.fallback = fallback_provider or ClaudeProvider()

    def generate_structured_report(
        self,
        prompt: str,
        schema_cls: Type[T] = AIInfrastructureReportResponse,
        system_instruction: Optional[str] = None,
    ) -> T:
        """Execute report generation with primary provider; fallback on recoverable errors."""
        primary_name = type(self.primary).__name__
        fallback_name = type(self.fallback).__name__

        primary_exc = None
        try:
            return self.primary.generate_structured_report(
                prompt, schema_cls=schema_cls, system_instruction=system_instruction
            )
        except LLMValidationError as val_exc:
            # Do NOT failover on validation errors: schema mismatch indicates contract/prompt issue
            logger.error("Primary provider %s generated invalid schema output. Aborting failover.", primary_name)
            raise val_exc
        except FAILOVER_EXCEPTIONS as exc:
            primary_exc = exc
            logger.warning(
                "Primary provider %s failed (%s: %s). Initiating single fallback attempt to %s.",
                primary_name,
                type(primary_exc).__name__,
                primary_exc,
                fallback_name,
            )

        # Fallback invocation (strictly 1 attempt, no loop)
        try:
            return self.fallback.generate_structured_report(
                prompt, schema_cls=schema_cls, system_instruction=system_instruction
            )
        except LLMConfigurationError:
            # If fallback provider is not configured, surface the actual primary failure
            logger.info(
                "Fallback provider %s is unconfigured. Propagating primary provider %s error.",
                fallback_name,
                primary_name,
            )
            if primary_exc is not None:
                raise primary_exc
            raise
        except Exception as fallback_exc:
            logger.error(
                "Fallback provider %s also failed (%s: %s).",
                fallback_name,
                type(fallback_exc).__name__,
                fallback_exc,
            )
            raise fallback_exc
