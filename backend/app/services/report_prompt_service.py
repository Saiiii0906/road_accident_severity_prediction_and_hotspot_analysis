"""
Report Prompt Service.

Constructs grounded, anti-hallucination prompts for evidence-based
road safety decision support from structured GroundingPayload objects.
"""

import json
from app.services.report_grounding_service import GroundingPayload


class ReportPromptService:
    """Deterministic prompt construction service for AI Infrastructure Reports."""

    SYSTEM_INSTRUCTIONS = (
        "You are an evidence-grounded road safety decision-support assistant.\n"
        "Your role is to translate empirical model evidence and spatial hotspot data into "
        "actionable, prioritized infrastructure interventions and policy recommendations for transport planners.\n\n"
        "CRITICAL GROUNDING & INTEGRITY RULES:\n"
        "1. ALL quantitative statistics, accident counts, coordinates, road numbers, and cluster IDs "
        "MUST come strictly from the provided Grounding Evidence Payload.\n"
        "2. NEVER invent, hallucinate, extrapolate, or estimate missing facts, coordinates, or statistics.\n"
        "3. DISTINGUISH observation from inference: treat model outputs as statistical indicators, "
        "not absolute proof of physical infrastructure causation.\n"
        "4. DO NOT claim that proposed recommendations have already been empirically validated; frame them "
        "as prioritized decision-support proposals for engineering review.\n"
        "5. MODEL-SPECIFIC DEFINITIONS:\n"
        "   - Student A: Random Forest multi-class severity prediction (Fatal, Serious, Slight).\n"
        "   - Student B: DBSCAN density clusters (500m haversine neighborhood, min_samples=25).\n"
        "   - Student C: Graph Neural Network (GNN) continuous road-segment risk index (0.0 to 1.0).\n"
        "6. Do not describe Student C predicted risk as a percentage probability of death or collision; "
        "refer to it as 'GNN predicted road-risk index' or 'structural risk score'."
    )

    @classmethod
    def build_prompt(cls, grounding_payload: GroundingPayload) -> str:
        """Construct the complete prompt including user context, grounding evidence, and schema instructions."""
        payload_json = grounding_payload.model_dump_json(indent=2)
        filters = grounding_payload.request_filters

        prompt = f"""{cls.SYSTEM_INSTRUCTIONS}

================================================================================
USER ANALYSIS CONTROLS:
- Geographic Region: {filters.region}
- Historical Period: {filters.period}
- Risk Threshold: {filters.threshold}
- Strategic Focus Area: {filters.focus}

================================================================================
VERIFIED GROUNDING EVIDENCE PAYLOAD:
```json
{payload_json}
```

OUTPUT REQUIREMENTS:
Produce a complete, structured JSON response where EVERY array is populated with grounded items:
1. `signals`: 3 to 6 key risk signals synthesized directly from the grounding data.
2. `interventions`: 2 to 5 ranked infrastructure interventions (e.g. roundabout conversion, signal timing, high-friction surfacing) tied to specific road numbers and coordinates in the evidence.
3. `evidence`: 3 to 6 concrete corroboration points directly citing cluster counts, GNN risk scores, or severity ratios from the payload.
4. `recommendations`: 2 to 5 actionable policy/engineering recommendations addressing problem areas.
5. `priorities`: 2 to 5 implementation matrix rows categorizing interventions by priority level, impact (low/moderate/high), and effort (low/moderate/high).
6. `summary`: Executive briefing summary (`theme`, `topIntervention`, `keySignal`, `nextStep`).
7. `provenance`: Grounding metadata referencing Student A, Student B, and Student C artifacts.

Ensure all text is professional, precise, and directly grounded in the provided evidence.
"""
        return prompt

