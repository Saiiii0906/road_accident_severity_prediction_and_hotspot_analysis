import unittest

from app.schemas.report import AIInfrastructureReportRequest
from app.services.report_grounding_service import ReportGroundingService
from app.services.report_prompt_service import ReportPromptService


class TestReportPromptService(unittest.TestCase):
    """Test suite for deterministic grounded prompt construction."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.grounding_service = ReportGroundingService()
        req = AIInfrastructureReportRequest(
            region="central",
            period="last_12_months",
            threshold="high",
            focus="speed_reduction",
        )
        cls.payload = cls.grounding_service.build_grounding_payload(req)
        cls.prompt = ReportPromptService.build_prompt(cls.payload)

    def test_prompt_contains_grounding_rules(self) -> None:
        """Prompt must include anti-hallucination and evidence integrity rules."""
        self.assertIn("CRITICAL GROUNDING & INTEGRITY RULES", self.prompt)
        self.assertIn("NEVER invent, hallucinate, extrapolate", self.prompt)
        self.assertIn("DISTINGUISH observation from inference", self.prompt)

    def test_prompt_contains_all_student_sections(self) -> None:
        """Prompt must clearly identify Student A, B, and C capabilities."""
        self.assertIn("Student A", self.prompt)
        self.assertIn("Student B", self.prompt)
        self.assertIn("Student C", self.prompt)
        self.assertIn("Random Forest", self.prompt)
        self.assertIn("DBSCAN", self.prompt)
        self.assertIn("Graph Neural Network", self.prompt)

    def test_prompt_contains_actual_grounding_payload(self) -> None:
        """Prompt must inject the JSON serialized GroundingPayload."""
        self.assertIn("student_a", self.prompt)
        self.assertIn("student_b", self.prompt)
        self.assertIn("student_c", self.prompt)
        self.assertIn("central", self.prompt)
        self.assertIn("speed_reduction", self.prompt)

    def test_prompt_specifies_structured_output_fields(self) -> None:
        """Prompt must instruct the model on all 7 target JSON schema sections."""
        self.assertIn("signals", self.prompt)
        self.assertIn("interventions", self.prompt)
        self.assertIn("evidence", self.prompt)
        self.assertIn("recommendations", self.prompt)
        self.assertIn("priorities", self.prompt)
        self.assertIn("summary", self.prompt)
        self.assertIn("provenance", self.prompt)


if __name__ == "__main__":
    unittest.main()

