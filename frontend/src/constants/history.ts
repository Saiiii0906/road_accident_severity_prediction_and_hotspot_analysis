import type { Option } from "@/constants/severity";
import type { AnalysisType, HistoryStatus } from "@/lib/api/history";
import {
  Gauge,
  MapPinned,
  Route as RouteIcon,
  BrainCircuit,
  Navigation,
  type LucideIcon,
} from "lucide-react";

export const ANALYSIS_TYPE_DISPLAY: Record<AnalysisType, { label: string; icon: LucideIcon }> = {
  severity_prediction: { label: "Severity prediction", icon: Gauge },
  hotspot_analysis: { label: "Hotspot analysis", icon: MapPinned },
  road_risk_analysis: { label: "Road risk analysis", icon: RouteIcon },
  infrastructure_report: { label: "Infrastructure report", icon: BrainCircuit },
  journey_safety_analysis: { label: "Journey safety analysis", icon: Navigation },
};

/** Reuses existing status tokens only — no new colours. */
export const HISTORY_STATUS_DISPLAY: Record<
  HistoryStatus,
  { label: string; badgeClassName: string; dotClassName: string }
> = {
  completed: {
    label: "Completed",
    badgeClassName: "border-success/30 bg-success/10 text-success",
    dotClassName: "bg-success",
  },
  processing: {
    label: "Processing",
    badgeClassName: "border-warning/30 bg-warning/10 text-warning",
    dotClassName: "bg-warning",
  },
  failed: {
    label: "Failed",
    badgeClassName: "border-danger/30 bg-danger/10 text-danger",
    dotClassName: "bg-danger",
  },
};

export const HISTORY_TYPES: Option[] = [
  { value: "all", label: "All analyses" },
  { value: "journey_safety_analysis", label: "Journey safety analysis" },
  { value: "severity_prediction", label: "Severity prediction" },
  { value: "hotspot_analysis", label: "Hotspot analysis" },
  { value: "road_risk_analysis", label: "Road risk analysis" },
  { value: "infrastructure_report", label: "Infrastructure report" },
];

export const HISTORY_STATUSES: Option[] = [
  { value: "all", label: "All statuses" },
  { value: "completed", label: "Completed" },
  { value: "processing", label: "Processing" },
  { value: "failed", label: "Failed" },
];

export const HISTORY_REGIONS: Option[] = [
  { value: "all", label: "All regions" },
  { value: "north", label: "Northern district" },
  { value: "central", label: "Central district" },
  { value: "east", label: "Eastern district" },
  { value: "south", label: "Southern district" },
  { value: "west", label: "Western district" },
];

export const HISTORY_PERIODS: Option[] = [
  { value: "all", label: "Any period" },
  { value: "last_30_days", label: "Last 30 days" },
  { value: "last_6_months", label: "Last 6 months" },
  { value: "last_12_months", label: "Last 12 months" },
  { value: "last_3_years", label: "Last 3 years" },
];
