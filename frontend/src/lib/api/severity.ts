import { apiRequest } from "@/lib/api/client";

/**
 * Severity prediction service.
 *
 * The FastAPI contract is defined in backend/app/schemas/severity.py. When the real
 * schema is updated, update ONLY this file (and the mapper below) — no UI changes needed.
 */

export const SEVERITY_ENDPOINT = "/api/severity/predict";

/**
 * UI-facing severity categories. Not produced by the frontend — only rendered.
 */
export type SeverityLevel = "low" | "moderate" | "high" | "fatal";

export interface SeverityPredictionRequest {
  accident_date: string; // ISO date (YYYY-MM-DD)
  accident_time: string; // 24h HH:mm
  day_of_week: string;
  vehicles_involved: number;
  casualties: number;
  speed_limit: number;
  junction_control: string;
  road_type: string;
  traffic_density: string;
  road_surface: string;
  weather: string;
  light_conditions: string;
  visibility: string;
  area_type: string;
  latitude: number;
  longitude: number;
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
  model_version: string;
  /** Timestamp when prediction was made */
  predicted_at?: string; // ISO datetime string
}

/**
 * Maps the internal severity levels to human-readable strings
 */
const SEVERITY_LEVELS: SeverityLevel[] = ["low", "moderate", "high", "fatal"];

/**
 * Convert a raw severity string from the API to a UI-facing SeverityLevel.
 * @param value - Raw severity string from API
 * @returns Validated SeverityLevel or "moderate" as fallback
 */
function toSeverityLevel(value: string): SeverityLevel {
  const normalised = value.trim().toLowerCase();
  return SEVERITY_LEVELS.find((level) => level === normalised) ?? "moderate";
}

/**
 * Map the raw API response to the UI-facing result structure.
 */
function mapResponse(payload: SeverityPredictionResponse): SeverityPredictionResult {
  // Convert class_probabilities array to a simple object for easier consumption
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
      .map(([severity, prob]) => ({ severity, prob }))
      .sort((a, b) => b.prob - a.prob);

    // Add top 2 factors as contributors
    for (const [, { severity, prob }] of sortedFactors.slice(0, 2)) {
      contributingFactors.push({
        label: `Model predicts ${severity} severity`,
        weight: prob,
        direction: prob > 0.5 ? "increases" : "reduces",
      });
    }
  }

  return {
    severity: toSeverityLevel(payload.predicted_severity),
    confidence: payload.confidence,
    probabilities,
    interpretation: `The model predicts ${payload.predicted_severity} severity with ${Math.round(
      payload.confidence * 100
    )}% confidence.`,
    ...(contributingFactors.length > 0 && { contributingFactors }),
    ...(payload.model_version && { modelVersion: payload.model_version }),
    recommendedAction:
      payload.predicted_severity === "fatal"
        ? "Immediate emergency response required. Consider road closure and diversion."
        : payload.predicted_severity === "high"
          ? "Increased police presence and traffic monitoring recommended."
          : payload.predicted_severity === "moderate"
            ? "Standard accident response procedures sufficient."
            : "Monitor situation and provide routine assistance.",
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
  // Convert to backend batch format
  const batchRequest = {
    accidents: request.map((req) => ({
      ...req,
      // Convert flat fields to nested objects expected by backend
      location: {
        latitude: 0, // Default - in real app would come from form/map
        longitude: 0,
      },
      occurred_at: new Date(`${req.accident_date}T${req.accient_time}:00Z`).toISOString(),
    })),
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