/**
 * Journey Safety Analysis API client.
 *
 * Exposes the POST /api/journey/analyze endpoint to the frontend.
 */

import { apiRequest } from "./client";

export type DataAvailabilityStatus = "pending" | "available" | "partial" | "unavailable";

export interface JourneyAnalyzeRequest {
  source: string;
  destination: string;
  travel_date: string; // YYYY-MM-DD
  travel_time: string; // HH:MM
}

export interface JourneyDetails {
  source: string;
  destination: string;
  travel_date: string;
  travel_time: string;
}

export interface RouteSegment {
  segment_id?: string | null;
  name?: string | null;
  length_km?: number | null;
}

export interface GeocodedLocation {
  latitude: number;
  longitude: number;
  display_name: string;
}

export interface RouteGeometry {
  type: string;
  coordinates: [number, number][];
}

export interface RouteInfo {
  status: DataAvailabilityStatus;
  source?: GeocodedLocation | null;
  destination?: GeocodedLocation | null;
  distance_km?: number | null;
  duration_minutes?: number | null;
  geometry?: RouteGeometry | null;
  provider?: string | null;
  segments: RouteSegment[];
}

export type ProviderCoverageStatus =
  | "provider_supported"
  | "provider_partially_supported"
  | "provider_unsupported_for_geography"
  | "provider_failed"
  | "provider_returned_no_results"
  | "provider_not_configured";

export interface TrafficContext {
  status?: DataAvailabilityStatus | null;
  coverage_status?: ProviderCoverageStatus | null;
  congestion_level?: string | null;
  delay_minutes?: number | null;
  description?: string | null;
  corridor_monitored?: string | null;
}

export interface WeatherContext {
  status?: DataAvailabilityStatus | null;
  coverage_status?: ProviderCoverageStatus | null;
  condition?: string | null;
  temperature_c?: number | null;
  precipitation_probability?: number | null;
  precipitation_mm?: number | null;
  wind_speed_kmh?: number | null;
  visibility?: string | null;
  precipitation_risk?: string | null;
  queried_time?: string | null;
  location_name?: string | null;
}

export interface IncidentContext {
  incident_id: string;
  description: string;
  severity?: string | null;
  category?: string | null;
  location?: string | null;
}

export interface LiveContextProviders {
  weather?: string | null;
  traffic?: string | null;
  incidents?: string | null;
}

export interface LiveContext {
  status: DataAvailabilityStatus;
  weather?: WeatherContext | null;
  traffic?: TrafficContext | null;
  incidents: IncidentContext[];
  incidents_status?: DataAvailabilityStatus | null;
  incidents_coverage?: ProviderCoverageStatus | null;
  incidents_description?: string | null;
  providers?: LiveContextProviders | null;
}

export interface MatchedHotspot {
  cluster_id: number;
  latitude: number;
  longitude: number;
  total_accidents: number;
  fatal_count: number;
  serious_count: number;
  slight_count: number;
  dominant_severity?: string | null;
  dominant_weather?: string | null;
  dominant_road_type?: string | null;
  average_speed?: number | null;
  average_casualties?: number | null;
  peak_hour?: number | null;
  distance_to_route_m: number;
}

export interface MatchedSegment {
  edge_id: number;
  road_number: number;
  start_lat: number;
  start_lon: number;
  end_lat: number;
  end_lon: number;
  predicted_risk: number;
  risk_category: string;
  distance_to_route_m: number;
}

export interface HistoricalSeverityEvidence {
  status?: DataAvailabilityStatus | null;
  predicted_severity?: string | null;
  confidence?: number | null;
  probabilities?: Record<string, number> | null;
  reason?: string | null;
}

export interface HistoricalHotspotEvidence {
  status?: DataAvailabilityStatus | null;
  hotspots_on_route: number;
  total_historical_accidents?: number | null;
  cluster_ids: string[];
  highest_cluster_density?: number | null;
  matched_hotspots: MatchedHotspot[];
  description?: string | null;
}

export interface HistoricalRiskEvidence {
  status?: DataAvailabilityStatus | null;
  segments_on_route: number;
  critical_segments_count: number;
  high_risk_segments_count: number;
  average_gnn_risk?: number | null;
  peak_gnn_risk?: number | null;
  high_risk_corridors: string[];
  matched_segments: MatchedSegment[];
  description?: string | null;
}

export interface HistoricalCoverage {
  supported: boolean;
  status: DataAvailabilityStatus;
  region: string;
  reason?: string | null;
}

export interface CorridorMatchingMetadata {
  corridor_radius_m: number;
  method: string;
  route_waypoints_count: number;
}

export interface HistoricalEvidence {
  status: DataAvailabilityStatus;
  coverage?: HistoricalCoverage | null;
  matching?: CorridorMatchingMetadata | null;
  student_a?: HistoricalSeverityEvidence | null;
  student_b?: HistoricalHotspotEvidence | null;
  student_c?: HistoricalRiskEvidence | null;
  summary?: string | null;
}

export interface SafetyKeyFactor {
  factor: string;
  title: string;
  severity: string;
  description: string;
  source: string;
}

export interface SafetyEvidenceItem {
  source: string;
  metric: string;
  value: string;
  interpretation: string;
}

export interface SafetyDataCoverage {
  route: DataAvailabilityStatus;
  weather: DataAvailabilityStatus;
  traffic: DataAvailabilityStatus;
  incidents: DataAvailabilityStatus;
  historical: DataAvailabilityStatus;
}

export interface SafetyAssessment {
  status: DataAvailabilityStatus;
  overall_score?: number | null;
  level?: string | null;
  summary?: string | null;
  key_factors: SafetyKeyFactor[];
  supporting_evidence: SafetyEvidenceItem[];
  data_coverage?: SafetyDataCoverage | null;
  limitations: string[];
}

export type LLMKeyFindingSeverity = "critical" | "high" | "moderate" | "low" | "unknown";

export interface LLMKeyFinding {
  title: string;
  description: string;
  severity: LLMKeyFindingSeverity;
  evidence_sources: string[];
}

export interface LLMRecommendation {
  action: string;
  reason: string;
  evidence_sources: string[];
}

export interface LLMSynthesis {
  status: DataAvailabilityStatus;
  headline?: string | null;
  summary?: string | null;
  key_findings: LLMKeyFinding[];
  recommendations: LLMRecommendation[];
  limitations: string[];
}

export interface JourneyProvenance {
  route_provider?: string | null;
  weather_provider?: string | null;
  traffic_provider?: string | null;
  incident_provider?: string | null;
  traffic_coverage_status?: ProviderCoverageStatus | null;
  incident_coverage_status?: ProviderCoverageStatus | null;
  weather_coverage_status?: ProviderCoverageStatus | null;
  traffic_queried?: boolean;
  incident_queried?: boolean;
  weather_queried?: boolean;
  live_data_available: boolean;
  historical_data_available: boolean;
  historical_coverage_region?: string | null;
  corridor_radius_m?: number | null;
  matched_hotspots_count: number;
  matched_segments_count: number;
  student_a_used: boolean;
  student_b_used: boolean;
  student_c_used: boolean;
  gemini_used: boolean;
  analysis_timestamp: string;
}

export interface JourneyAnalyzeResponse {
  journey: JourneyDetails;
  route: RouteInfo;
  live_context: LiveContext;
  historical_evidence: HistoricalEvidence;
  safety_assessment: SafetyAssessment;
  llm_synthesis: LLMSynthesis;
  provenance: JourneyProvenance;
}

/**
 * Submit a journey request for multi-source safety analysis.
 */
export async function analyzeJourney(
  request: JourneyAnalyzeRequest,
): Promise<JourneyAnalyzeResponse> {
  return apiRequest<JourneyAnalyzeResponse>("/api/journey/analyze", {
    method: "POST",
    body: request,
  });
}
