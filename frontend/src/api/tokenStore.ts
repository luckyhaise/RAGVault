import {
  ACCESS_TOKEN_KEY,
  REFRESH_TOKEN_KEY,
  SESSION_USER_KEY,
} from "../config";
import type { SessionUser } from "../types/auth_types";

// A tiny observable store for the session, backed by localStorage so a reload
// keeps the user signed in. Keeping reads in memory avoids localStorage
// round-trips on every request.

function readStorage(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeStorage(key: string, value: string | null): void {
  try {
    if (value === null) {
      window.localStorage.removeItem(key);
    } else {
      window.localStorage.setItem(key, value);
    }
  } catch {
    // Storage can be unavailable (private mode / quota); the in-memory value
    // still keeps the current tab working.
  }
}

let accessToken: string | null = readStorage(ACCESS_TOKEN_KEY);
let refreshToken: string | null = readStorage(REFRESH_TOKEN_KEY);
let sessionUser: SessionUser | null = parseUser(readStorage(SESSION_USER_KEY));

function parseUser(raw: string | null): SessionUser | null {
  if (!raw) return null;
  try {
    return JSON.parse(raw) as SessionUser;
  } catch {
    return null;
  }
}

const listeners = new Set<() => void>();

function emit(): void {
  for (const listener of listeners) listener();
}

export const tokenStore = {
  getAccessToken(): string | null {
    return accessToken;
  },

  getRefreshToken(): string | null {
    return refreshToken;
  },

  getUser(): SessionUser | null {
    return sessionUser;
  },

  /**
   * Persist a fresh token pair. A `null`/`undefined` refresh token means the
   * backend chose not to rotate it, so the existing one is preserved.
   */
  setTokens(access: string, refresh?: string | null): void {
    accessToken = access;
    writeStorage(ACCESS_TOKEN_KEY, access);

    if (refresh !== undefined && refresh !== null) {
      refreshToken = refresh;
      writeStorage(REFRESH_TOKEN_KEY, refresh);
    }
    emit();
  },

  setUser(user: SessionUser | null): void {
    sessionUser = user;
    writeStorage(SESSION_USER_KEY, user ? JSON.stringify(user) : null);
    emit();
  },

  clear(): void {
    accessToken = null;
    refreshToken = null;
    sessionUser = null;
    writeStorage(ACCESS_TOKEN_KEY, null);
    writeStorage(REFRESH_TOKEN_KEY, null);
    writeStorage(SESSION_USER_KEY, null);
    emit();
  },

  subscribe(listener: () => void): () => void {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
};
