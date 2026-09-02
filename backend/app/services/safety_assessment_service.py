"""
Deterministic Journey Safety Assessment Service.

Evaluates multi-source evidence (resolved route, live environmental context,
and historical empirical model outputs) to produce an evidence-based, transparent
safety assessment without arbitrary weighting or generative LLM extrapolation.
"""

import logging
from typing import Optional

from app.schemas.journey import (
    DataAvailabilityStatus,
    HistoricalEvidenceSchema,
    LiveContextSchema,
    RouteInfoSchema,
    SafetyAssessmentSchema,
    SafetyDataCoverageSchema,
    SafetyEvidenceItemSchema,
    SafetyKeyFactorSchema,
)

logger = logging.getLogger(__name__)


class SafetyAssessmentService:
    """Computes a transparent, evidence-based safety assessment across all verified subsystems."""

    def assess(
        self,
        route: RouteInfoSchema,
        live: LiveContextSchema,
        historical: HistoricalEvidenceSchema,
    ) -> SafetyAssessmentSchema:
        """Evaluate real journey evidence and synthesize a deterministic assessment."""
        key_factors: list[SafetyKeyFactorSchema] = []
        supporting_evidence: list[SafetyEvidenceItemSchema] = []
        limitations: list[str] = []

        # 1. Data Coverage Assessment
        data_coverage = SafetyDataCoverageSchema(
            route=route.status,
            weather=live.weather.status if live.weather else DataAvailabilityStatus.UNAVAILABLE,
            traffic=live.traffic.status if live.traffic else DataAvailabilityStatus.UNAVAILABLE,
            incidents=DataAvailabilityStatus.AVAILABLE if live.incidents else (
                DataAvailabilityStatus.AVAILABLE if live.status in (DataAvailabilityStatus.AVAILABLE, DataAvailabilityStatus.PARTIAL) else DataAvailabilityStatus.UNAVAILABLE
            ),
            historical=historical.status,
        )

        # 2. Route Corridor Context
        if route.status == DataAvailabilityStatus.AVAILABLE and route.distance_km is not None:
            supporting_evidence.append(
                SafetyEvidenceItemSchema(
                    source=f"{route.provider or 'OSRM'} Routing Engine",
                    metric="corridor_extent",
                    value=f"{route.distance_km} km (~{route.duration_minutes or 0:.0f} min)",
                    interpretation="Estimated driving distance and travel duration under free-flow conditions.",
                )
            )
        else:
            limitations.append(
                "Precise routing geometry is pending or could not be determined; corridor extent is approximate."
            )

        # 3. Live Traffic Context
        if live.traffic and live.traffic.status == DataAvailabilityStatus.AVAILABLE:
            cong = (live.traffic.congestion_level or "low").lower()
            if cong in ("severe", "critical"):
                traffic_sev = "critical"
            elif cong in ("serious", "heavy"):
                traffic_sev = "high"
            elif cong in ("moderate", "medium"):
                traffic_sev = "moderate"
            else:
                traffic_sev = "low"

            delay_text = (
                f" (+{live.traffic.delay_minutes} min delay)"
                if live.traffic.delay_minutes and live.traffic.delay_minutes > 0
                else ""
            )
            key_factors.append(
                SafetyKeyFactorSchema(
                    factor="live_traffic",
                    title="Corridor Traffic Flow",
                    severity=traffic_sev,
                    description=live.traffic.description or f"Current corridor traffic is {cong}{delay_text}.",
                    source="TfL Road Network",
                )
            )
            supporting_evidence.append(
                SafetyEvidenceItemSchema(
                    source="TfL Road Network",
                    metric="traffic_congestion",
                    value=f"{cong.capitalize()}{delay_text}",
                    interpretation="Real-time traffic monitor along designated road corridors.",
                )
            )
        else:
            limitations.append(
                "Live traffic monitoring is unavailable for this corridor; real-time congestion delays cannot be factored into the assessment."
            )

        # 4. Live Weather Context
        if live.weather and live.weather.status == DataAvailabilityStatus.AVAILABLE:
            precip_prob = live.weather.precipitation_probability or 0
            cond = live.weather.condition or "Unknown"

            # Factual severity classification based on meteorological indicators
            if precip_prob >= 70 or any(w in cond.lower() for w in ("storm", "snow", "heavy")):
                weather_sev = "high"
            elif precip_prob >= 40 or any(w in cond.lower() for w in ("rain", "drizzle", "shower")):
                weather_sev = "moderate"
            else:
                weather_sev = "low"

            key_factors.append(
                SafetyKeyFactorSchema(
                    factor="live_weather",
                    title="Atmospheric & Surface Conditions",
                    severity=weather_sev,
                    description=(
                        f"Forecast at travel time: {cond}, {live.weather.temperature_c}°C, "
                        f"{precip_prob}% precipitation probability, wind speed {live.weather.wind_speed_kmh or 0} km/h."
                    ),
                    source="Open-Meteo Weather Service",
                )
            )
            supporting_evidence.append(
                SafetyEvidenceItemSchema(
                    source="Open-Meteo",
                    metric="precipitation_probability",
                    value=f"{precip_prob}% ({cond})",
                    interpretation="Forecasted probability of rainfall or road surface wetness affecting tire grip.",
                )
            )
        else:
            limitations.append(
                "Live weather forecast is unavailable for this corridor; atmospheric friction hazards cannot be evaluated."
            )

        # 5. Active Road Hazards & Disruptions
        if live.incidents:
            # Determine peak disruption severity
            severities = [inc.severity.lower() for inc in live.incidents if inc.severity]
            if any(s in ("severe", "closure", "blocked") for s in severities):
                inc_sev = "critical"
            elif any(s in ("major", "serious") for s in severities):
                inc_sev = "high"
            else:
                inc_sev = "moderate"

            top_desc = live.incidents[0].description
            key_factors.append(
                SafetyKeyFactorSchema(
                    factor="active_disruptions",
                    title="Active Road Hazards & Disruptions",
                    severity=inc_sev,
                    description=f"{len(live.incidents)} active disruption(s) detected along corridor (e.g. {top_desc}).",
                    source="TfL Disruptions Feed",
                )
            )
            supporting_evidence.append(
                SafetyEvidenceItemSchema(
                    source="TfL Disruptions Feed",
                    metric="active_disruptions_count",
                    value=f"{len(live.incidents)} active",
                    interpretation="Active roadworks, lane closures, or incident notices on monitored corridor links.",
                )
            )
        elif live.status in (DataAvailabilityStatus.AVAILABLE, DataAvailabilityStatus.PARTIAL):
            supporting_evidence.append(
                SafetyEvidenceItemSchema(
                    source="TfL Disruptions Feed",
                    metric="active_disruptions_count",
                    value="0 detected",
                    interpretation="No active major road hazards or closures reported by transport authority on the corridor.",
                )
            )
        else:
            limitations.append(
                "Active road disruption feed is unavailable for this corridor."
            )

        # 6. Historical Grounding: Coverage Check & Evidence
        historical_supported = (
            historical.coverage.supported
            if historical.coverage is not None
            else historical.status in (DataAvailabilityStatus.AVAILABLE, DataAvailabilityStatus.PARTIAL)
        )

        if not historical_supported or historical.status == DataAvailabilityStatus.UNAVAILABLE:
            limitations.append(
                "Historical model evidence is unavailable for this journey: the route lies outside "
                "the geographic coverage of historical UK road safety models (Great Britain)."
            )
        else:
            # Student B: DBSCAN Hotspots
            if historical.student_b and historical.student_b.status == DataAvailabilityStatus.AVAILABLE:
                if historical.student_b.hotspots_on_route > 0:
                    peak_dens = historical.student_b.highest_cluster_density or 0
                    if peak_dens >= 100:
                        hotspot_sev = "critical"
                    elif peak_dens >= 40:
                        hotspot_sev = "high"
                    else:
                        hotspot_sev = "moderate"

                    key_factors.append(
                        SafetyKeyFactorSchema(
                            factor="historical_hotspots",
                            title="Historical Accident Hotspot Exposure",
                            severity=hotspot_sev,
                            description=(
                                f"Corridor intersects {historical.student_b.hotspots_on_route} historical DBSCAN "
                                f"accident cluster(s) with {historical.student_b.total_historical_accidents:,} crashes "
                                f"(peak density: {peak_dens} accidents)."
                            ),
                            source="Student B DBSCAN Model",
                        )
                    )
                    supporting_evidence.append(
                        SafetyEvidenceItemSchema(
                            source="Student B DBSCAN",
                            metric="matched_hotspots_count",
                            value=f"{historical.student_b.hotspots_on_route} clusters",
                            interpretation="Statistically significant historical accident clusters within 1,000m buffer.",
                        )
                    )
                else:
                    # Honest interpretation of 0 matches
                    key_factors.append(
                        SafetyKeyFactorSchema(
                            factor="historical_hotspots",
                            title="Historical Accident Hotspot Exposure",
                            severity="low",
                            description=(
                                "No dense DBSCAN accident clusters intersect the 1,000m corridor buffer. "
                                "This indicates an absence of dense statistical clusters, not necessarily zero historical accidents."
                            ),
                            source="Student B DBSCAN Model",
                        )
                    )
                    supporting_evidence.append(
                        SafetyEvidenceItemSchema(
                            source="Student B DBSCAN",
                            metric="matched_hotspots_count",
                            value="0 clusters",
                            interpretation="Absence of dense DBSCAN centroids along corridor. Does not imply zero historical accidents.",
                        )
                    )

            # Student C: RoadRiskGNN Segments
            if historical.student_c and historical.student_c.status == DataAvailabilityStatus.AVAILABLE:
                if historical.student_c.segments_on_route > 0:
                    crit_count = historical.student_c.critical_segments_count
                    high_count = historical.student_c.high_risk_segments_count
                    peak_risk = historical.student_c.peak_gnn_risk or 0.0

                    if crit_count > 0:
                        gnn_sev = "critical"
                    elif high_count > 0:
                        gnn_sev = "high"
                    elif peak_risk >= 0.06:
                        gnn_sev = "moderate"
                    else:
                        gnn_sev = "low"

                    corridors_str = (
                        f" Corridors affected: {', '.join(historical.student_c.high_risk_corridors)}."
                        if historical.student_c.high_risk_corridors
                        else ""
                    )
                    key_factors.append(
                        SafetyKeyFactorSchema(
                            factor="topological_road_risk",
                            title="GNN Topological Road Risk",
                            severity=gnn_sev,
                            description=(
                                f"Traversed {historical.student_c.segments_on_route} GNN road segments "
                                f"({crit_count} critical, {high_count} high risk, peak risk: {peak_risk:.4f}).{corridors_str}"
                            ),
                            source="Student C RoadRiskGNN",
                        )
                    )
                    supporting_evidence.append(
                        SafetyEvidenceItemSchema(
                            source="Student C RoadRiskGNN",
                            metric="peak_segment_risk",
                            value=f"{peak_risk:.4f} ({crit_count} critical, {high_count} high)",
                            interpretation="Continuous structural risk index reflecting road geometry and topology.",
                        )
                    )
                else:
                    key_factors.append(
                        SafetyKeyFactorSchema(
                            factor="topological_road_risk",
                            title="GNN Topological Road Risk",
                            severity="unknown",
                            description=(
                                "No modeled GNN road network segments intersect the 1,000m corridor buffer. "
                                "This indicates an absence of mapped network links, not low risk."
                            ),
                            source="Student C RoadRiskGNN",
                        )
                    )
                    supporting_evidence.append(
                        SafetyEvidenceItemSchema(
                            source="Student C RoadRiskGNN",
                            metric="matched_segments_count",
                            value="0 segments",
                            interpretation="Absence of modeled graph links along corridor. Does not imply safe infrastructure.",
                        )
                    )

        # 7. Student A Applicability Note
        limitations.append(
            "Student A RandomForest model predicts individual collision severity outcomes given specific crash-level "
            "parameters (vehicles involved, casualty counts, impact dynamics) rather than prospective corridor traversal "
            "risk. It is excluded from route-wide prospective risk without fabricating hypothetical crash inputs."
        )

        # 8. Overall Status Computation
        if route.status == DataAvailabilityStatus.UNAVAILABLE:
            overall_status = DataAvailabilityStatus.UNAVAILABLE
        elif (
            not historical_supported
            or historical.status in (DataAvailabilityStatus.PARTIAL, DataAvailabilityStatus.UNAVAILABLE)
            or live.status in (DataAvailabilityStatus.PARTIAL, DataAvailabilityStatus.UNAVAILABLE)
        ):
            overall_status = DataAvailabilityStatus.PARTIAL
            if historical.status == DataAvailabilityStatus.PARTIAL:
                limitations.append(
                    "Historical model coverage is partial: portions of the route extend beyond the geographic bounds of the historical UK road safety dataset."
                )
        else:
            overall_status = DataAvailabilityStatus.AVAILABLE

        # 9. Deterministic Summary Synthesis
        summary_parts = []
        if route.status == DataAvailabilityStatus.AVAILABLE and route.distance_km is not None:
            summary_parts.append(f"Route covers {route.distance_km} km (~{route.duration_minutes or 0:.0f} min).")

        live_summary = []
        if live.weather and live.weather.status == DataAvailabilityStatus.AVAILABLE:
            live_summary.append(f"weather: {live.weather.condition} ({live.weather.precipitation_probability}% rain)")
        if live.traffic and live.traffic.status == DataAvailabilityStatus.AVAILABLE:
            live_summary.append(f"traffic: {live.traffic.congestion_level}")
        if live.incidents:
            live_summary.append(f"{len(live.incidents)} active disruption(s)")
        elif live.status in (DataAvailabilityStatus.AVAILABLE, DataAvailabilityStatus.PARTIAL):
            live_summary.append("0 disruptions")

        if live_summary:
            summary_parts.append("Live context: " + ", ".join(live_summary) + ".")

        if historical_supported and historical.status in (DataAvailabilityStatus.AVAILABLE, DataAvailabilityStatus.PARTIAL):
            hist_parts = []
            if historical.student_b:
                hist_parts.append(f"{historical.student_b.hotspots_on_route} hotspot cluster(s)")
            if historical.student_c:
                hist_parts.append(f"{historical.student_c.segments_on_route} GNN segment(s) (peak risk: {historical.student_c.peak_gnn_risk or 0:.4f})")
            if hist_parts:
                summary_parts.append("Historical grounding: " + ", ".join(hist_parts) + ".")
        else:
            summary_parts.append("Historical models: unavailable for this route region.")

        summary_parts.append(
            "Composite numerical score is omitted in accordance with empirical methodology constraints."
        )
        summary = " ".join(summary_parts)

        return SafetyAssessmentSchema(
            status=overall_status,
            overall_score=None,  # Strictly None as no defensible composite weighting exists
            level=None,          # Strictly None to avoid arbitrary route-wide thresholding
            summary=summary,
            key_factors=key_factors,
            supporting_evidence=supporting_evidence,
            data_coverage=data_coverage,
            limitations=limitations,
        )
