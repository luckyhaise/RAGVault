import { API_BASE_URL } from "../config";
import { tokenStore } from "./tokenStore";
import type { RefreshTokenResponse } from "../types/auth_types";

/**
 * Normalized error raised for any non-2xx response. The backend always wraps
 * failures as `{ error: { code, error_code?, message } }`, so we surface a
 * human-readable `message` plus the machine-readable fields when present.
 */
export class ApiError extends Error {
  readonly status: number;
  readonly code?: string | number;
  readonly errorCode?: string;

  constructor(
    message: string,
    status: number,
    code?: string | number,
    errorCode?: string,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.errorCode = errorCode;
  }
}

export type AuthMode = "access" | "refresh" | "none";

export interface RequestOptions {
  /** Path relative to the API base, e.g. `/user/login`. */
  path: string;
  method?: "GET" | "POST";
  /** JSON body (ignored when `formData` is set). */
  body?: unknown;
  /** Multipart body; sets the correct boundary automatically. */
  formData?: FormData;
  /** Which bearer token to attach. Defaults to the access token. */
  auth?: AuthMode;
  /** Extra query parameters. */
  query?: Record<string, string | undefined>;
  signal?: AbortSignal;
}

const REFRESH_PATH = "/user/refresh-token";

function buildUrl(path: string, query?: RequestOptions["query"]): string {
  const url = new URL(`${API_BASE_URL}${path}`);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined) url.searchParams.set(key, value);
    }
  }
  return url.toString();
}

async function toApiError(response: Response): Promise<ApiError> {
  let message = `Request failed (${response.status})`;
  let code: string | number | undefined;
  let errorCode: string | undefined;

  try {
    const data: unknown = await response.json();
    const envelope = (data as { error?: unknown })?.error;
    if (envelope && typeof envelope === "object") {
      const err = envelope as {
        code?: string | number;
        error_code?: string;
        message?: string;
      };
      if (typeof err.message === "string" && err.message.length > 0) {
        message = err.message;
      }
      code = err.code;
      errorCode = err.error_code;
    } else {
      const detail = (data as { detail?: unknown })?.detail;
      if (typeof detail === "string") message = detail;
    }
  } catch {
    // Body was empty or not JSON; keep the generic message.
  }

  return new ApiError(message, response.status, code, errorCode);
}

// A single in-flight refresh shared by all concurrent 401s, so a burst of
// requests only triggers one token rotation.
let refreshInFlight: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const refresh = tokenStore.getRefreshToken();
  if (!refresh) {
    throw new ApiError("Your session has expired. Please sign in again.", 401);
  }

  const response = await fetch(buildUrl(REFRESH_PATH), {
    method: "POST",
    headers: { Authorization: `Bearer ${refresh}` },
  });

  if (!response.ok) {
    tokenStore.clear();
    throw await toApiError(response);
  }

  const data = (await response.json()) as RefreshTokenResponse;
  tokenStore.setTokens(data.access_token, data.refresh_token);
  return data.access_token;
}

function ensureFreshAccessToken(): Promise<string> {
  if (!refreshInFlight) {
    refreshInFlight = refreshAccessToken().finally(() => {
      refreshInFlight = null;
    });
  }
  return refreshInFlight;
}

async function send<T>(
  options: RequestOptions,
  allowRefreshRetry: boolean,
): Promise<T> {
  const { path, method = "POST", body, formData, auth = "access", query } = options;

  const headers = new Headers();
  if (!formData && body !== undefined) {
    headers.set("Content-Type", "application/json");
  }

  if (auth !== "none") {
    const token =
      auth === "refresh"
        ? tokenStore.getRefreshToken()
        : tokenStore.getAccessToken();
    if (!token) {
      throw new ApiError("You are not signed in.", 401);
    }
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(buildUrl(path, query), {
    method,
    headers,
    body: formData ?? (body !== undefined ? JSON.stringify(body) : undefined),
    signal: options.signal,
  });

  // Access tokens are short-lived; transparently refresh once and retry.
  if (response.status === 401 && auth === "access" && allowRefreshRetry) {
    try {
      await ensureFreshAccessToken();
    } catch (error) {
      tokenStore.clear();
      throw error;
    }
    return send<T>(options, false);
  }

  if (!response.ok) {
    throw await toApiError(response);
  }

  if (response.status === 204) return undefined as unknown as T;

  const text = await response.text();
  if (text.length === 0) return undefined as unknown as T;
  return JSON.parse(text) as T;
}

/** Perform an authenticated API request with automatic token refresh. */
export function request<T>(options: RequestOptions): Promise<T> {
  return send<T>(options, true);
}
