"""
LLM Report Orchestration Service.

Coordinates deterministic evidence grounding, prompt engineering,
and multi-provider LLM routing (Gemini primary with Claude fallback)
to generate verified AI Infrastructure Reports.
"""

from datetime import datetime, timezone
import logging
from typing import Optional

from fastapi import HTTPException, status

from app.schemas.report import (
    AIInfrastructureReportRequest,
    AIInfrastructureReportResponse,
    ReportProvenanceSchema,
    ReportSummarySchema,
)
from app.services.llm_provider import (
    LLMAuthenticationError,
    LLMBaseError,
    LLMConfigurationError,
    LLMProvider,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMValidationError,
)
from app.services.llm_provider_router import LLMProviderRouter
from app.services.report_grounding_service import (
    GroundingPayload,
    ReportGroundingService,
)
from app.services.report_prompt_service import ReportPromptService

logger = logging.getLogger(__name__)


class LLMReportService:
    """Orchestrates AI decision support report generation across grounding, prompt, and LLM layers."""

    def __init__(
        self,
        grounding_service: Optional[ReportGroundingService] = None,
        prompt_service: type[ReportPromptService] = ReportPromptService,
        provider: Optional[LLMProvider] = None,
    ) -> None:
        self.grounding_service = grounding_service or ReportGroundingService()
        self.prompt_service = prompt_service
        self.provider = provider or LLMProviderRouter()

    def generate_report(
        self, request: AIInfrastructureReportRequest
    ) -> AIInfrastructureReportResponse:
        """Execute end-to-end grounded report generation."""
        logger.info(
            "Generating AI Infrastructure Report for region=%s, period=%s, threshold=%s, focus=%s",
            request.region,
            request.period,
            request.threshold,
            request.focus,
        )

        # 1. Deterministic Evidence Aggregation
        try:
            payload: GroundingPayload = self.grounding_service.build_grounding_payload(request)
        except Exception as exc:
            logger.error("Failed to build grounding evidence payload: %s", exc, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to aggregate model evidence for report generation.",
            ) from exc

        # 2. Check for Empty Grounding Context
        if (
            payload.student_b.total_clusters_in_scope == 0
            and payload.student_c.total_segments_in_scope == 0
        ):
            logger.info("Grounding payload returned 0 clusters and 0 segments. Returning empty report.")
            return AIInfrastructureReportResponse(
                generatedLabel=self._generate_label(),
                signals=[],
                interventions=[],
                evidence=[],
                recommendations=[],
                priorities=[],
                summary=ReportSummarySchema(
                    theme="No active collision hotspots or high-risk road corridors detected.",
                    topIntervention="Maintain standard routine network inspection.",
                    keySignal="Zero high-density clusters or elevated GNN risk segments in queried bounds.",
                    nextStep="Expand geographic search perimeter or lower risk threshold.",
                ),
                provenance=self._enforce_provenance(),
            )

        # 3. Construct Grounded Prompt
        prompt = self.prompt_service.build_prompt(payload)

        # 4. Invoke LLM Provider (via router)
        try:
            raw_report: AIInfrastructureReportResponse = self.provider.generate_structured_report(
                prompt=prompt,
                schema_cls=AIInfrastructureReportResponse,
            )
        except LLMConfigurationError as exc:
            logger.error("LLM configuration error: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI report generation service is not configured (missing API credentials).",
            ) from exc
        except LLMAuthenticationError as exc:
            logger.error("LLM authentication error: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI report provider authentication failed. Please verify API credentials.",
            ) from exc
        except LLMTimeoutError as exc:
            logger.error("LLM provider timeout: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="AI report generation timed out. Please try again.",
            ) from exc
        except LLMRateLimitError as exc:
            logger.error("LLM rate limit error: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI report service is currently rate limited. Please retry shortly.",
            ) from exc
        except LLMValidationError as exc:
            logger.error("LLM validation error: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI report provider returned an unreadable or malformed response.",
            ) from exc
        except LLMProviderError as exc:
            logger.error("LLM provider error: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Upstream AI report provider encountered an error.",
            ) from exc
        except Exception as exc:
            logger.error("Unexpected error during LLM report generation: %s", exc, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while generating the AI report.",
            ) from exc

        # 5. Enforce Application-Owned Fields (Timestamp & Provenance)
        report_dict = raw_report.model_dump()
        report_dict["generatedLabel"] = self._generate_label()
        report_dict["provenance"] = self._enforce_provenance().model_dump()

        try:
            return AIInfrastructureReportResponse.model_validate(report_dict)
        except Exception as exc:
            logger.error("Final report model validation failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Final report structure failed application validation.",
            ) from exc

    @staticmethod
    def _generate_label() -> str:
        """Application-owned UTC timestamp label."""
        return datetime.now(timezone.utc).strftime("Generated %d %b %Y, %H:%M UTC")

    @staticmethod
    def _enforce_provenance() -> ReportProvenanceSchema:
        """Application-owned grounding provenance guaranteeing model lineage."""
        return ReportProvenanceSchema(
            student_a_model="RandomForestClassifier",
            student_b_hotspots="DBSCAN",
            student_c_gnn="RoadRiskGNN",
            grounded=True,
        )
