/**
 * Hotspot Explorer service boundary.
 *
 * Connected to FastAPI backend endpoint POST /api/hotspots/analyze,
 * querying precomputed Student B DBSCAN hotspot clusters.
 */

import { apiRequest } from "@/lib/api/client";

export const HOTSPOTS_ENDPOINT = "/api/hotspots/analyze";

/** Visualization-only intensity categories based on accident density. */
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
  location: string;
  region: string;
  intensity: HotspotIntensity;
  latitude: number;
  longitude: number;
  /** Normalised map position (0–1) within the UK bounding box. */
  x: number;
  y: number;
  accidentCount: number;
  severeAccidentCount: number;
  fatalAccidentCount: number;
  seriousAccidentCount: number;
  slightAccidentCount: number;
  dominantSeverity: string;
  dominantWeather: string;
  dominantRoadType: string;
  averageSpeed: number;
  averageCasualties: number;
  peakHour: number;
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
  period: "all",
  density: "all",
  weather: "all",
  roadCondition: "all",
};

/** Raw backend schemas matching backend/app/schemas/hotspot.py */
interface BackendHotspotCluster {
  cluster_id: string;
  center: {
    latitude: number;
    longitude: number;
  };
  radius_meters: number;
  accident_count: number;
  severity_breakdown: {
    slight: number;
    serious: number;
    fatal: number;
  };
  dominant_severity?: string;
  dominant_weather?: string;
  dominant_road_type?: string;
  average_speed?: number;
  average_casualties?: number;
  peak_hour?: number;
  dominant_contributing_factor?: string;
}

interface BackendHotspotResponse {
  clusters: BackendHotspotCluster[];
  total_accidents_considered: number;
  total_hotspots_in_area?: number;
  generated_at: string;
}

// UK Mainland Bounding Box for schematic coordinate normalization
const UK_MIN_LAT = 49.9;
const UK_MAX_LAT = 60.8;
const UK_MIN_LON = -7.6;
const UK_MAX_LON = 1.8;

function toIntensity(accidentCount: number): HotspotIntensity {
  if (accidentCount >= 2000) return "critical";
  if (accidentCount >= 500) return "high";
  if (accidentCount >= 100) return "moderate";
  return "low";
}

function deriveRegion(lat: number, lon: number): string {
  if (lat >= 55.0) return "north";
  if (lat >= 53.0) return "central";
  if (lon < -2.5) return "west";
  if (lon > 0.0) return "east";
  return "south";
}

function deriveIntervention(roadType: string, avgSpeed: number): string {
  if (avgSpeed >= 50) {
    return "Speed management enforcement and roadside barrier integrity inspection.";
  }
  if (roadType.toLowerCase().includes("roundabout")) {
    return "Roundabout lane markings refresh and approach geometry review.";
  }
  if (roadType.toLowerCase().includes("dual")) {
    return "Grade separation review and central reservation lighting assessment.";
  }
  return "Targeted junction safety review, high-friction anti-skid resurfacing, and visibility clearance.";
}

function mapClusterToHotspot(cluster: BackendHotspotCluster): Hotspot {
  const lat = cluster.center.latitude;
  const lon = cluster.center.longitude;

  // Normalized 0-1 canvas coordinates with margin padding
  const normX = Math.max(0.04, Math.min(0.96, (lon - UK_MIN_LON) / (UK_MAX_LON - UK_MIN_LON)));
  const normY = Math.max(0.04, Math.min(0.96, (UK_MAX_LAT - lat) / (UK_MAX_LAT - UK_MIN_LAT)));

  const fatalCount = cluster.severity_breakdown.fatal || 0;
  const seriousCount = cluster.severity_breakdown.serious || 0;
  const slightCount = cluster.severity_breakdown.slight || 0;
  const severeAccidents = fatalCount + seriousCount;

  const clusterNum = cluster.cluster_id.replace("cluster-", "");
  const lonFormatted = `${Math.abs(lon).toFixed(3)}°${lon < 0 ? "W" : "E"}`;
  const locationLabel = `Cluster #${clusterNum} · (${lat.toFixed(3)}°N, ${lonFormatted})`;

  const conditions: string[] = [];
  if (cluster.dominant_road_type) conditions.push(cluster.dominant_road_type);
  if (cluster.dominant_weather) conditions.push(cluster.dominant_weather);
  if (cluster.peak_hour !== undefined) conditions.push(`Peak: ${cluster.peak_hour}:00`);

  const riskLabel =
    fatalCount >= 50
      ? "Priority Intervention Zone"
      : severeAccidents >= 100
        ? "High Severe Risk Corridor"
        : "Standard Monitoring Hotspot";

  return {
    id: cluster.cluster_id,
    location: locationLabel,
    region: deriveRegion(lat, lon),
    intensity: toIntensity(cluster.accident_count),
    latitude: lat,
    longitude: lon,
    x: normX,
    y: normY,
    accidentCount: cluster.accident_count,
    severeAccidentCount: severeAccidents,
    fatalAccidentCount: fatalCount,
    seriousAccidentCount: seriousCount,
    slightAccidentCount: slightCount,
    dominantSeverity: cluster.dominant_severity || "Slight",
    dominantWeather: cluster.dominant_weather || "Unknown",
    dominantRoadType: cluster.dominant_road_type || "Unknown",
    averageSpeed: cluster.average_speed ?? 0,
    averageCasualties: cluster.average_casualties ?? 1,
    peakHour: cluster.peak_hour ?? 17,
    riskLevel: riskLabel,
    dominantConditions: conditions,
    recommendedIntervention: deriveIntervention(
      cluster.dominant_road_type || "",
      cluster.average_speed ?? 0,
    ),
  };
}

/**
 * Load real DBSCAN accident hotspots from backend API.
 */
export async function loadHotspots(
  filters: HotspotFilters,
  signal?: AbortSignal,
): Promise<HotspotDataset> {
  const requestPayload: Record<string, unknown> = {
    min_lat: 49.5,
    max_lat: 61.0,
    min_lon: -8.5,
    max_lon: 2.0,
    limit: 150,
  };

  if (filters.severity === "fatal") {
    requestPayload.min_severity = "fatal";
  } else if (filters.severity === "high" || filters.severity === "critical") {
    requestPayload.min_severity = "serious";
  }

  const response = await apiRequest<BackendHotspotResponse>(HOTSPOTS_ENDPOINT, {
    method: "POST",
    body: requestPayload,
    ...(signal && { signal }),
  });

  const allHotspots = (response.clusters || []).map(mapClusterToHotspot);

  // Apply frontend filters (region, weather, road condition)
  const filtered = allHotspots.filter((hotspot) => {
    if (filters.region !== "all" && hotspot.region !== filters.region) return false;
    if (filters.severity !== "all" && hotspot.intensity !== filters.severity) return false;
    if (filters.density !== "all") {
      const bucket =
        hotspot.accidentCount >= 500 ? "high" : hotspot.accidentCount >= 100 ? "medium" : "low";
      if (bucket !== filters.density) return false;
    }
    if (filters.weather !== "all") {
      const wLower = hotspot.dominantWeather.toLowerCase();
      if (filters.weather === "rain" && !wLower.includes("rain")) return false;
      if (filters.weather === "fog" && !wLower.includes("fog")) return false;
      if (filters.weather === "snow" && !wLower.includes("snow")) return false;
      if (filters.weather === "clear" && !wLower.includes("fine")) return false;
    }
    if (filters.roadCondition !== "all") {
      const rLower = hotspot.dominantRoadType.toLowerCase();
      if (filters.roadCondition === "single" && !rLower.includes("single")) return false;
      if (filters.roadCondition === "dual" && !rLower.includes("dual")) return false;
      if (filters.roadCondition === "roundabout" && !rLower.includes("roundabout")) return false;
    }
    return true;
  });

  const totalAccidents = filtered.reduce((acc, h) => acc + h.accidentCount, 0);
  const totalSevere = filtered.reduce((acc, h) => acc + h.severeAccidentCount, 0);
  const highRiskCount = filtered.filter(
    (h) => h.intensity === "high" || h.intensity === "critical",
  ).length;

  const topArea =
    filtered.length > 0
      ? [...filtered].sort((a, b) => b.accidentCount - a.accidentCount)[0].location
      : "—";
  const severeShare =
    totalAccidents > 0 ? `${Math.round((totalSevere / totalAccidents) * 100)}% of accidents` : "—";

  return {
    hotspots: filtered,
    summary: {
      totalHotspots: filtered.length,
      highRiskHotspots: highRiskCount,
      severeConcentration: severeShare,
      mostAffectedArea: topArea,
    },
  };
}
