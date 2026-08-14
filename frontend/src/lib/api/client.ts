/**
 * Minimal typed HTTP abstraction for the (separately developed) FastAPI backend.
 * UI components must never call fetch directly — they go through the service
 * modules in this folder.
 */

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

/** Backend base URL, e.g. "https://api.example.com". Unset until the API is live. */
export function getApiBaseUrl(): string | undefined {
  const value = import.meta.env["VITE_API_BASE_URL"];
  return typeof value === "string" && value.length > 0 ? value.replace(/\/$/, "") : undefined;
}

export function isApiConfigured(): boolean {
  return getApiBaseUrl() !== undefined;
}

export async function apiRequest<TResponse>(
  path: string,
  init: { method?: "GET" | "POST"; body?: unknown; signal?: AbortSignal } = {},
): Promise<TResponse> {
  const baseUrl = getApiBaseUrl();

  if (!baseUrl) {
    // TODO(backend): remove once VITE_API_BASE_URL points at the FastAPI service.
    throw new ApiError("The prediction service is not connected to this environment yet.", {
      code: "api_not_configured",
    });
  }

  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, {
      method: init.method ?? "GET",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      ...(init.body !== undefined && { body: JSON.stringify(init.body) }),
      ...(init.signal && { signal: init.signal }),
    });
  } catch {
    throw new ApiError("The prediction service could not be reached.", {
      code: "network_error",
    });
  }

  if (!response.ok) {
    throw new ApiError(`The prediction service returned an error (${response.status}).`, {
      status: response.status,
      code: "http_error",
    });
  }

  try {
    return (await response.json()) as TResponse;
  } catch {
    throw new ApiError("The prediction service returned an unreadable response.", {
      code: "invalid_response",
    });
  }
}
