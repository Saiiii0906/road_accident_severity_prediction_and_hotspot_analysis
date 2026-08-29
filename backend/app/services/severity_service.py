import logging
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
from fastapi import HTTPException, status

from app.config import settings
from app.schemas.common import Severity
from app.schemas.severity import (
    BatchSeverityPredictionRequest,
    BatchSeverityPredictionResponse,
    SeverityClassProbability,
    SeverityPredictionRequest,
    SeverityPredictionResponse,
)
from app.services.student_a_transformer import StudentATransformer

logger = logging.getLogger(__name__)


class SeverityModelManager:
    """Singleton manager for Student A's Random Forest Severity Model.

    Loads the 8.37 GB model artifact, label encoder, and feature list once at
    application startup, caching them in memory for high-throughput inference.
    """

    _instance: Optional["SeverityModelManager"] = None

    def __init__(self) -> None:
        self.model = None
        self.encoder = None
        self.features: list[str] = []
        self.transformer: Optional[StudentATransformer] = None
        self._is_loaded = False

    @classmethod
    def get_instance(cls) -> "SeverityModelManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    def load(
        self,
        model_path: Optional[Path] = None,
        encoder_path: Optional[Path] = None,
        features_path: Optional[Path] = None,
    ) -> None:
        """Load model, encoder, and feature artifacts into memory."""
        m_path = model_path or settings.STUDENT_A_MODEL_PATH
        e_path = encoder_path or settings.STUDENT_A_ENCODER_PATH
        f_path = features_path or settings.STUDENT_A_FEATURES_PATH

        logger.info("Initializing Student A Severity model artifacts...")

        if not m_path.exists():
            raise FileNotFoundError(f"Student A model not found at {m_path}")
        if not e_path.exists():
            raise FileNotFoundError(f"Student A encoder not found at {e_path}")
        if not f_path.exists():
            raise FileNotFoundError(f"Student A features list not found at {f_path}")

        # 1. Load feature names
        logger.info("Loading feature list from %s", f_path)
        with open(f_path, "rb") as f:
            self.features = pickle.load(f)
        logger.info("Loaded %d feature definitions.", len(self.features))

        # 2. Load LabelEncoder
        logger.info("Loading label encoder from %s", e_path)
        with open(e_path, "rb") as f:
            self.encoder = pickle.load(f)
        logger.info("Loaded label encoder with classes: %s", getattr(self.encoder, "classes_", None))

        # 3. Load RandomForestClassifier
        logger.info("Loading trained RandomForestClassifier from %s (may take a few seconds)...", m_path)
        with open(m_path, "rb") as f:
            self.model = pickle.load(f)
        logger.info("Student A model loaded successfully: %s", type(self.model).__name__)

        # 4. Initialize transformer
        self.transformer = StudentATransformer(feature_names=self.features)
        self._is_loaded = True
        logger.info("Student A Severity Model Manager is ready for inference.")

    def predict_batch(
        self, requests: list[SeverityPredictionRequest]
    ) -> list[SeverityPredictionResponse]:
        """Perform batch severity prediction on a list of accident requests."""
        if not self._is_loaded or self.model is None or self.transformer is None or self.encoder is None:
            # Attempt lazy load if not yet initialized
            try:
                self.load()
            except Exception as exc:
                logger.error("Failed to load Student A model: %s", exc)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Student A severity model is not loaded: {exc}",
                ) from exc

        # Transform inputs into 138-feature matrix
        df_features = self.transformer.transform(requests)

        # Run inference
        preds_encoded = self.model.predict(df_features)
        probas = self.model.predict_proba(df_features)
        preds_labels = self.encoder.inverse_transform(preds_encoded)

        responses: list[SeverityPredictionResponse] = []
        now = datetime.now(timezone.utc)

        # Map encoder classes to lowercase Severity enum
        # encoder.classes_: ['Fatal', 'Serious', 'Slight']
        encoder_classes = [str(c).lower() for c in self.encoder.classes_]

        for i, (pred_label, proba_row) in enumerate(zip(preds_labels, probas)):
            pred_sev_str = str(pred_label).lower()
            try:
                pred_severity = Severity(pred_sev_str)
            except ValueError:
                pred_severity = Severity.SLIGHT

            confidence = round(float(np.max(proba_row)), 4)

            # Build class probability distribution
            class_probs: list[SeverityClassProbability] = []
            probs_dict: dict[str, float] = {}

            # Standard Stats19 mappings:
            # col 0: Fatal, col 1: Serious, col 2: Slight
            for cls_name, prob_val in zip(encoder_classes, proba_row):
                try:
                    sev_enum = Severity(cls_name)
                except ValueError:
                    sev_enum = Severity.SLIGHT
                p_val = round(float(prob_val), 4)
                class_probs.append(SeverityClassProbability(severity=sev_enum, probability=p_val))
                probs_dict[cls_name] = p_val

            responses.append(
                SeverityPredictionResponse(
                    predicted_severity=pred_severity,
                    confidence=confidence,
                    class_probabilities=class_probs,
                    probabilities=probs_dict,
                    model_version="student-a-rf-v1.0",
                    predicted_at=now,
                )
            )

        return responses


class SeverityService:
    """Service layer exposing severity prediction endpoints backed by Student A's ML model."""

    def __init__(self, manager: Optional[SeverityModelManager] = None) -> None:
        self.manager = manager or SeverityModelManager.get_instance()

    def predict(
        self, request: SeverityPredictionRequest
    ) -> SeverityPredictionResponse:
        """Predict severity for a single accident."""
        logger.info("Received single severity prediction request")
        predictions = self.manager.predict_batch([request])
        return predictions[0]

    def predict_batch(
        self, request: BatchSeverityPredictionRequest
    ) -> BatchSeverityPredictionResponse:
        """Predict severity for a batch of accidents."""
        logger.info("Received batch severity prediction request for %d accidents", len(request.accidents))
        predictions = self.manager.predict_batch(request.accidents)
        return BatchSeverityPredictionResponse(predictions=predictions)