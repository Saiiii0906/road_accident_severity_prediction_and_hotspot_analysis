import unittest
import sys
from pathlib import Path

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.schemas.common import Severity
from app.schemas.severity import (
    BatchSeverityPredictionRequest,
    SeverityPredictionRequest,
    SeverityPredictionResponse,
)
from app.services.severity_service import SeverityModelManager, SeverityService
from app.services.student_a_transformer import StudentATransformer


class TestStudentASeverityIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = SeverityModelManager.get_instance()
        cls.manager.load()
        cls.service = SeverityService(manager=cls.manager)

    def test_01_artifacts_loaded(self):
        self.assertTrue(self.manager.is_loaded)
        self.assertIsNotNone(self.manager.model)
        self.assertIsNotNone(self.manager.encoder)
        self.assertEqual(len(self.manager.features), 138)
        self.assertEqual(
            list(self.manager.encoder.classes_),
            ["Fatal", "Serious", "Slight"],
        )

    def test_02_transformer_output_shape_and_features(self):
        req = SeverityPredictionRequest(
            accident_date="2024-06-15",
            accident_time="17:30",
            day_of_week="Friday",
            speed_limit=30,
            number_of_vehicles=2,
            number_of_casualties=1,
            road_type="single_carriageway",
            road_surface="wet",
            weather="raining",
            light_conditions="daylight",
            urban_or_rural_area="urban",
        )
        df = self.manager.transformer.transform([req])
        self.assertEqual(df.shape, (1, 138))
        self.assertEqual(list(df.columns), self.manager.features)
        self.assertEqual(df.isna().sum().sum(), 0)

    def test_03_single_prediction_output(self):
        req = SeverityPredictionRequest(
            accident_date="2024-06-15",
            accident_time="17:30",
            day_of_week="Friday",
            speed_limit=30,
            number_of_vehicles=2,
            number_of_casualties=1,
            road_type="single_carriageway",
            road_surface="dry",
            weather="fine",
            light_conditions="daylight",
            urban_or_rural_area="urban",
        )
        res = self.service.predict(req)
        self.assertIsInstance(res, SeverityPredictionResponse)
        self.assertIn(res.predicted_severity, [Severity.SLIGHT, Severity.SERIOUS, Severity.FATAL])
        self.assertGreaterEqual(res.confidence, 0.0)
        self.assertLessEqual(res.confidence, 1.0)
        self.assertEqual(len(res.class_probabilities), 3)

        # Check probabilities sum to ~1.0
        prob_sum = sum(p.probability for p in res.class_probabilities)
        self.assertAlmostEqual(prob_sum, 1.0, places=2)

        # Check dictionary probabilities mapping
        self.assertIn("fatal", res.probabilities)
        self.assertIn("serious", res.probabilities)
        self.assertIn("slight", res.probabilities)

    def test_04_batch_prediction(self):
        req1 = SeverityPredictionRequest(
            accident_date="2024-01-10",
            accident_time="08:30",
            speed_limit=60,
            number_of_vehicles=3,
            number_of_casualties=2,
            road_surface="ice",
            weather="snowing",
        )
        req2 = SeverityPredictionRequest(
            accident_date="2024-07-20",
            accident_time="12:00",
            speed_limit=20,
            number_of_vehicles=1,
            number_of_casualties=0,
            road_surface="dry",
            weather="fine",
        )
        batch_req = BatchSeverityPredictionRequest(accidents=[req1, req2])
        batch_res = self.service.predict_batch(batch_req)
        self.assertEqual(len(batch_res.predictions), 2)
        for p in batch_res.predictions:
            self.assertIn(p.predicted_severity, [Severity.SLIGHT, Severity.SERIOUS, Severity.FATAL])


if __name__ == "__main__":
    unittest.main()

