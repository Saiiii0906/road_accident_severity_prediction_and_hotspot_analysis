/**
 * DEMO / PRESENTATION DATA ONLY.
 *
 * Illustrative placeholder values used to exercise the Road Risk Analysis UI
 * before backend/model integration. These are NOT real-world statistics and no
 * value here should be read as a validated finding.
 *
 * TODO(backend): delete this file once `loadRiskAnalysis` reads from the API.
 */

import type { RiskAnalysis } from "@/lib/api/risk";

export const DEMO_RISK_ANALYSIS: RiskAnalysis = {
  overview: {
    overallRiskLevel: "high",
    highRiskConditionCount: 5,
    mostSignificantFactor: "Wet road surface",
    severeAccidentRate: "18.4% of demo records",
  },

  distribution: [
    { level: "low", share: 34, recordCount: 1420 },
    { level: "moderate", share: 31, recordCount: 1295 },
    { level: "high", share: 24, recordCount: 1004 },
    { level: "critical", share: 11, recordCount: 462 },
  ],

  roadConditions: [
    {
      id: "wet",
      label: "Wet surface",
      riskIndex: 82,
      level: "critical",
      accidentShare: 29,
      note: "Elevated severe-outcome share in the demo set.",
    },
    {
      id: "damaged",
      label: "Poor surface condition",
      riskIndex: 71,
      level: "high",
      accidentShare: 18,
      note: "Surface defects co-occur with loss-of-control records.",
    },
    {
      id: "works",
      label: "Under construction",
      riskIndex: 58,
      level: "moderate",
      accidentShare: 12,
      note: "Works zones show clustered low-speed impacts.",
    },
    {
      id: "dry",
      label: "Dry surface",
      riskIndex: 41,
      level: "moderate",
      accidentShare: 33,
      note: "Highest volume, lower relative risk index.",
    },
    {
      id: "other",
      label: "Other or unrecorded",
      riskIndex: 26,
      level: "low",
      accidentShare: 8,
      note: "Sparse demo coverage — treat as inconclusive.",
    },
  ],

  weatherConditions: [
    {
      id: "fog",
      label: "Fog",
      riskIndex: 79,
      level: "critical",
      accidentShare: 11,
      note: "Low volume with a high severe-outcome ratio.",
    },
    {
      id: "storm",
      label: "Storm or high winds",
      riskIndex: 68,
      level: "high",
      accidentShare: 7,
      note: "Concentrated on exposed high-speed sections.",
    },
    {
      id: "rain",
      label: "Rain",
      riskIndex: 63,
      level: "high",
      accidentShare: 26,
      note: "Broad exposure across the demo network.",
    },
    {
      id: "clear",
      label: "Clear",
      riskIndex: 38,
      level: "moderate",
      accidentShare: 49,
      note: "Volume-driven rather than condition-driven.",
    },
    {
      id: "other",
      label: "Other",
      riskIndex: 22,
      level: "low",
      accidentShare: 7,
      note: "Insufficient demo records for comparison.",
    },
  ],

  timeBuckets: [
    {
      id: "early_morning",
      label: "Early morning",
      riskIndex: 46,
      level: "moderate",
      severeShare: 12,
    },
    { id: "morning", label: "Morning", riskIndex: 58, level: "moderate", severeShare: 15 },
    { id: "afternoon", label: "Afternoon", riskIndex: 64, level: "high", severeShare: 17 },
    { id: "evening", label: "Evening", riskIndex: 77, level: "high", severeShare: 22 },
    { id: "night", label: "Night", riskIndex: 88, level: "critical", severeShare: 27 },
    { id: "late_night", label: "Late night", riskIndex: 71, level: "high", severeShare: 24 },
  ],

  factors: [
    { id: "f1", label: "Wet road surface", contribution: 84, level: "critical" },
    { id: "f2", label: "Poor visibility", contribution: 76, level: "high" },
    { id: "f3", label: "High-speed road class", contribution: 69, level: "high" },
    { id: "f4", label: "Night-time conditions", contribution: 61, level: "high" },
    { id: "f5", label: "Junction proximity", contribution: 54, level: "moderate" },
    { id: "f6", label: "Heavy traffic density", contribution: 43, level: "moderate" },
    { id: "f7", label: "Unlit carriageway", contribution: 31, level: "low" },
  ],

  insights: [
    {
      id: "i1",
      level: "critical",
      text: "Higher risk is observed under wet-road conditions across the demo record set.",
    },
    {
      id: "i2",
      level: "high",
      text: "Night-time records show an elevated concentration of severe outcomes.",
    },
    {
      id: "i3",
      level: "moderate",
      text: "High-speed road classes account for a disproportionate share of severe records.",
    },
    {
      id: "i4",
      level: "low",
      text: "Clear-weather records are volume-driven and do not indicate elevated condition risk.",
    },
  ],

  focusAreas: [
    {
      id: "fa1",
      area: "Road surface improvement",
      signal: "Wet and defective surfaces rank highest in the demo index.",
      action: "Prioritise anti-skid resurfacing and drainage correction reviews.",
      level: "critical",
    },
    {
      id: "fa2",
      area: "Lighting improvement",
      signal: "Night and late-night periods carry the highest severe share.",
      action: "Audit unlit sections on higher-speed corridors.",
      level: "high",
    },
    {
      id: "fa3",
      area: "Visibility management",
      signal: "Fog records show a high severe-to-volume ratio.",
      action: "Extend reflective delineation and variable warning signage.",
      level: "high",
    },
    {
      id: "fa4",
      area: "Speed management",
      signal: "High-speed classes recur among top-contributing factors.",
      action: "Review posted limits and enforcement placement.",
      level: "moderate",
    },
    {
      id: "fa5",
      area: "Junction redesign",
      signal: "Junction proximity appears as a mid-ranked contributor.",
      action: "Assess turn phasing and sightlines at recurring junction types.",
      level: "moderate",
    },
  ],
};
