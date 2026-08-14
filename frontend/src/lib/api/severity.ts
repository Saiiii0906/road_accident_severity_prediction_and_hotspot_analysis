import { apiRequest } from "@/lib/api/client";

/**
 * Severity prediction service.
 *
 * The FastAPI contract is not published yet, so the request/response shapes below
 * are the single provisional definition used by the whole frontend. When the real
 * schema lands, update ONLY this file (and the mapper below) — no UI changes needed.
 */

export const SEVERITY_ENDPOINT = "/api/severity/predict";

/** UI-facing severity categories. Not produced by the frontend — only rendered. */
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

/** Raw backend payload — TODO(backend): confirm field names against FastAPI schemas. */
interface SeverityPredictionResponse {
  severity: string;
  confidence?: number;
  probabilities?: Record<string, number>;
  interpretation?: string;
  contributing_factors?: { label: string; weight?: number; direction?: string }[];
  recommended_action?: string;
  model_version?: string;
}

const SEVERITY_LEVELS: SeverityLevel[] = ["low", "moderate", "high", "fatal"];

function toSeverityLevel(value: string): SeverityLevel {
  const normalised = value.trim().toLowerCase();
  return SEVERITY_LEVELS.find((level) => level === normalised) ?? "moderate";
}

function mapResponse(payload: SeverityPredictionResponse): SeverityPredictionResult {
  const probabilities = payload.probabilities
    ? Object.entries(payload.probabilities).reduce<Partial<Record<SeverityLevel, number>>>(
        (acc, [key, value]) => {
          acc[toSeverityLevel(key)] = value;
          return acc;
        },
        {},
      )
    : undefined;

  return {
    severity: toSeverityLevel(payload.severity),
    ...(payload.confidence !== undefined && { confidence: payload.confidence }),
    ...(probabilities && { probabilities }),
    ...(payload.interpretation !== undefined && { interpretation: payload.interpretation }),
    ...(payload.contributing_factors && {
      contributingFactors: payload.contributing_factors.map((factor) => ({
        label: factor.label,
        ...(factor.weight !== undefined && { weight: factor.weight }),
        ...(factor.direction === "increases" || factor.direction === "reduces"
          ? { direction: factor.direction }
          : {}),
      })),
    }),
    ...(payload.recommended_action !== undefined && {
      recommendedAction: payload.recommended_action,
    }),
    ...(payload.model_version !== undefined && { modelVersion: payload.model_version }),
  };
}

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
