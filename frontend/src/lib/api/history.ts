/**
 * History service boundary (frontend stage).
 *
 * TODO(backend): replace `loadHistory` internals with `apiRequest` against the
 * real endpoint and map the payload into `HistoryRecord`. No component changes.
 */

import { DEMO_HISTORY_RECORDS } from "@/lib/mock/history";

export type AnalysisType =
  "severity_prediction" | "hotspot_analysis" | "road_risk_analysis" | "infrastructure_report";

export type HistoryStatus = "completed" | "processing" | "failed";

export interface HistoryRecord {
  id: string;
  type: AnalysisType;
  title: string;
  region: string;
  regionLabel: string;
  period: string;
  periodLabel: string;
  /** ISO timestamp. */
  createdAt: string;
  /** Pre-formatted label so the demo list renders deterministically. */
  createdLabel: string;
  status: HistoryStatus;
  /** Short, scannable outcome summary. */
  result: string;
  signals: string[];
}

export interface HistoryFilters {
  type: AnalysisType | "all";
  region: string;
  period: string;
  status: HistoryStatus | "all";
  search: string;
}

export interface HistorySummary {
  total: number;
  completed: number;
  processing: number;
  failed: number;
}

export const DEFAULT_HISTORY_FILTERS: HistoryFilters = {
  type: "all",
  region: "all",
  period: "all",
  status: "all",
  search: "",
};

export function summarizeHistory(records: HistoryRecord[]): HistorySummary {
  return {
    total: records.length,
    completed: records.filter((r) => r.status === "completed").length,
    processing: records.filter((r) => r.status === "processing").length,
    failed: records.filter((r) => r.status === "failed").length,
  };
}

/** Route for the "View analysis" action — reuses the existing modules. */
export const ANALYSIS_ROUTE = {
  severity_prediction: "/severity-prediction",
  hotspot_analysis: "/hotspot-explorer",
  road_risk_analysis: "/road-risk-analysis",
  infrastructure_report: "/ai-infrastructure-report",
} as const satisfies Record<AnalysisType, string>;

/** Frontend-stage loader: narrows the isolated demo dataset client-side. */
export async function loadHistory(filters: HistoryFilters): Promise<HistoryRecord[]> {
  await new Promise((resolve) => setTimeout(resolve, 600));

  const query = filters.search.trim().toLowerCase();

  return DEMO_HISTORY_RECORDS.filter((record) => {
    if (filters.type !== "all" && record.type !== filters.type) return false;
    if (filters.status !== "all" && record.status !== filters.status) return false;
    if (filters.region !== "all" && record.region !== filters.region) return false;
    if (filters.period !== "all" && record.period !== filters.period) return false;
    if (!query) return true;
    return (
      record.title.toLowerCase().includes(query) ||
      record.regionLabel.toLowerCase().includes(query) ||
      record.result.toLowerCase().includes(query)
    );
  });
}
