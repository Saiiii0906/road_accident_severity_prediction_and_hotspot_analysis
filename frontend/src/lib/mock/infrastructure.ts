/**
 * Isolated demonstration data for the AI Infrastructure Report workspace.
 *
 * Everything here is illustrative only — no value has been produced by a trained
 * model or validated against real collision records.
 *
 * TODO(backend): delete this module once the report endpoint is available.
 */

import type { InfrastructureReport } from "@/lib/api/infrastructure";

export const DEMO_INFRASTRUCTURE_REPORT: InfrastructureReport = {
  generatedLabel: "Demonstration report",
  signals: [
    {
      id: "hotspots",
      label: "High-risk hotspots",
      value: "38",
      note: "Clusters flagged in the demo dataset",
      level: "high",
    },
    {
      id: "critical-locations",
      label: "Critical severity locations",
      value: "9",
      note: "Locations with severe outcome concentration",
      level: "critical",
    },
    {
      id: "road-conditions",
      label: "Priority road conditions",
      value: "5",
      note: "Surface conditions above the demo threshold",
      level: "moderate",
    },
    {
      id: "risk-signals",
      label: "Infrastructure risk signals",
      value: "24",
      note: "Signals mapped to intervention categories",
      level: "high",
    },
  ],
  interventions: [
    {
      id: "lighting",
      intervention: "Improved street lighting",
      signal: "Night-time severity concentration",
      location: "Corridor N4 · Eastern district",
      level: "critical",
      rationale:
        "Evening and late-night incidents dominate this corridor in the demo dataset, which is consistent with reduced visibility exposure.",
    },
    {
      id: "resurfacing",
      intervention: "Road resurfacing",
      signal: "Poor surface condition index",
      location: "Segment A12 · Northern district",
      level: "high",
      rationale:
        "Wet and degraded surface records cluster on this segment, suggesting skid-resistance review.",
    },
    {
      id: "junction",
      intervention: "Junction redesign",
      signal: "Hotspot concentration at intersections",
      location: "Market Street / Ring Road junction",
      level: "high",
      rationale:
        "Repeated conflict points at the same approach indicate geometry and priority control should be reassessed.",
    },
    {
      id: "crossing",
      intervention: "Pedestrian crossing improvement",
      signal: "Vulnerable road user exposure",
      location: "City centre retail frontage",
      level: "moderate",
      rationale:
        "Pedestrian-involved records appear near uncontrolled crossing points in the demo sample.",
    },
    {
      id: "speed",
      intervention: "Speed management",
      signal: "High-severity outcome share",
      location: "Southern approach · Route S7",
      level: "moderate",
      rationale:
        "Severe outcomes are over-represented relative to volume, a pattern often linked to approach speeds.",
    },
    {
      id: "drainage",
      intervention: "Drainage improvement",
      signal: "Rain-related risk index",
      location: "Western district underpass",
      level: "low",
      rationale: "Standing-water incidents recur seasonally in the demonstration records.",
    },
  ],
  evidence: [
    {
      id: "hotspot-concentration",
      signal: "Hotspot concentration",
      value: "82 / 100",
      strength: 82,
      relation: "Supports junction redesign and lighting priorities",
      level: "high",
    },
    {
      id: "accident-severity",
      signal: "Accident severity",
      value: "2.8 average band",
      strength: 74,
      relation: "Supports speed management review",
      level: "high",
    },
    {
      id: "surface",
      signal: "Road surface condition",
      value: "68 / 100",
      strength: 68,
      relation: "Supports resurfacing prioritisation",
      level: "moderate",
    },
    {
      id: "weather",
      signal: "Weather exposure",
      value: "+18% in rain",
      strength: 61,
      relation: "Supports drainage and visibility works",
      level: "moderate",
    },
    {
      id: "time-of-day",
      signal: "Time-of-day pattern",
      value: "Evening peak",
      strength: 77,
      relation: "Supports street lighting upgrades",
      level: "high",
    },
    {
      id: "risk-index",
      signal: "Composite risk index",
      value: "71 / 100",
      strength: 71,
      relation: "Supports overall intervention ordering",
      level: "high",
    },
  ],
  recommendations: [
    {
      id: "junction-visibility",
      title: "Improve junction visibility",
      why: "Reduced visibility may increase conflict risk at high-traffic junctions.",
      objective: "Improve driver awareness and reduce collision exposure.",
      level: "critical",
      supportingSignals: ["Hotspot concentration", "Time-of-day pattern"],
    },
    {
      id: "surface-renewal",
      title: "Renew degraded carriageway surfacing",
      why: "Worn surfaces reduce skid resistance, particularly during wet conditions.",
      objective: "Restore braking performance and reduce loss-of-control events.",
      level: "high",
      supportingSignals: ["Road surface condition", "Weather exposure"],
    },
    {
      id: "lighting-upgrade",
      title: "Upgrade corridor street lighting",
      why: "Night-time incident share is elevated on unlit or poorly lit stretches.",
      objective: "Extend effective sight distance during darkness hours.",
      level: "high",
      supportingSignals: ["Time-of-day pattern", "Accident severity"],
    },
    {
      id: "crossing-provision",
      title: "Formalise pedestrian crossing provision",
      why: "Informal crossing behaviour concentrates pedestrian conflict points.",
      objective: "Channel pedestrian movement to protected, visible locations.",
      level: "moderate",
      supportingSignals: ["Hotspot concentration", "Composite risk index"],
    },
    {
      id: "signage",
      title: "Refresh warning and directional signage",
      why: "Inconsistent signage can reduce anticipation on unfamiliar approaches.",
      objective: "Improve advance warning ahead of known conflict points.",
      level: "low",
      supportingSignals: ["Composite risk index"],
    },
  ],
  priorities: [
    {
      id: "lighting",
      intervention: "Street lighting",
      priority: "high",
      impact: "high",
      effort: "moderate",
    },
    {
      id: "resurfacing",
      intervention: "Road resurfacing",
      priority: "high",
      impact: "high",
      effort: "high",
    },
    {
      id: "junction",
      intervention: "Junction redesign",
      priority: "critical",
      impact: "high",
      effort: "high",
    },
    {
      id: "crossing",
      intervention: "Crossing improvement",
      priority: "moderate",
      impact: "moderate",
      effort: "moderate",
    },
    {
      id: "signage",
      intervention: "Signage improvement",
      priority: "moderate",
      impact: "moderate",
      effort: "low",
    },
    {
      id: "drainage",
      intervention: "Drainage works",
      priority: "low",
      impact: "moderate",
      effort: "moderate",
    },
  ],
  summary: {
    theme: "Visibility and surface condition dominate the demo risk picture",
    topIntervention: "Improved street lighting on Corridor N4",
    keySignal: "Evening and late-night severity concentration",
    nextStep: "Commission a site review for the three highest-ranked locations",
  },
};
