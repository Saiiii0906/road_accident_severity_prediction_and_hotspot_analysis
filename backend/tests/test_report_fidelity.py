from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.schemas.report import (
    AIInfrastructureReportRequest,
    AIInfrastructureReportResponse,
    EvidenceItemSchema,
    MatrixImpactEffort,
    PriorityInterventionSchema,
    PriorityLevel,
    PriorityMatrixRowSchema,
    RecommendationSchema,
    ReportProvenanceSchema,
    ReportSummarySchema,
    RiskSignalSchema,
)
from app.services.report_grounding_service import ReportGroundingService
from app.services.report_prompt_service import ReportPromptService


class TestReportGroundingFidelity(unittest.TestCase):
    """Test suite for deterministic grounding payload fidelity and fact consistency."""

    def setUp(self) -> None:
        self.grounding_service = ReportGroundingService()
        self.request = AIInfrastructureReportRequest(
            region="all",
            period="last_12_months",
            threshold="moderate",
            focus="overall_safety",
        )
        self.payload = self.grounding_service.build_grounding_payload(self.request)

    def test_student_b_grounding_facts(self) -> None:
        """Student B evidence in payload must match actual empirical hotspot summary."""
        self.assertEqual(self.payload.student_b.total_clusters_in_scope, 3705)
        self.assertEqual(self.payload.student_b.total_accidents_in_scope, 916614)
        self.assertGreaterEqual(len(self.payload.student_b.top_hotspots), 1)

        # First cluster must be cluster-0 with 484266 accidents
        top_cluster = self.payload.student_b.top_hotspots[0]
        self.assertEqual(top_cluster.cluster_id, "cluster-0")
        self.assertEqual(top_cluster.accident_count, 484266)
        self.assertEqual(top_cluster.fatal_count, 3522)
        self.assertEqual(top_cluster.serious_count, 55283)
        self.assertAlmostEqual(top_cluster.center.latitude, 51.51517, places=3)
        self.assertAlmostEqual(top_cluster.center.longitude, -0.1632317, places=3)

    def test_student_c_grounding_facts(self) -> None:
        """Student C evidence in payload must match actual GNN road predictions."""
        self.assertEqual(self.payload.student_c.total_segments_in_scope, 13921)
        self.assertAlmostEqual(self.payload.student_c.highest_predicted_risk, 0.1565, places=3)
        self.assertGreaterEqual(len(self.payload.student_c.top_segments), 1)

        # First segment must be Segment 1205 on Road 12 with risk 0.1565
        top_segment = self.payload.student_c.top_segments[0]
        self.assertEqual(top_segment.segment_id, 1205)
        self.assertEqual(top_segment.road_number, 12)
        self.assertAlmostEqual(top_segment.predicted_risk, 0.1565, places=4)
        self.assertEqual(top_segment.risk_category, "Critical")

    def test_prompt_contains_exact_grounding_records(self) -> None:
        """Compiled prompt must contain verified numerical records rather than vague summaries."""
        prompt = ReportPromptService.build_prompt(self.payload)

        # Hotspot facts must be present
        self.assertIn("cluster-0", prompt)
        self.assertIn("484266", prompt)
        self.assertIn("3522", prompt)
        self.assertIn("55283", prompt)

        # GNN segment facts must be present
        self.assertIn("1205", prompt)
        self.assertIn("0.1565", prompt)
        self.assertIn("Critical", prompt)

    def test_response_schema_requires_all_actionable_arrays(self) -> None:
        """Schema must require all 6 top-level actionable sections."""
        json_schema = AIInfrastructureReportResponse.model_json_schema()
        required_fields = set(json_schema.get("required", []))
        expected_fields = {"signals", "interventions", "evidence", "recommendations", "priorities", "summary"}
        self.assertTrue(expected_fields.issubset(required_fields))

    def test_grounding_fidelity_cross_verification(self) -> None:
        """Demonstrates verification that reported cluster IDs and road segments exist in grounding."""
        # Simulated response grounded in real payload
        sample_response = AIInfrastructureReportResponse(
            generatedLabel="Generated 30 Aug 2026, 03:12 UTC",
            signals=[
                RiskSignalSchema(
                    id="sig-01",
                    label="Peak Structural GNN Road Risk",
                    value="0.1565 GNN risk index",
                    note="Observed on Road 12 Segment 1205.",
                    level=PriorityLevel.CRITICAL,
                ),
                RiskSignalSchema(
                    id="sig-02",
                    label="Highest Incident Cluster Concentration",
                    value="484,266 accidents",
                    note="Cluster-0 center (51.51517, -0.1632317) recorded 3,522 fatal casualties.",
                    level=PriorityLevel.CRITICAL,
                ),
            ],
            interventions=[
                PriorityInterventionSchema(
                    id="int-01",
                    intervention="Corridor Speed Management",
                    signal="Peak GNN risk 0.1565",
                    location="Road 12 Segment 1205",
                    level=PriorityLevel.CRITICAL,
                    rationale="High topological vulnerability on road 12.",
                )
            ],
            evidence=[
                EvidenceItemSchema(
                    id="ev-01",
                    signal="Cluster Concentration",
                    value="484,266 accidents",
                    strength=98,
                    relation="Dense urban collision nexus",
                    level=PriorityLevel.CRITICAL,
                )
            ],
            recommendations=[
                RecommendationSchema(
                    id="rec-01",
                    title="Junction Redesign",
                    why="High incident concentration at Cluster-0",
                    objective="Mitigate turning collisions",
                    level=PriorityLevel.HIGH,
                    supportingSignals=["sig-02"],
                )
            ],
            priorities=[
                PriorityMatrixRowSchema(
                    id="p-01",
                    intervention="Corridor Speed Management",
                    priority=PriorityLevel.CRITICAL,
                    impact=MatrixImpactEffort.HIGH,
                    effort=MatrixImpactEffort.MODERATE,
                )
            ],
            summary=ReportSummarySchema(
                theme="Spatial and topological safety overhaul",
                topIntervention="Corridor speed management on Road 12",
                keySignal="GNN risk 0.1565 on Segment 1205",
                nextStep="Commission engineering review",
            ),
            provenance=ReportProvenanceSchema(
                student_a_model="RandomForestClassifier",
                student_b_hotspots="DBSCAN",
                student_c_gnn="RoadRiskGNN",
                grounded=True,
            ),
        )

        # Verify cluster ID existence in grounding payload
        valid_cluster_ids = {h.cluster_id.lower() for h in self.payload.student_b.top_hotspots}
        valid_segment_ids = {s.segment_id for s in self.payload.student_c.top_segments}
        valid_road_numbers = {s.road_number for s in self.payload.student_c.top_segments}

        # Check references in signals
        for sig in sample_response.signals:
            if "cluster-0" in sig.note.lower():
                self.assertIn("cluster-0", valid_cluster_ids)
            if "segment 1205" in sig.note.lower():
                self.assertIn(1205, valid_segment_ids)
            if "road 12" in sig.note.lower():
                self.assertIn(12, valid_road_numbers)


if __name__ == "__main__":
    unittest.main()

