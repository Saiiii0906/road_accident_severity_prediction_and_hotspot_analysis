"""
Student B - Hotspot Analysis Integration & Query Test Suite.

Verifies:
1. HotspotDataManager startup loading and validation.
2. Invariant: Fatal_Count + Serious_Count + Slight_Count == Total_Accidents.
3. Bounding-box and center/radius spatial queries.
4. Severity filtering (fatal / serious / slight).
5. Deterministic sorting and pagination limits.
6. Graceful handling of empty areas and invalid queries.
7. Date filter rejection per specification.
8. API endpoints under /hotspots/analyze and /api/hotspots/analyze.
"""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.schemas.common import Coordinates, Severity
from app.schemas.hotspot import HotspotQueryRequest
from app.services.hotspot_service import HotspotDataManager, HotspotService


class TestHotspotIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = HotspotDataManager()
        cls.manager.load()
        cls.service = HotspotService(cls.manager)

    def test_01_hotspot_data_loaded_and_verified(self):
        """Verify HotspotDataManager successfully loaded the 3,705 real clusters."""
        self.assertTrue(self.manager.is_loaded)
        self.assertEqual(self.manager.total_clusters, 3705)

        df = self.manager._df
        self.assertEqual(len(df), 3705)
        self.assertFalse(df.isnull().any().any(), "No NaNs allowed in hotspot summary")

        # Verify severity invariant
        sev_sum = df["Fatal_Count"] + df["Serious_Count"] + df["Slight_Count"]
        self.assertTrue((sev_sum == df["Total_Accidents"]).all())

    def test_02_missing_artifact_raises_error(self):
        """Verify loading a non-existent artifact fails explicitly with FileNotFoundError."""
        temp_manager = HotspotDataManager()
        with self.assertRaises(FileNotFoundError):
            temp_manager.load(custom_path=Path("/tmp/non_existent_hotspots.csv"))

    def test_03_bounding_box_query_greater_london(self):
        """Verify bounding box query around Greater London returns Cluster 0 with 484,266 accidents."""
        req = HotspotQueryRequest(
            min_lat=51.2,
            max_lat=51.8,
            min_lon=-0.6,
            max_lon=0.4,
            limit=10,
        )
        res = self.service.analyze(req)
        self.assertGreater(len(res.clusters), 0)
        top_cluster = res.clusters[0]

        # Top cluster in London must be Cluster 0
        self.assertEqual(top_cluster.cluster_id, "cluster-0")
        self.assertEqual(top_cluster.accident_count, 484266)
        self.assertEqual(top_cluster.radius_meters, 500.0)
        self.assertEqual(top_cluster.severity_breakdown.fatal, 3522)
        self.assertEqual(top_cluster.severity_breakdown.serious, 55283)
        self.assertEqual(top_cluster.severity_breakdown.slight, 425461)
        self.assertAlmostEqual(top_cluster.center.latitude, 51.51517, places=3)
        self.assertAlmostEqual(top_cluster.center.longitude, -0.16323, places=3)

    def test_04_center_radius_query_birmingham(self):
        """Verify center/radius query around Birmingham (lat 52.519, lon -1.954) returns Cluster 633."""
        req = HotspotQueryRequest(
            center=Coordinates(latitude=52.51914, longitude=-1.95465),
            radius_km=15.0,
            limit=5,
        )
        res = self.service.analyze(req)
        self.assertGreater(len(res.clusters), 0)
        top_cluster = res.clusters[0]
        self.assertEqual(top_cluster.cluster_id, "cluster-633")
        self.assertEqual(top_cluster.accident_count, 83307)
        self.assertEqual(top_cluster.severity_breakdown.fatal, 765)

    def test_05_min_severity_filtering(self):
        """Verify min_severity filtering filters by real severity counts."""
        # Query with min_severity=fatal
        req_fatal = HotspotQueryRequest(
            min_lat=50.0,
            max_lat=60.0,
            min_lon=-7.0,
            max_lon=2.0,
            min_severity=Severity.FATAL,
            limit=50,
        )
        res_fatal = self.service.analyze(req_fatal)
        for c in res_fatal.clusters:
            self.assertGreaterEqual(c.severity_breakdown.fatal, 1)

    def test_06_deterministic_sorting_and_limit(self):
        """Verify clusters are strictly sorted descending by Total_Accidents."""
        req = HotspotQueryRequest(
            min_lat=49.0,
            max_lat=61.0,
            min_lon=-8.0,
            max_lon=3.0,
            limit=20,
        )
        res = self.service.analyze(req)
        self.assertEqual(len(res.clusters), 20)
        counts = [c.accident_count for c in res.clusters]
        self.assertEqual(counts, sorted(counts, reverse=True))

    def test_07_empty_area_query_handled_gracefully(self):
        """Verify searching an uninhabited sea coordinate returns empty results without error."""
        req = HotspotQueryRequest(
            center=Coordinates(latitude=50.0, longitude=-7.0),  # Off coast of Cornwall
            radius_km=1.0,
            limit=10,
        )
        res = self.service.analyze(req)
        self.assertEqual(len(res.clusters), 0)
        self.assertEqual(res.total_accidents_considered, 0)
        self.assertEqual(res.total_hotspots_in_area, 0)

    def test_08_date_filter_rejection(self):
        """Verify providing date_from or date_to is rejected with validation error."""
        from datetime import date
        with self.assertRaises(ValueError):
            HotspotQueryRequest(
                min_lat=51.0,
                max_lat=52.0,
                min_lon=-1.0,
                max_lon=0.0,
                date_from=date(2020, 1, 1),
            )

    def test_09_fastapi_endpoints_dual_mount(self):
        """Verify POST /hotspots/analyze and POST /api/hotspots/analyze via FastAPI TestClient."""
        payload = {
            "center": {"latitude": 53.49606, "longitude": -2.24795},  # Greater Manchester
            "radius_km": 10.0,
            "limit": 5,
        }
        with TestClient(app) as client:
            # Test /hotspots/analyze
            res1 = client.post("/hotspots/analyze", json=payload)
            self.assertEqual(res1.status_code, 200)
            data1 = res1.json()
            self.assertIn("clusters", data1)
            self.assertEqual(data1["clusters"][0]["cluster_id"], "cluster-140")
            self.assertEqual(data1["clusters"][0]["accident_count"], 62855)

            # Test /api/hotspots/analyze
            res2 = client.post("/api/hotspots/analyze", json=payload)
            self.assertEqual(res2.status_code, 200)
            data2 = res2.json()
            self.assertEqual(data2["clusters"][0]["cluster_id"], "cluster-140")


if __name__ == "__main__":
    unittest.main()
