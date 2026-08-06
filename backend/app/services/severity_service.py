import logging

from app.schemas.severity import (
    BatchSeverityPredictionRequest,
    BatchSeverityPredictionResponse,
    SeverityPredictionRequest,
    SeverityPredictionResponse,
)
from app.services.base_service import BaseMockService

logger = logging.getLogger(__name__)

_MOCK_FILE = "severity.json"


class SeverityService(BaseMockService):
    def predict(
        self, request: SeverityPredictionRequest
    ) -> SeverityPredictionResponse:
        """Predict the severity of a single accident.

        Args:
            request: Validated accident conditions. Not used by the mock;
                accepted here only so the signature matches the real,
                model-backed implementation that will replace this one.

        Returns:
            A SeverityPredictionResponse loaded from the mock fixture.

        Raises:
            HTTPException: 500 if the mock fixture is missing, unreadable,
                or fails schema validation.
        """
        logger.info("Received severity prediction request")
        logger.debug("Serving mock single severity prediction")
        return self._load_prediction_template()

    def predict_batch(
        self, request: BatchSeverityPredictionRequest
    ) -> BatchSeverityPredictionResponse:
        """Predict severity for a batch of accidents.

        Returns one prediction per submitted accident, in the same order.
        The mock fixture is loaded once and copied per item; a real
        implementation would instead run inference once per accident.

        Args:
            request: Batch of accidents to predict for. Only its length is
                used by the mock, to determine how many predictions to
                return.

        Returns:
            A BatchSeverityPredictionResponse with one prediction per
            submitted accident.

        Raises:
            HTTPException: 500 if the mock fixture is missing, unreadable,
                or fails schema validation.
        """
        template = self._load_prediction_template()
        logger.debug(
            "Serving mock batch severity prediction for %d accidents",
            len(request.accidents),
        )
        predictions = [
            template.model_copy(deep=True) for _ in request.accidents
        ]
        return BatchSeverityPredictionResponse(predictions=predictions)

    def _load_prediction_template(self) -> SeverityPredictionResponse:
        """Load and validate the mock severity prediction fixture.

        Raises:
            HTTPException: 500 if the fixture cannot be read or validated.
        """
        return self._load_and_parse(_MOCK_FILE, SeverityPredictionResponse)