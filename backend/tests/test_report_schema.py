import unittest
from pydantic import ValidationError

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


class TestReportSchemaValidation(unittest.TestCase):
    """Test strict Pydantic validation for AI Infrastructure Report schemas."""

    def setUp(self) -> None:
        self.valid_payload = {
            "generatedLabel": "Generated 30 Aug 2026, 01:40 UTC",
            "signals": [
                {
                    "id": "sig-1",
                    "label": "Elevated Junction Risk",
                    "value": "18.4% Severe Ratio",
                    "note": "Dominant on A1 corridor",
                    "level": "critical",
                }
            ],
            "interventions": [
                {
                    "id": "int-1",
                    "intervention": "Roundabout Conversion",
                    "signal": "High angle collisions",
                    "location": "Road #1 Junction 4",
                    "level": "critical",
                    "rationale": "GNN predicted risk 0.1565 indicates severe collision exposure.",
                }
            ],
            "evidence": [
                {
                    "id": "ev-1",
                    "signal": "DBSCAN Cluster Density",
                    "value": "1,240 collisions",
                    "strength": 94,
                    "relation": "High correlation with wet road conditions",
                    "level": "critical",
                }
            ],
            "recommendations": [
                {
                    "id": "rec-1",
                    "title": "Upgrade High-Friction Pavement",
                    "why": "Wet surface conditions exacerbate braking distances.",
                    "objective": "Reduce wet weather skidding by 40%",
                    "level": "high",
                    "supportingSignals": ["sig-1"],
                }
            ],
            "priorities": [
                {
                    "id": "p-1",
                    "intervention": "Roundabout Conversion",
                    "priority": "critical",
                    "impact": "high",
                    "effort": "high",
                }
            ],
            "summary": {
                "theme": "Corridor safety overhaul",
                "topIntervention": "Roundabout Conversion at Junction 4",
                "keySignal": "Topological GNN Risk > 0.15",
                "nextStep": "Commission detailed engineering feasibility study",
            },
            "provenance": {
                "student_a_model": "RandomForest_138_features",
                "student_b_hotspots": "DBSCAN_3705_clusters",
                "student_c_gnn": "GNN_13921_segments",
                "grounded": True,
            },
        }

    def test_valid_report_instantiation(self) -> None:
        """A complete and valid report payload must parse cleanly."""
        report = AIInfrastructureReportResponse.model_validate(self.valid_payload)
        self.assertEqual(len(report.signals), 1)
        self.assertEqual(report.signals[0].level, PriorityLevel.CRITICAL)
        self.assertEqual(report.evidence[0].strength, 94)
        self.assertEqual(report.priorities[0].impact, MatrixImpactEffort.HIGH)
        self.assertIsNotNone(report.provenance)
        self.assertTrue(report.provenance.grounded)

    def test_request_defaults(self) -> None:
        """AIInfrastructureReportRequest must provide safe defaults."""
        req = AIInfrastructureReportRequest()
        self.assertEqual(req.region, "all")
        self.assertEqual(req.period, "last_12_months")
        self.assertEqual(req.threshold, "moderate")
        self.assertEqual(req.focus, "overall_safety")

    def test_missing_summary_fails(self) -> None:
        """Missing required summary section must raise ValidationError."""
        invalid = dict(self.valid_payload)
        del invalid["summary"]
        with self.assertRaises(ValidationError):
            AIInfrastructureReportResponse.model_validate(invalid)

    def test_invalid_level_enum_fails(self) -> None:
        """Invalid level values not in PriorityLevel enum must fail."""
        invalid = dict(self.valid_payload)
        invalid["signals"] = [
            {
                "id": "sig-1",
                "label": "Bad Level",
                "value": "100",
                "note": "Note",
                "level": "extremely_dangerous",
            }
        ]
        with self.assertRaises(ValidationError):
            AIInfrastructureReportResponse.model_validate(invalid)

    def test_evidence_strength_out_of_bounds_fails(self) -> None:
        """Evidence strength outside [0, 100] must fail validation."""
        invalid = dict(self.valid_payload)
        invalid["evidence"] = [
            {
                "id": "ev-1",
                "signal": "Test Signal",
                "value": "10",
                "strength": 150,
                "relation": "None",
                "level": "low",
            }
        ]
        with self.assertRaises(ValidationError):
            AIInfrastructureReportResponse.model_validate(invalid)

    def test_malformed_priority_matrix_fails(self) -> None:
        """Invalid impact/effort strings must fail validation."""
        invalid = dict(self.valid_payload)
        invalid["priorities"] = [
            {
                "id": "p-1",
                "intervention": "Test",
                "priority": "low",
                "impact": "huge",
                "effort": "low",
            }
        ]
        with self.assertRaises(ValidationError):
            AIInfrastructureReportResponse.model_validate(invalid)


if __name__ == "__main__":
    unittest.main()

