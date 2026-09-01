/**
 * Journey Safety Analysis API client.
 *
 * Exposes the POST /api/journey/analyze endpoint to the frontend.
 */

import { apiRequest } from "./client";

export type DataAvailabilityStatus = "pending" | "available" | "unavailable";

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

export interface RouteInfo {
  status: DataAvailabilityStatus;
  distance_km?: number | null;
  duration_minutes?: number | null;
  segments: RouteSegment[];
}

export interface TrafficContext {
  congestion_level?: string | null;
  delay_minutes?: number | null;
  description?: string | null;
}

export interface WeatherContext {
  condition?: string | null;
  temperature_c?: number | null;
  visibility?: string | null;
  precipitation_risk?: string | null;
}

export interface IncidentContext {
  incident_id: string;
  description: string;
  severity?: string | null;
}

export interface LiveContext {
  status: DataAvailabilityStatus;
  traffic?: TrafficContext | null;
  weather?: WeatherContext | null;
  incidents: IncidentContext[];
}

export interface HistoricalSeverityEvidence {
  predicted_severity?: string | null;
  confidence?: number | null;
  probabilities?: Record<string, number> | null;
}

export interface HistoricalHotspotEvidence {
  hotspots_on_route: number;
  cluster_ids: string[];
  highest_cluster_density?: number | null;
}

export interface HistoricalRiskEvidence {
  critical_segments_count: number;
  average_gnn_risk?: number | null;
  high_risk_corridors: string[];
}

export interface HistoricalEvidence {
  status: DataAvailabilityStatus;
  student_a?: HistoricalSeverityEvidence | null;
  student_b?: HistoricalHotspotEvidence | null;
  student_c?: HistoricalRiskEvidence | null;
}

export interface SafetyAssessment {
  status: DataAvailabilityStatus;
  overall_score?: number | null;
  level?: string | null;
  summary?: string | null;
}

export interface LLMSynthesis {
  status: DataAvailabilityStatus;
  summary?: string | null;
  recommendations: string[];
}

export interface JourneyProvenance {
  route_provider?: string | null;
  live_data_available: boolean;
  historical_data_available: boolean;
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
