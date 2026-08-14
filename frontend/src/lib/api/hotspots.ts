/**
 * Hotspot Explorer service boundary.
 *
 * The FastAPI contract for hotspot analysis is NOT published yet, so this module
 * is intentionally provisional: types describe what the UI needs, and the loader
 * currently resolves from an isolated demo dataset (`@/lib/mock/hotspots`).
 *
 * TODO(backend): replace `loadHotspots` internals with `apiRequest` against the
 * real endpoint and map the payload here. No UI component should change.
 */

import { DEMO_HOTSPOTS, DEMO_SUMMARY } from "@/lib/mock/hotspots";

/** Visualization-only intensity categories. Not a statistical claim. */
export type HotspotIntensity = "low" | "moderate" | "high" | "critical";

export interface HotspotFilters {
  region: string;
  severity: string;
  period: string;
  density: string;
  weather: string;
  roadCondition: string;
}

export interface Hotspot {
  id: string;
  /** Human-readable placeholder location label (demo data). */
  location: string;
  region: string;
  intensity: HotspotIntensity;
  /** Normalised map position (0–1) within the map surface. */
  x: number;
  y: number;
  accidentCount: number;
  severeAccidentCount: number;
  riskLevel: string;
  dominantConditions: string[];
  recommendedIntervention: string;
}

export interface HotspotSummary {
  totalHotspots: number;
  highRiskHotspots: number;
  severeConcentration: string;
  mostAffectedArea: string;
}

export interface HotspotDataset {
  hotspots: Hotspot[];
  summary: HotspotSummary;
}

export const DEFAULT_HOTSPOT_FILTERS: HotspotFilters = {
  region: "all",
  severity: "all",
  period: "last_12_months",
  density: "all",
  weather: "all",
  roadCondition: "all",
};

/**
 * Frontend-stage loader. Filtering is applied client-side over demo data purely
 * so the workspace is interactive; the backend will own this later.
 */
export async function loadHotspots(filters: HotspotFilters): Promise<HotspotDataset> {
  await new Promise((resolve) => setTimeout(resolve, 650));

  const hotspots = DEMO_HOTSPOTS.filter((hotspot) => {
    if (filters.region !== "all" && hotspot.region !== filters.region) return false;
    if (filters.severity !== "all" && hotspot.intensity !== filters.severity) return false;
    if (filters.density !== "all" && densityBucket(hotspot) !== filters.density) return false;
    if (
      filters.weather !== "all" &&
      !hotspot.dominantConditions.includes(WEATHER_TAGS[filters.weather] ?? "")
    ) {
      return false;
    }
    if (
      filters.roadCondition !== "all" &&
      !hotspot.dominantConditions.includes(ROAD_TAGS[filters.roadCondition] ?? "")
    ) {
      return false;
    }
    return true;
  });

  const highRisk = hotspots.filter((h) => h.intensity === "high" || h.intensity === "critical");

  return {
    hotspots,
    summary:
      hotspots.length === 0
        ? { totalHotspots: 0, highRiskHotspots: 0, severeConcentration: "—", mostAffectedArea: "—" }
        : {
            ...DEMO_SUMMARY,
            totalHotspots: hotspots.length,
            highRiskHotspots: highRisk.length,
            mostAffectedArea:
              [...hotspots].sort((a, b) => b.severeAccidentCount - a.severeAccidentCount)[0]
                ?.location ?? "—",
          },
  };
}

function densityBucket(hotspot: Hotspot): string {
  if (hotspot.accidentCount >= 240) return "high";
  if (hotspot.accidentCount >= 120) return "medium";
  return "low";
}

const WEATHER_TAGS: Record<string, string> = {
  clear: "Clear weather",
  rain: "Rainfall",
  fog: "Fog or mist",
  snow: "Snow or ice",
};

const ROAD_TAGS: Record<string, string> = {
  dry: "Dry surface",
  wet: "Wet surface",
  damaged: "Surface defects",
  works: "Roadworks",
};
