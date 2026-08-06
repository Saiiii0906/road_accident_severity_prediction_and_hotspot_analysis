import logging

from app.schemas.hotspot import HotspotAnalysisResponse, HotspotQueryRequest
from app.services.base_service import BaseMockService

logger = logging.getLogger(__name__)

_MOCK_FILE = "hotspot.json"


class HotspotService(BaseMockService):
    """Provides accident hotspot cluster analysis.

    Mock implementation: returns clusters loaded from
    mock_data/hotspot.json, truncated to `request.limit`. A real
    ML-backed implementation should replace this class while keeping
    `analyze` with the same signature.
    """

    def analyze(self, request: HotspotQueryRequest) -> HotspotAnalysisResponse:
        """Analyze accidents matching the query and return hotspot clusters.

        Args:
            request: Validated hotspot query. Only `request.limit` affects
                the mock response; the area/date/severity filters are
                unused since the mock has no underlying dataset to filter.

        Returns:
            A HotspotAnalysisResponse with at most `request.limit`
            clusters.

        Raises:
            HTTPException: 500 if the mock fixture is missing, unreadable,
                or fails schema validation.
        """
        logger.debug("Serving mock hotspot analysis (limit=%d)", request.limit)
        template = self._load_and_parse(_MOCK_FILE, HotspotAnalysisResponse)
        return self._apply_limit(template, request.limit)

    @staticmethod
    def _apply_limit(
        response: HotspotAnalysisResponse, limit: int
    ) -> HotspotAnalysisResponse:
        """Return a copy of `response` with at most `limit` clusters.

        `total_accidents_considered` is left untouched: it represents the
        count of accidents matched before clustering/truncation, which
        `limit` does not change.
        """
        if len(response.clusters) <= limit:
            return response
        return response.model_copy(update={"clusters": response.clusters[:limit]})