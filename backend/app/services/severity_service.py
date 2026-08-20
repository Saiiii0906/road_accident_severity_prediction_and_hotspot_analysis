import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.schemas.severity import (
    BatchSeverityPredictionRequest,
    BatchSeverityPredictionResponse,
    SeverityPredictionRequest,
    SeverityPredictionResponse,
    SeverityClassProbability,
)
from app.services.base_service import BaseMockService

logger = logging.getLogger(__name__)

_MOCK_FILE = "severity.json"

_SEVERITY_CLASSES = ["low", "moderate", "high", "fatal"]


def _generate_mock_prediction(request: SeverityPredictionRequest) -> SeverityPredictionResponse:
    """Generate a deterministic mock prediction based on request characteristics.
    
    This is a placeholder for the real ML model. The prediction logic here is
    intentionally simple and deterministic so that tests are reproducible.
    """
    # Simple heuristic: more vehicles + higher speed limit = higher severity
    severity_score = (
        request.number_of_vehicles * 0.1
        + request.speed_limit * 0.02
        + (1 if request.is_junction else 0) * 0.3
        + (0.5 if request.road_surface_conditions.value in ("wet", "snow", "ice", "flood") else 0)
        + (0.3 if request.light_conditions.value in ("dark_unlit", "dusk") else 0)
    )
    
    # Normalize to 0-1 range
    severity_score = min(1.0, max(0.0, severity_score / 2.0))
    
    # Map score to severity class
    if severity_score < 0.25:
        predicted_class = "low"
        probabilities = [0.7, 0.2, 0.08, 0.02]
    elif severity_score < 0.5:
        predicted_class = "moderate"
        probabilities = [0.15, 0.6, 0.2, 0.05]
    elif severity_score < 0.75:
        predicted_class = "high"
        probabilities = [0.05, 0.2, 0.6, 0.15]
    else:
        predicted_class = "fatal"
        probabilities = [0.02, 0.08, 0.2, 0.7]
    
    class_probabilities = [
        SeverityClassProbability(severity=cls, probability=prob)
        for cls, prob in zip(_SEVERITY_CLASSES, probabilities)
    ]
    
    return SeverityPredictionResponse(
        predicted_severity=predicted_class,
        confidence=probabilities[_SEVERITY_CLASSES.index(predicted_class)],
        class_probabilities=class_probabilities,
        model_version="mock-v1.0.0",
        predicted_at=datetime.now(timezone.utc),
    )


class SeverityService(BaseMockService):
    def predict(
        self, request: SeverityPredictionRequest
    ) -> SeverityPredictionResponse:
        """Predict the severity of a single accident.
        
        Args:
            request: Validated accident conditions.
            
        Returns:
            A SeverityPredictionResponse with the predicted severity.
            
        Raises:
            HTTPException: 500 if the mock fixture is missing, unreadable,
                or fails schema validation.
        """
        logger.info("Received severity prediction request")
        logger.debug("Serving mock single severity prediction")
        
        try:
            return _generate_mock_prediction(request)
        except Exception as exc:
            logger.error("Failed to generate severity prediction: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate severity prediction",
            ) from exc

    def predict_batch(
        self, request: BatchSeverityPredictionRequest
    ) -> BatchSeverityPredictionResponse:
        """Predict severity for a batch of accidents.
        
        Returns one prediction per submitted accident, in the same order.
        
        Args:
            request: Batch of accidents to predict for.
            
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
        
        try:
            predictions = [
                _generate_mock_prediction(accident)
                for accident in request.accidents
            ]
            return BatchSeverityPredictionResponse(predictions=predictions)
        except Exception as exc:
            logger.error("Failed to generate batch severity predictions: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate batch severity predictions",
            ) from exc

    def _load_prediction_template(self) -> SeverityPredictionResponse:
        """Load and validate the mock severity prediction fixture.
        
        Returns:
            A default SeverityPredictionResponse if the fixture cannot be loaded.
            
        Raises:
            HTTPException: 500 if the fixture cannot be read or validated.
        """
        try:
            return self._load_and_parse(_MOCK_FILE, SeverityPredictionResponse)
        except Exception as exc:
            logger.warning("Failed to load mock fixture %s: %s", _MOCK_FILE, exc)
            # Return a default template instead of failing
            return SeverityPredictionResponse(
                predicted_severity="moderate",
                confidence=0.5,
                class_probabilities=[
                    SeverityClassProbability(severity=cls, probability=0.25)
                    for cls in _SEVERITY_CLASSES
                ],
                model_version="mock-v1.0.0",
                predicted_at=datetime.now(timezone.utc),
            )