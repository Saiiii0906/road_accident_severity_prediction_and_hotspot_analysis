/**
 * AI Infrastructure Report service boundary.
 *
 * Connected to the real backend AI decision-support endpoint:
 * POST /api/reports/ai-infrastructure-report
 */

import { apiRequest } from "@/lib/api/client";
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
  /** Empirical evidence strength score on a 0–100 scale. */
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

export interface ReportProvenance {
  student_a_model: string;
  student_b_hotspots: string;
  student_c_gnn: string;
  grounded: boolean;
}

export interface InfrastructureReport {
  generatedLabel: string;
  signals: RiskSignal[];
  interventions: PriorityIntervention[];
  evidence: EvidenceItem[];
  recommendations: Recommendation[];
  priorities: PriorityMatrixRow[];
  summary: ReportSummary;
  provenance?: ReportProvenance;
}

export const DEFAULT_REPORT_FILTERS: ReportFilters = {
  region: "all",
  period: "last_12_months",
  threshold: "moderate",
  focus: "overall_safety",
};

/**
 * Generate evidence-grounded AI Infrastructure report via backend API.
 */
export async function generateInfrastructureReport(
  filters: ReportFilters,
): Promise<InfrastructureReport> {
  return apiRequest<InfrastructureReport>("/api/reports/ai-infrastructure-report", {
    method: "POST",
    body: {
      region: filters.region,
      period: filters.period,
      threshold: filters.threshold,
      focus: filters.focus,
    },
  });
}
