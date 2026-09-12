// Central place for environment-driven frontend configuration.

function normalizeBaseUrl(raw: string): string {
  return raw.endsWith("/") ? raw.slice(0, -1) : raw;
}

export const API_BASE_URL = normalizeBaseUrl(
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
    "http://localhost:8000/api/v1",
);

// Keys used to persist the session across reloads.
export const ACCESS_TOKEN_KEY = "ragvault.access_token";
export const REFRESH_TOKEN_KEY = "ragvault.refresh_token";
export const SESSION_USER_KEY = "ragvault.session_user";

// Backend upload limits (kept in sync with upload_file_validation.py).
export const MAX_UPLOAD_BYTES = 50 * 1024 * 1024;
export const ALLOWED_UPLOAD_MIME_TYPES = [
  "text/plain",
  "text/csv",
  "text/markdown",
] as const;
export const ALLOWED_UPLOAD_EXTENSIONS = [".txt", ".csv", ".md"] as const;

export const DEFAULT_PAGE_SIZE = 10;
export const DOCUMENT_TEXT_PAGE_SIZE = 5000;
