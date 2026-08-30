/**
 * History service boundary.
 *
 * Client-side persistence of real user-generated analysis runs,
 * model predictions, and AI decision-support reports.
 */

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
  /** Pre-formatted user-facing date string. */
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

export const HISTORY_STORAGE_KEY = "vantage_analysis_history";

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

/** Get stored history records from local storage. */
export function getStoredHistory(): HistoryRecord[] {
  if (typeof window === "undefined" || !window.localStorage) {
    return [];
  }
  try {
    const raw = window.localStorage.getItem(HISTORY_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as HistoryRecord[]) : [];
  } catch {
    return [];
  }
}

/** Save a newly executed analysis run into local history. */
export function recordAnalysisHistory(
  recordInput: Omit<HistoryRecord, "id" | "createdAt" | "createdLabel">,
): HistoryRecord {
  const now = new Date();
  const id = `run-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
  const createdLabel = now.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  const record: HistoryRecord = {
    ...recordInput,
    id,
    createdAt: now.toISOString(),
    createdLabel,
  };

  if (typeof window !== "undefined" && window.localStorage) {
    try {
      const existing = getStoredHistory();
      const updated = [record, ...existing.filter((r) => r.id !== record.id)].slice(0, 50);
      window.localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(updated));
    } catch {
      // Graceful fallback if localStorage quota is exceeded
    }
  }

  return record;
}

/** Clear all stored analysis history. */
export function clearStoredHistory(): void {
  if (typeof window !== "undefined" && window.localStorage) {
    try {
      window.localStorage.removeItem(HISTORY_STORAGE_KEY);
    } catch {
      // Ignore
    }
  }
}

/** Load history filtered by user controls. */
export async function loadHistory(filters: HistoryFilters): Promise<HistoryRecord[]> {
  const records = getStoredHistory();
  const query = filters.search.trim().toLowerCase();

  return records.filter((record) => {
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
