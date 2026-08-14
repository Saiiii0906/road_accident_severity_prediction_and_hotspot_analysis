import type { HotspotIntensity } from "@/lib/api/hotspots";
import type { Option } from "@/constants/severity";

export const HOTSPOT_INTENSITY_DISPLAY: Record<
  HotspotIntensity,
  { label: string; description: string; badgeClassName: string; dotClassName: string }
> = {
  low: {
    label: "Low",
    description: "Sparse concentration — routine monitoring.",
    badgeClassName: "border-success/30 bg-success/10 text-success",
    dotClassName: "bg-success",
  },
  moderate: {
    label: "Moderate",
    description: "Emerging concentration — review recommended.",
    badgeClassName: "border-warning/30 bg-warning/10 text-warning",
    dotClassName: "bg-warning",
  },
  high: {
    label: "High",
    description: "Dense concentration — intervention candidate.",
    badgeClassName: "border-danger/30 bg-danger/10 text-danger",
    dotClassName: "bg-danger",
  },
  critical: {
    label: "Critical",
    description: "Severe concentration — priority intervention.",
    badgeClassName: "border-danger/40 bg-danger/15 text-danger",
    dotClassName: "bg-danger",
  },
};

export const HOTSPOT_INTENSITY_ORDER: HotspotIntensity[] = ["low", "moderate", "high", "critical"];

export const HOTSPOT_REGIONS: Option[] = [
  { value: "all", label: "All regions" },
  { value: "north", label: "Northern district" },
  { value: "central", label: "City centre" },
  { value: "east", label: "Eastern district" },
  { value: "south", label: "Southern district" },
  { value: "west", label: "Western district" },
];

export const HOTSPOT_SEVERITIES: Option[] = [
  { value: "all", label: "All severity levels" },
  { value: "low", label: "Low" },
  { value: "moderate", label: "Moderate" },
  { value: "high", label: "High" },
  { value: "critical", label: "Critical" },
];

export const HOTSPOT_PERIODS: Option[] = [
  { value: "last_30_days", label: "Last 30 days" },
  { value: "last_6_months", label: "Last 6 months" },
  { value: "last_12_months", label: "Last 12 months" },
  { value: "last_3_years", label: "Last 3 years" },
];

export const HOTSPOT_DENSITIES: Option[] = [
  { value: "all", label: "Any density" },
  { value: "low", label: "Low density" },
  { value: "medium", label: "Medium density" },
  { value: "high", label: "High density" },
];

export const HOTSPOT_WEATHER: Option[] = [
  { value: "all", label: "Any weather" },
  { value: "clear", label: "Clear" },
  { value: "rain", label: "Rain" },
  { value: "fog", label: "Fog or mist" },
  { value: "snow", label: "Snow or ice" },
];

export const HOTSPOT_ROAD_CONDITIONS: Option[] = [
  { value: "all", label: "Any road condition" },
  { value: "dry", label: "Dry surface" },
  { value: "wet", label: "Wet surface" },
  { value: "damaged", label: "Surface defects" },
  { value: "works", label: "Roadworks" },
];
