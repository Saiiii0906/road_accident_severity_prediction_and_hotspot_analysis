import json
import unittest

from app.schemas.report import AIInfrastructureReportRequest
from app.services.hotspot_service import HotspotDataManager
from app.services.report_grounding_service import (
    GroundingPayload,
    ReportGroundingService,
)
from app.services.risk_service import RiskDataManager
from app.services.severity_service import SeverityModelManager


class TestReportGroundingService(unittest.TestCase):
    """Test suite for ReportGroundingService evidence aggregation."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.severity_manager = SeverityModelManager.get_instance()
        cls.hotspot_manager = HotspotDataManager()
        cls.hotspot_manager.load()
        cls.risk_manager = RiskDataManager()
        cls.risk_manager.load()

        cls.grounding_service = ReportGroundingService(
            severity_manager=cls.severity_manager,
            hotspot_manager=cls.hotspot_manager,
            risk_manager=cls.risk_manager,
        )

    def test_service_initialization(self) -> None:
        """Grounding service should instantiate and hold references to data managers."""
        self.assertIsNotNone(self.grounding_service)
        self.assertTrue(self.hotspot_manager.is_loaded)
        self.assertTrue(self.risk_manager.is_loaded)

    def test_build_grounding_payload_basic(self) -> None:
        """Payload should contain verified Student A, B, and C sections."""
        req = AIInfrastructureReportRequest(region="all", threshold="moderate")
        payload = self.grounding_service.build_grounding_payload(req)

        self.assertIsInstance(payload, GroundingPayload)
        self.assertEqual(payload.student_a.feature_count, 138)
        self.assertGreater(payload.student_b.total_clusters_in_scope, 0)
        self.assertGreater(payload.student_c.total_segments_in_scope, 0)

    def test_student_b_evidence_bounded_and_real(self) -> None:
        """Student B evidence must be bounded (<=12) and contain real cluster numbers."""
        req = AIInfrastructureReportRequest(region="all")
        payload = self.grounding_service.build_grounding_payload(req)

        self.assertLessEqual(len(payload.student_b.top_hotspots), 12)
        self.assertGreater(len(payload.student_b.top_hotspots), 0)

        # Check real values
        first_cluster = payload.student_b.top_hotspots[0]
        self.assertTrue(first_cluster.cluster_id.startswith("cluster-"))
        self.assertGreater(first_cluster.accident_count, 0)
        self.assertGreaterEqual(first_cluster.center.latitude, 49.0)
        self.assertLessEqual(first_cluster.center.latitude, 61.0)

    def test_student_c_evidence_bounded_and_real(self) -> None:
        """Student C evidence must be bounded (<=12) and contain real GNN segments."""
        req = AIInfrastructureReportRequest(region="all")
        payload = self.grounding_service.build_grounding_payload(req)

        self.assertLessEqual(len(payload.student_c.top_segments), 12)
        self.assertGreater(len(payload.student_c.top_segments), 0)

        # Check real values
        first_segment = payload.student_c.top_segments[0]
        self.assertGreaterEqual(first_segment.predicted_risk, 0.0)
        self.assertLessEqual(first_segment.predicted_risk, 1.0)
        self.assertIn(first_segment.risk_category, ["Critical", "High", "Moderate", "Low"])

    def test_deterministic_ordering(self) -> None:
        """Repeated identical requests must produce exactly equivalent evidence."""
        req = AIInfrastructureReportRequest(region="central")
        payload1 = self.grounding_service.build_grounding_payload(req)
        payload2 = self.grounding_service.build_grounding_payload(req)

        self.assertEqual(
            [h.cluster_id for h in payload1.student_b.top_hotspots],
            [h.cluster_id for h in payload2.student_b.top_hotspots],
        )
        self.assertEqual(
            [s.segment_id for s in payload1.student_c.top_segments],
            [s.segment_id for s in payload2.student_c.top_segments],
        )

    def test_limitations_stated_honestly(self) -> None:
        """Artifact limitations regarding date filtering must be stated clearly."""
        req = AIInfrastructureReportRequest(period="last_30_days")
        payload = self.grounding_service.build_grounding_payload(req)

        self.assertIn("precomputed", payload.student_b.limitations.lower())
        self.assertIn("temporal", payload.student_a.limitations.lower())
        self.assertIn("traffic", payload.student_c.limitations.lower())

    def test_json_serialization(self) -> None:
        """Payload must serialize cleanly to standard JSON for LLM consumption."""
        req = AIInfrastructureReportRequest(region="north")
        payload = self.grounding_service.build_grounding_payload(req)

        json_str = payload.model_dump_json()
        parsed = json.loads(json_str)

        self.assertIn("student_a", parsed)
        self.assertIn("student_b", parsed)
        self.assertIn("student_c", parsed)
        self.assertIn("grounding_rules", parsed)


if __name__ == "__main__":
    unittest.main()

