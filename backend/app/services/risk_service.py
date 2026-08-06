import logging

from app.schemas.risk import RiskAssessmentRequest, RiskAssessmentResponse
from app.services.base_service import BaseMockService

logger = logging.getLogger(__name__)

_MOCK_FILE = "risk.json"


class RiskService(BaseMockService):
    """Provides location-based accident risk assessments.

    Mock implementation: loads a fixed risk score and contributing-factor
    breakdown from mock_data/risk.json, then overlays the requested
    location and assessment time onto the response. A real ML-backed
    implementation should replace this class while keeping `assess` with
    the same signature.
    """

    def assess(self, request: RiskAssessmentRequest) -> RiskAssessmentResponse:
        """Assess accident risk for a location and condition set.

        Args:
            request: Validated location and road/weather conditions.
                `request.location` and `request.assessed_at` are echoed
                into the response; the remaining condition fields are
                unused by the mock.

        Returns:
            A RiskAssessmentResponse with mock scoring data, but the
            actual requested location and assessment time.

        Raises:
            HTTPException: 500 if the mock fixture is missing, unreadable,
                or fails schema validation.
        """
        logger.debug(
            "Serving mock risk assessment for location (%s, %s)",
            request.location.latitude,
            request.location.longitude,
        )
        template = self._load_and_parse(_MOCK_FILE, RiskAssessmentResponse)
        return self._apply_request_context(template, request)

    @staticmethod
    def _apply_request_context(
        response: RiskAssessmentResponse, request: RiskAssessmentRequest
    ) -> RiskAssessmentResponse:
        """Overlay request-derived fields onto a fixture-loaded response.

        Only fields that share a name and type with the request are
        overridden: `location` and `assessed_at`. Everything else is
        prediction output and stays as loaded from the fixture.
        """
        return response.model_copy(
            update={
                "location": request.location,
                "assessed_at": request.assessed_at,
            }
        )