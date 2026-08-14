/**
 * AI Infrastructure Report service boundary.
 *
 * The report/model contract is NOT published yet. This module deliberately keeps
 * only the shapes the UI needs and resolves them from an isolated demo dataset
 * (`@/lib/mock/infrastructure`).
 *
 * TODO(backend): replace `generateInfrastructureReport` internals with a real
 * request and map the payload here. No UI component should need to change.
 */

import { DEMO_INFRASTRUCTURE_REPORT } from "@/lib/mock/infrastructure";
import type { RiskLevel } from "@/lib/api/risk";

/** Presentation-only priority bands; reuses the existing risk visual tokens. */
export type PriorityLevel = RiskLevel;

export interface ReportFilters {
  region: string;
  period: string;
  threshold: string;
  focus: string;
}

export interface RiskSignal {
  id: string;
  label: string;
  value: string;
  note: string;
  level: PriorityLevel;
}

export interface PriorityIntervention {
  id: string;
  intervention: string;
  signal: string;
  location: string;
  level: PriorityLevel;
  rationale: string;
}

export interface EvidenceItem {
  id: string;
  signal: string;
  value: string;
  /** Demo strength on a 0–100 scale. */
  strength: number;
  relation: string;
  level: PriorityLevel;
}

export interface Recommendation {
  id: string;
  title: string;
  why: string;
  objective: string;
  level: PriorityLevel;
  supportingSignals: string[];
}

export interface PriorityMatrixRow {
  id: string;
  intervention: string;
  priority: PriorityLevel;
  impact: "low" | "moderate" | "high";
  effort: "low" | "moderate" | "high";
}

export interface ReportSummary {
  theme: string;
  topIntervention: string;
  keySignal: string;
  nextStep: string;
}

export interface InfrastructureReport {
  generatedLabel: string;
  signals: RiskSignal[];
  interventions: PriorityIntervention[];
  evidence: EvidenceItem[];
  recommendations: Recommendation[];
  priorities: PriorityMatrixRow[];
  summary: ReportSummary;
}

export const DEFAULT_REPORT_FILTERS: ReportFilters = {
  region: "all",
  period: "last_12_months",
  threshold: "moderate",
  focus: "overall_safety",
};

const THRESHOLD_RANK: Record<string, number> = {
  low: 0,
  moderate: 1,
  high: 2,
  critical: 3,
};

const LEVEL_RANK: Record<PriorityLevel, number> = {
  low: 0,
  moderate: 1,
  high: 2,
  critical: 3,
};

/**
 * Frontend-stage generator. The demo dataset is lightly narrowed client-side so
 * the controls feel responsive; the backend will own all analysis later.
 */
export async function generateInfrastructureReport(
  filters: ReportFilters,
): Promise<InfrastructureReport> {
  await new Promise((resolve) => setTimeout(resolve, 800));

  const min = THRESHOLD_RANK[filters.threshold] ?? 0;
  const base = DEMO_INFRASTRUCTURE_REPORT;

  return {
    ...base,
    interventions: base.interventions.filter((i) => LEVEL_RANK[i.level] >= min),
    recommendations: base.recommendations.filter((r) => LEVEL_RANK[r.level] >= min),
    priorities: base.priorities.filter((p) => LEVEL_RANK[p.priority] >= min),
  };
}
