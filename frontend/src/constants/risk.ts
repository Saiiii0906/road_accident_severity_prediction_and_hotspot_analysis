import type { Option } from "@/constants/severity";
import type { RiskLevel } from "@/lib/api/risk";

export const RISK_LEVEL_DISPLAY: Record<
  RiskLevel,
  { label: string; badgeClassName: string; barClassName: string; dotClassName: string }
> = {
  low: {
    label: "Low risk",
    badgeClassName: "border-success/30 bg-success/10 text-success",
    barClassName: "bg-success",
    dotClassName: "bg-success",
  },
  moderate: {
    label: "Moderate risk",
    badgeClassName: "border-warning/30 bg-warning/10 text-warning",
    barClassName: "bg-warning",
    dotClassName: "bg-warning",
  },
  high: {
    label: "High risk",
    badgeClassName: "border-danger/30 bg-danger/10 text-danger",
    barClassName: "bg-danger",
    dotClassName: "bg-danger",
  },
  critical: {
    label: "Critical risk",
    badgeClassName: "border-danger/40 bg-danger/15 text-danger",
    barClassName: "bg-danger",
    dotClassName: "bg-danger",
  },
};

export const RISK_LEVEL_ORDER: RiskLevel[] = ["low", "moderate", "high", "critical"];

export const RISK_REGIONS: Option[] = [
  { value: "all", label: "All regions" },
  { value: "north", label: "Northern district" },
  { value: "central", label: "City centre" },
  { value: "east", label: "Eastern district" },
  { value: "south", label: "Southern district" },
  { value: "west", label: "Western district" },
];

export const RISK_PERIODS: Option[] = [
  { value: "last_30_days", label: "Last 30 days" },
  { value: "last_6_months", label: "Last 6 months" },
  { value: "last_12_months", label: "Last 12 months" },
  { value: "last_3_years", label: "Last 3 years" },
];

export const RISK_SEVERITIES: Option[] = [
  { value: "all", label: "All risk levels" },
  { value: "low", label: "Low risk" },
  { value: "moderate", label: "Moderate risk" },
  { value: "high", label: "High risk" },
  { value: "critical", label: "Critical risk" },
];

export const RISK_ROAD_CONDITIONS: Option[] = [
  { value: "all", label: "Any road condition" },
  { value: "dry", label: "Dry surface" },
  { value: "wet", label: "Wet surface" },
  { value: "damaged", label: "Poor surface condition" },
  { value: "works", label: "Under construction" },
  { value: "other", label: "Other or unrecorded" },
];

export const RISK_WEATHER: Option[] = [
  { value: "all", label: "Any weather" },
  { value: "clear", label: "Clear" },
  { value: "rain", label: "Rain" },
  { value: "fog", label: "Fog" },
  { value: "storm", label: "Storm or high winds" },
  { value: "other", label: "Other" },
];

export const RISK_TIME_OF_DAY: Option[] = [
  { value: "all", label: "All periods" },
  { value: "early_morning", label: "Early morning" },
  { value: "morning", label: "Morning" },
  { value: "afternoon", label: "Afternoon" },
  { value: "evening", label: "Evening" },
  { value: "night", label: "Night" },
  { value: "late_night", label: "Late night" },
];
