/**
 * Minimal typed HTTP abstraction for the FastAPI backend.
 * UI components must never call fetch directly — they go through the service
 * modules in this folder.
 *
 * Configuration:
 * - Set VITE_API_BASE_URL in your .env file to point at the backend service.
 * - Example: VITE_API_BASE_URL=http://localhost:8000
 * - If not set, the client will throw a typed ApiError with code "api_not_configured".
 */

interface DshBoot {
  apiBaseUrl?: string;
}

declare global {
  interface Window {
    __DSH_BOOT__?: DshBoot;
  }
}

export class ApiError extends Error {
  readonly status: number | undefined;
  readonly code: string;

  constructor(message: string, options: { status?: number; code?: string } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = options.status;
    this.code = options.code ?? "request_failed";
  }
}

/**
 * Backend base URL, e.g. "https://api.example.com".
 * Reads from the VITE_API_BASE_URL environment variable.
 * Returns undefined if not set.
 */
export function getApiBaseUrl(): string | undefined {
  // Check for environment variable first
  const envValue = import.meta.env?.["VITE_API_BASE_URL"];
  if (typeof envValue === "string" && envValue.length > 0) {
    return envValue.replace(/\/$/, "");
  }

  // Fallback to runtime configuration injected via window.__DSH_BOOT__
  const runtimeValue = window.__DSH_BOOT__?.apiBaseUrl;
  if (typeof runtimeValue === "string" && runtimeValue.length > 0) {
    return runtimeValue.replace(/\/$/, "");
  }

  return undefined;
}

/**
 * Check whether the API is configured and reachable.
 * @returns true if a base URL is configured.
 */
export function isApiConfigured(): boolean {
  return getApiBaseUrl() !== undefined;
}

/**
 * Default request options
 */
const DEFAULT_OPTIONS: RequestInit = {
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
};

/**
 * Type for query parameters
 */
export type QueryParams = Record<string, string | number | boolean | undefined>;

/**
 * Build a query string from an object of parameters.
 * @param params - Object of query parameters
 * @returns URL-encoded query string (without leading ?)
 */
export function buildQueryString(params: QueryParams): string {
  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) {
      searchParams.append(key, String(value));
    }
  }
  return searchParams.toString();
}

/**
 * Make an authenticated request to the API.
 *
 * @template TResponse - The expected response type
 * @param path - The API endpoint path (relative to the base URL)
 * @param init - Request options including method, body, signal, and optional query params
 * @returns The parsed JSON response
 * @throws {ApiError} If the API is not configured, the request fails, or the response is invalid
 */
export async function apiRequest<TResponse = unknown>(
  path: string,
  init: {
    method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
    body?: unknown;
    signal?: AbortSignal;
    query?: QueryParams;
    headers?: Record<string, string>;
  } = {},
): Promise<TResponse> {
  const baseUrl = getApiBaseUrl();

  if (!baseUrl) {
    throw new ApiError("The backend service is not connected to this environment yet.", {
      code: "api_not_configured",
      status: 503,
    });
  }

  // Build the full URL with query parameters
  let url = `${baseUrl}${path}`;
  if (init.query && Object.keys(init.query).length > 0) {
    const queryString = buildQueryString(init.query);
    if (queryString) {
      url += `?${queryString}`;
    }
  }

  // Merge headers
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
    ...init.headers,
  };

  const requestInit: RequestInit = {
    method: init.method ?? "GET",
    headers,
    signal: init.signal ?? null,
    ...DEFAULT_OPTIONS,
  };

  if (init.body !== undefined) {
    requestInit.body = JSON.stringify(init.body);
  }

  let response: Response;
  try {
    response = await fetch(url, requestInit);
  } catch (networkError) {
    logger.error("Network error", networkError);
    throw new ApiError("The backend service could not be reached.", {
      code: "network_error",
      status: 503,
    });
  }

  if (!response.ok) {
    let errorMessage = `The backend service returned an error (${response.status}).`;
    try {
      const errorBody = await response.json();
      if (typeof errorBody?.detail === "string") {
        errorMessage = errorBody.detail;
      } else if (Array.isArray(errorBody?.detail) && errorBody.detail.length > 0) {
        errorMessage = errorBody.detail[0]?.msg || errorMessage;
      }
    } catch {
      // Response wasn't JSON, use default message
    }

    throw new ApiError(errorMessage, {
      status: response.status,
      code: "http_error",
    });
  }

  // Check for empty response (e.g., 204 No Content)
  const contentLength = response.headers.get("content-length");
  if (contentLength === "0") {
    return undefined as TResponse;
  }

  try {
    return (await response.json()) as TResponse;
  } catch {
    throw new ApiError("The backend service returned an unreadable response.", {
      code: "invalid_response",
      status: 502,
    });
  }
}

// Lightweight logger to avoid circular dependencies
const logger = {
  error: (...args: unknown[]) => console.error("[API]", ...args),
  warn: (...args: unknown[]) => console.warn("[API]", ...args),
  debug: (...args: unknown[]) => console.debug("[API]", ...args),
};
