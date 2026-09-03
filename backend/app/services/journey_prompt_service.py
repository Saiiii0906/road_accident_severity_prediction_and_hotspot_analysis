"""
Journey Safety Analysis LLM Prompt Engineering Service.

Formats structured multi-source evidence and enforces strict groundedness
and safety reporting constraints for Gemini/LLM synthesis.
"""

import json
from typing import Any

from app.schemas.journey import (
    DataAvailabilityStatus,
    HistoricalEvidenceSchema,
    JourneyDetailsSchema,
    LiveContextSchema,
    RouteInfoSchema,
    SafetyAssessmentSchema,
)


class JourneyPromptService:
    """Constructs grounded prompts and instructions for LLM journey safety synthesis."""

    SYSTEM_INSTRUCTIONS = """You are a specialized Road Safety Intelligence Synthesizer.
Your sole role is to produce an explainable, human-readable journey safety synthesis based STRICTLY on the provided structured evidence.

CRITICAL GROUNDEDNESS & TRUTHFULNESS RULES:
1. Use ONLY the supplied structured evidence. Never invent facts, data sources, or numbers.
2. Never infer unavailable data as available. If a feed is missing or unmonitored, state it clearly.
3. Never create numerical risk scores or composite percentages (overall_score is intentionally null; do not fabricate one).
4. Never create route-wide safety level categories if they are null.
5. Never fabricate confidence scores or percentages.
6. Never fabricate accident counts or casualties that are not in the supplied evidence.
7. Never extrapolate UK historical model results (Student B or C) to routes outside Great Britain.
8. Never treat absence of a DBSCAN hotspot (0 matched clusters) as proof that there were zero historical accidents.
9. Never treat Student A (RandomForest collision severity model) as a route-level prospective risk model.
10. Never claim live traffic or incidents exist if the corresponding feeds are unavailable.
11. If evidence is missing (e.g. traffic unmonitored outside London or historical models out-of-coverage), explicitly record it under limitations and state it in findings.
12. Actionable recommendations must be directly connected to the observed evidence (e.g., wet road surface, severe traffic delays, high topological risk corridor). Do not provide irrelevant generic filler recommendations.
13. If the input deterministic assessment is "partial" or "unavailable", your output status must be "partial" or "unavailable" accordingly.
"""

    @classmethod
    def build_evidence_payload(
        cls,
        journey: JourneyDetailsSchema,
        route: RouteInfoSchema,
        live: LiveContextSchema,
        historical: HistoricalEvidenceSchema,
        assessment: SafetyAssessmentSchema,
    ) -> dict[str, Any]:
        """Convert multi-source pipeline schemas into a structured JSON evidence dictionary."""
        payload: dict[str, Any] = {
            "journey": {
                "source": journey.source,
                "destination": journey.destination,
                "travel_date": str(journey.travel_date),
                "travel_time": str(journey.travel_time),
            },
            "route": {
                "status": route.status.value,
                "distance_km": route.distance_km,
                "duration_minutes": route.duration_minutes,
                "provider": route.provider,
                "corridor_roads": [s.name for s in route.segments if s.name],
            },
            "live_context": {
                "status": live.status.value,
                "weather": (
                    {
                        "status": live.weather.status.value,
                        "condition": live.weather.condition,
                        "temperature_c": live.weather.temperature_c,
                        "precipitation_probability": live.weather.precipitation_probability,
                        "precipitation_mm": live.weather.precipitation_mm,
                        "wind_speed_kmh": live.weather.wind_speed_kmh,
                        "visibility": live.weather.visibility,
                        "precipitation_risk": live.weather.precipitation_risk,
                        "location": live.weather.location_name,
                    }
                    if live.weather
                    else None
                ),
                "traffic": (
                    {
                        "status": live.traffic.status.value,
                        "congestion_level": live.traffic.congestion_level,
                        "delay_minutes": live.traffic.delay_minutes,
                        "corridor_monitored": live.traffic.corridor_monitored,
                        "description": live.traffic.description,
                    }
                    if live.traffic
                    else None
                ),
                "incidents": [
                    {
                        "incident_id": inc.incident_id,
                        "description": inc.description,
                        "severity": inc.severity,
                        "category": inc.category,
                        "location": inc.location,
                    }
                    for inc in live.incidents
                ],
            },
            "historical_evidence": {
                "status": historical.status.value,
                "coverage": (
                    {
                        "supported": historical.coverage.supported,
                        "region": historical.coverage.region,
                        "status": historical.coverage.status.value,
                        "reason": historical.coverage.reason,
                    }
                    if historical.coverage
                    else None
                ),
                "student_b_hotspots": (
                    {
                        "status": historical.student_b.status.value,
                        "hotspots_on_route": historical.student_b.hotspots_on_route,
                        "total_historical_accidents": historical.student_b.total_historical_accidents,
                        "highest_cluster_density": historical.student_b.highest_cluster_density,
                        "matched_hotspots_sample": [
                            {
                                "cluster_id": h.cluster_id,
                                "total_accidents": h.total_accidents,
                                "dominant_severity": h.dominant_severity,
                                "distance_to_route_m": round(h.distance_to_route_m, 1),
                            }
                            for h in historical.student_b.matched_hotspots[:3]
                        ],
                    }
                    if historical.student_b
                    else None
                ),
                "student_c_risk": (
                    {
                        "status": historical.student_c.status.value,
                        "segments_on_route": historical.student_c.segments_on_route,
                        "critical_segments_count": historical.student_c.critical_segments_count,
                        "high_risk_segments_count": historical.student_c.high_risk_segments_count,
                        "peak_gnn_risk": (
                            round(historical.student_c.peak_gnn_risk, 4)
                            if historical.student_c.peak_gnn_risk is not None
                            else None
                        ),
                        "high_risk_corridors": historical.student_c.high_risk_corridors,
                    }
                    if historical.student_c
                    else None
                ),
                "student_a_note": "Student A is collision-level only and excluded from prospective route traversal.",
            },
            "deterministic_assessment": {
                "status": assessment.status.value,
                "overall_score": assessment.overall_score,
                "level": assessment.level,
                "summary": assessment.summary,
                "key_factors": [
                    {
                        "factor": kf.factor,
                        "title": kf.title,
                        "severity": kf.severity,
                        "description": kf.description,
                        "source": kf.source,
                    }
                    for kf in assessment.key_factors
                ],
                "supporting_evidence": [
                    {
                        "source": ev.source,
                        "metric": ev.metric,
                        "value": ev.value,
                        "interpretation": ev.interpretation,
                    }
                    for ev in assessment.supporting_evidence
                ],
                "limitations": assessment.limitations,
            },
        }
        return payload

    @classmethod
    def build_prompt(
        cls,
        journey: JourneyDetailsSchema,
        route: RouteInfoSchema,
        live: LiveContextSchema,
        historical: HistoricalEvidenceSchema,
        assessment: SafetyAssessmentSchema,
    ) -> str:
        """Construct the grounded prompt string containing instructions and structured evidence."""
        evidence_payload = cls.build_evidence_payload(
            journey, route, live, historical, assessment
        )
        evidence_json = json.dumps(evidence_payload, indent=2)

        prompt = f"""{cls.SYSTEM_INSTRUCTIONS}

EVALUATION EVIDENCE (STRUCTURED INPUT):
```json
{evidence_json}
```

TASK:
Synthesize the structured evidence above into a concise, factual, and actionable Journey Safety Report conforming to the JSON schema.
- headline: High-level executive headline reflecting key observed conditions.
- summary: Grounded narrative overview explaining weather, traffic, disruptions, and historical model context.
- key_findings: List of key empirical findings with assigned severity and supporting evidence sources.
- recommendations: List of actionable, pragmatic driver/dispatcher precautions directly connected to the observed evidence.
- limitations: Explicit limitations reflecting missing data feeds or geographic boundary constraints.
"""
        return prompt

