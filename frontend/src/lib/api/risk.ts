/**
 * Road Risk Analysis service boundary.
 *
 * The FastAPI/model contract is NOT published yet, so this module is
 * provisional: types describe what the UI needs and the loader resolves from an
 * isolated demo dataset (`@/lib/mock/risk`).
 *
 * TODO(backend): replace `loadRiskAnalysis` internals with `apiRequest` against
 * the real endpoint and map the payload here. No UI component should change.
 */

import { DEMO_RISK_ANALYSIS } from "@/lib/mock/risk";

/** Presentation-only risk bands. Not a statistical claim. */
export type RiskLevel = "low" | "moderate" | "high" | "critical";

export interface RiskFilters {
  region: string;
  period: string;
  severity: string;
  roadCondition: string;
  weather: string;
  timeOfDay: string;
}

export interface RiskOverview {
  overallRiskLevel: RiskLevel;
  highRiskConditionCount: number;
  mostSignificantFactor: string;
  severeAccidentRate: string;
}

export interface RiskDistributionSlice {
  level: RiskLevel;
  /** Share of the demo record set, 0–100. */
  share: number;
  recordCount: number;
}

export interface ConditionBreakdown {
  id: string;
  label: string;
  /** Relative risk index (demo scale, 0–100). */
  riskIndex: number;
  level: RiskLevel;
  accidentShare: number;
  note: string;
}

export interface TimeBucket {
  id: string;
  label: string;
  riskIndex: number;
  level: RiskLevel;
  severeShare: number;
}

export interface RiskFactor {
  id: string;
  label: string;
  /** Relative contribution on a demo 0–100 scale. */
  contribution: number;
  level: RiskLevel;
}

export interface PriorityInsight {
  id: string;
  level: RiskLevel;
  text: string;
}

export interface FocusArea {
  id: string;
  area: string;
  signal: string;
  action: string;
  level: RiskLevel;
}

export interface RiskAnalysis {
  overview: RiskOverview;
  distribution: RiskDistributionSlice[];
  roadConditions: ConditionBreakdown[];
  weatherConditions: ConditionBreakdown[];
  timeBuckets: TimeBucket[];
  factors: RiskFactor[];
  insights: PriorityInsight[];
  focusAreas: FocusArea[];
}

export const DEFAULT_RISK_FILTERS: RiskFilters = {
  region: "all",
  period: "last_12_months",
  severity: "all",
  roadCondition: "all",
  weather: "all",
  timeOfDay: "all",
};

/**
 * Frontend-stage loader. The demo dataset is lightly narrowed client-side so the
 * workspace is interactive; the backend will own all aggregation later.
 */
export async function loadRiskAnalysis(filters: RiskFilters): Promise<RiskAnalysis> {
  await new Promise((resolve) => setTimeout(resolve, 700));

  const base = DEMO_RISK_ANALYSIS;

  const roadConditions =
    filters.roadCondition === "all"
      ? base.roadConditions
      : base.roadConditions.filter((c) => c.id === filters.roadCondition);

  const weatherConditions =
    filters.weather === "all"
      ? base.weatherConditions
      : base.weatherConditions.filter((c) => c.id === filters.weather);

  const timeBuckets =
    filters.timeOfDay === "all"
      ? base.timeBuckets
      : base.timeBuckets.filter((t) => t.id === filters.timeOfDay);

  const distribution =
    filters.severity === "all"
      ? base.distribution
      : base.distribution.filter((d) => d.level === filters.severity);

  return {
    ...base,
    distribution,
    roadConditions,
    weatherConditions,
    timeBuckets,
  };
}
