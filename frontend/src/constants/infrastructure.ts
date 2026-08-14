import type { Option } from "@/constants/severity";
import { RISK_LEVEL_DISPLAY } from "@/constants/risk";
import type { PriorityLevel } from "@/lib/api/infrastructure";

/** Reuses the approved risk tokens; only the wording differs. */
export const PRIORITY_DISPLAY: Record<
  PriorityLevel,
  { label: string; badgeClassName: string; barClassName: string; dotClassName: string }
> = {
  low: { ...RISK_LEVEL_DISPLAY.low, label: "Low" },
  moderate: { ...RISK_LEVEL_DISPLAY.moderate, label: "Moderate" },
  high: { ...RISK_LEVEL_DISPLAY.high, label: "High" },
  critical: { ...RISK_LEVEL_DISPLAY.critical, label: "Critical" },
};

export const PRIORITY_ORDER: PriorityLevel[] = ["critical", "high", "moderate", "low"];

export const REPORT_REGIONS: Option[] = [
  { value: "all", label: "All regions" },
  { value: "north", label: "Northern district" },
  { value: "central", label: "City centre" },
  { value: "east", label: "Eastern district" },
  { value: "south", label: "Southern district" },
  { value: "west", label: "Western district" },
];

export const REPORT_PERIODS: Option[] = [
  { value: "last_30_days", label: "Last 30 days" },
  { value: "last_6_months", label: "Last 6 months" },
  { value: "last_12_months", label: "Last 12 months" },
  { value: "last_3_years", label: "Last 3 years" },
];

export const REPORT_THRESHOLDS: Option[] = [
  { value: "low", label: "Include all signals" },
  { value: "moderate", label: "Moderate and above" },
  { value: "high", label: "High and above" },
  { value: "critical", label: "Critical only" },
];

export const REPORT_FOCUS_OPTIONS: Option[] = [
  { value: "overall_safety", label: "Overall safety" },
  { value: "high_severity", label: "High-severity incidents" },
  { value: "hotspot_intervention", label: "Hotspot intervention" },
  { value: "road_conditions", label: "Road conditions" },
  { value: "infrastructure_priorities", label: "Infrastructure priorities" },
];

export const IMPACT_EFFORT_DISPLAY: Record<
  "low" | "moderate" | "high",
  { label: string; className: string }
> = {
  low: { label: "Low", className: "border-border bg-muted/40 text-muted-foreground" },
  moderate: { label: "Moderate", className: "border-warning/30 bg-warning/10 text-warning" },
  high: { label: "High", className: "border-primary/30 bg-primary/10 text-primary" },
};
