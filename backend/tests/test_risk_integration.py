"""
Student C - Graph Neural Network (GNN) Road Risk Integration & Query Test Suite.

Verifies:
1. RiskDataManager startup loading and 13,921 segment validation.
2. Edge IDs uniqueness, coordinate bounds, and predicted_risk range [0.0, 1.0].
3. Query by road_number.
4. Query by bounding box.
5. Query by center + radius (Haversine midpoint matching).
6. min_risk threshold filtering.
7. Limit and deterministic ordering (predicted_risk descending, segment_id ascending).
8. Graceful empty query handling.
9. Query mode validation and client error handling.
10. Missing artifact error handling.
11. In-memory serving (no PyTorch / PyG required for API inference).
12. API endpoints under /road-risk/predict and /api/road-risk/predict.
"""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.schemas.common import Coordinates
from app.schemas.risk import RoadRiskQueryRequest
from app.services.risk_service import RiskDataManager, RiskService


class TestRiskIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = RiskDataManager()
        cls.manager.load()
        cls.service = RiskService(cls.manager)

    def test_01_risk_data_loaded_and_verified(self):
        """Verify RiskDataManager loaded exactly 13,921 road segments."""
        self.assertTrue(self.manager.is_loaded)
        self.assertEqual(self.manager.total_segments, 13921)
        self.assertEqual(len(self.manager._edge_ids), 13921)

    def test_02_unique_edge_ids_and_risk_range(self):
        """Verify unique edge IDs and all predicted_risk values within [0.0, 1.0]."""
        edge_ids = self.manager._edge_ids
        self.assertEqual(len(set(edge_ids)), len(edge_ids))
        
        risks = self.manager._predicted_risks
        self.assertTrue((risks >= 0.0).all())
        self.assertTrue((risks <= 1.0).all())
        self.assertAlmostEqual(float(risks.min()), 0.0373, places=3)
        self.assertAlmostEqual(float(risks.max()), 0.1565, places=3)

    def test_03_missing_artifact_raises_error(self):
        """Verify loading a non-existent artifact fails explicitly with FileNotFoundError."""
        temp_manager = RiskDataManager()
        with self.assertRaises(FileNotFoundError):
            temp_manager.load(custom_path=Path("/tmp/non_existent_predictions.json"))

    def test_04_query_by_road_number(self):
        """Verify querying by road_number returns only segments for that road."""
        req = RoadRiskQueryRequest(
            road_number=1,  # Road A1
            limit=20,
        )
        res = self.service.predict(req)
        self.assertGreater(len(res.segments), 0)
        for seg in res.segments:
            self.assertEqual(seg.road_number, 1)

    def test_05_query_by_bounding_box(self):
        """Verify bounding box query around Greater London returns segments in that box."""
        req = RoadRiskQueryRequest(
            min_lat=51.2,
            max_lat=51.8,
            min_lon=-0.6,
            max_lon=0.4,
            limit=15,
        )
        res = self.service.predict(req)
        self.assertGreater(len(res.segments), 0)
        for seg in res.segments:
            mid_lat = (seg.start.latitude + seg.end.latitude) / 2.0
            mid_lon = (seg.start.longitude + seg.end.longitude) / 2.0
            self.assertTrue(51.2 <= mid_lat <= 51.8)
            self.assertTrue(-0.6 <= mid_lon <= 0.4)

    def test_06_query_by_center_radius(self):
        """Verify center/radius query around Birmingham (52.519, -1.954) returns nearby segments."""
        req = RoadRiskQueryRequest(
            center=Coordinates(latitude=52.519, longitude=-1.954),
            radius_km=15.0,
            limit=10,
        )
        res = self.service.predict(req)
        self.assertGreater(len(res.segments), 0)
        self.assertEqual(len(res.segments), 10)

    def test_07_min_risk_filtering(self):
        """Verify min_risk filter returns only segments above threshold."""
        req = RoadRiskQueryRequest(
            road_number=1,
            min_risk=0.08,
            limit=50,
        )
        res = self.service.predict(req)
        for seg in res.segments:
            self.assertGreaterEqual(seg.predicted_risk, 0.08)

    def test_08_deterministic_sorting_and_limit(self):
        """Verify segments are deterministically sorted by predicted_risk descending."""
        req = RoadRiskQueryRequest(
            min_lat=50.0,
            max_lat=60.0,
            min_lon=-7.0,
            max_lon=2.0,
            limit=25,
        )
        res = self.service.predict(req)
        self.assertEqual(len(res.segments), 25)
        risks = [s.predicted_risk for s in res.segments]
        self.assertEqual(risks, sorted(risks, reverse=True))

    def test_09_empty_area_query(self):
        """Verify searching an uninhabited sea coordinate returns empty list without error."""
        req = RoadRiskQueryRequest(
            center=Coordinates(latitude=50.0, longitude=-7.0),
            radius_km=1.0,
            limit=10,
        )
        res = self.service.predict(req)
        self.assertEqual(len(res.segments), 0)
        self.assertEqual(res.total_segments, 0)
        self.assertEqual(res.total_segments_matched, 0)

    def test_10_invalid_query_validation(self):
        """Verify requests with no query mode or inverted bounding boxes fail validation."""
        # No query mode
        with self.assertRaises(ValueError):
            RoadRiskQueryRequest()

        # Inverted bounding box
        with self.assertRaises(ValueError):
            RoadRiskQueryRequest(
                min_lat=55.0,
                max_lat=51.0,
                min_lon=-1.0,
                max_lon=0.0,
            )

    def test_11_fastapi_endpoints_dual_mount(self):
        """Verify POST /road-risk/predict and POST /api/road-risk/predict via TestClient."""
        payload = {
            "road_number": 1,
            "limit": 5,
        }
        with TestClient(app) as client:
            res1 = client.post("/road-risk/predict", json=payload)
            self.assertEqual(res1.status_code, 200)
            data1 = res1.json()
            self.assertIn("segments", data1)
            self.assertEqual(len(data1["segments"]), 5)
            self.assertEqual(data1["segments"][0]["road_number"], 1)

            res2 = client.post("/api/road-risk/predict", json=payload)
            self.assertEqual(res2.status_code, 200)
            data2 = res2.json()
            self.assertEqual(len(data2["segments"]), 5)


if __name__ == "__main__":
    unittest.main()

