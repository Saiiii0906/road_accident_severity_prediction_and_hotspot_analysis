import { apiRequest } from "@/lib/api/client";

/**
 * Severity prediction service.
 *
 * The FastAPI contract is defined in backend/app/schemas/severity.py. When the real
 * schema is updated, update ONLY this file (and the mapper below) — no UI changes needed.
 */

export const SEVERITY_ENDPOINT = "/api/severity/predict";

/**
 * UI-facing severity categories matching Student A's real model classes.
 */
export type SeverityLevel = "slight" | "serious" | "fatal";

export interface SeverityPredictionRequest {
  accident_date?: string; // ISO date (YYYY-MM-DD)
  accident_time?: string; // 24h HH:mm
  day_of_week?: string;
  number_of_vehicles?: number;
  vehicles_involved?: number;
  number_of_casualties?: number;
  casualties?: number;
  speed_limit?: number;
  junction_control?: string;
  junction_detail?: string;
  road_type?: string;
  traffic_density?: string;
  road_surface?: string;
  road_surface_conditions?: string;
  weather?: string;
  weather_conditions?: string;
  light_conditions?: string;
  visibility?: string;
  area_type?: string;
  urban_or_rural_area?: string;
  latitude?: number;
  longitude?: number;
}

export interface SeverityContributingFactor {
  label: string;
  /** Relative contribution 0–1, when the backend provides it. */
  weight?: number;
  direction?: "increases" | "reduces";
}

export interface SeverityPredictionResult {
  severity: SeverityLevel;
  /** 0–1 model confidence, when provided. */
  confidence?: number;
  /** Per-class probabilities, when provided. */
  probabilities?: Partial<Record<SeverityLevel, number>>;
  interpretation?: string;
  contributingFactors?: SeverityContributingFactor[];
  recommendedAction?: string;
  modelVersion?: string;
}

/**
 * Raw backend payload — matches backend/app/schemas/severity.py
 */
interface SeverityPredictionResponse {
  predicted_severity: string;
  confidence: number;
  class_probabilities: {
    severity: string;
    probability: number;
  }[];
  probabilities?: Record<string, number>;
  model_version: string;
  /** Timestamp when prediction was made */
  predicted_at?: string; // ISO datetime string
}

/**
 * Maps the internal severity levels
 */
const SEVERITY_LEVELS: SeverityLevel[] = ["slight", "serious", "fatal"];

/**
 * Convert a raw severity string from the API to a UI-facing SeverityLevel.
 * @param value - Raw severity string from API
 * @returns Validated SeverityLevel
 */
function toSeverityLevel(value: string): SeverityLevel {
  const normalised = value.trim().toLowerCase();
  if (normalised === "fatal") return "fatal";
  if (normalised === "serious") return "serious";
  return "slight";
}

/**
 * Map the raw API response to the UI-facing result structure.
 */
function mapResponse(payload: SeverityPredictionResponse): SeverityPredictionResult {
  // Convert class_probabilities array to a simple object
  const probabilities = payload.class_probabilities
    ? payload.class_probabilities.reduce<Partial<Record<SeverityLevel, number>>>(
        (acc, item) => {
          const level = toSeverityLevel(item.severity);
          acc[level] = item.probability;
          return acc;
        },
        {}
      )
    : undefined;

  // Generate contributing factors based on prediction confidence and probabilities
  const contributingFactors: SeverityContributingFactor[] = [];
  if (probabilities) {
    // Sort by probability descending to find top contributing factors
    const sortedFactors = Object.entries(probabilities)
      .map(([severity, prob]) => ({ severity, prob: prob ?? 0 }))
      .sort((a, b) => b.prob - a.prob);

    // Add top factors as contributors
    for (const { severity, prob } of sortedFactors.slice(0, 2)) {
      if (prob > 0.05) {
        contributingFactors.push({
          label: `Model estimated ${Math.round(prob * 100)}% likelihood of ${severity} injury outcome`,
          weight: prob,
          direction: prob > 0.5 ? "increases" : "reduces",
        });
      }
    }
  }

  const sevLevel = toSeverityLevel(payload.predicted_severity);

  return {
    severity: sevLevel,
    confidence: payload.confidence,
    probabilities,
    interpretation: `The Student A model predicts ${payload.predicted_severity.toUpperCase()} severity with ${Math.round(
      payload.confidence * 100
    )}% confidence based on vehicle dynamics, road layout, and environmental factors.`,
    ...(contributingFactors.length > 0 && { contributingFactors }),
    ...(payload.model_version && { modelVersion: payload.model_version }),
    recommendedAction:
      sevLevel === "fatal"
        ? "Immediate emergency multi-agency response required. Consider full road closure, air ambulance, and major crash investigation protocol."
        : sevLevel === "serious"
          ? "Urgent paramedic dispatch and local traffic diversion recommended. Monitor road conditions."
          : "Standard traffic police and incident response sufficient. Clear debris and monitor traffic flow.",
  };
}

/**
 * Predict the severity for a single accident.
 *
 * @param request - The accident conditions
 * @param signal - Optional AbortSignal for cancellation
 * @returns Prediction result including severity, confidence, and recommendations
 */
export async function predictSeverity(
  request: SeverityPredictionRequest,
  signal?: AbortSignal,
): Promise<SeverityPredictionResult> {
  const payload = await apiRequest<SeverityPredictionResponse>(SEVERITY_ENDPOINT, {
    method: "POST",
    body: request,
    ...(signal && { signal }),
  });
  return mapResponse(payload);
}

/**
 * Predict the severity for multiple accidents in batch.
 *
 * @param request - Batch of accident conditions
 * @param signal - Optional AbortSignal for cancellation
 * @returns Array of prediction results in the same order as input
 */
export async function predictSeverityBatch(
  request: SeverityPredictionRequest[],
  signal?: AbortSignal,
): Promise<SeverityPredictionResult[]> {
  const batchRequest = {
    accidents: request,
  };

  const response = await apiRequest<{ predictions: SeverityPredictionResponse[] }>(
    "/api/severity/predict-batch",
    {
      method: "POST",
      body: batchRequest,
      ...(signal && { signal }),
    }
  );

  return response.predictions.map(mapResponse);
}