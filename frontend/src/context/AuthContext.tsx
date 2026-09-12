/* eslint-disable react-refresh/only-export-components -- context modules intentionally export both a provider component and its hook. */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  deriveSessionUser,
  fetchUserProfile,
  logoutSession,
  sendLoginRequest,
} from "../api/auth";
import { tokenStore } from "../api/tokenStore";
import type { Login, SessionUser } from "../types/auth_types";

interface AuthContextValue {
  user: SessionUser | null;
  isAuthenticated: boolean;
  signIn: (credentials: Login) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function hasSession(): boolean {
  return Boolean(tokenStore.getAccessToken() || tokenStore.getRefreshToken());
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<SessionUser | null>(() => tokenStore.getUser());
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(hasSession);

  // Keep React state in sync with the token store. This is what makes a failed
  // background refresh (which clears the store) automatically sign the user out.
  useEffect(() => {
    const sync = () => {
      setUser(tokenStore.getUser());
      setIsAuthenticated(hasSession());
    };
    sync();
    return tokenStore.subscribe(sync);
  }, []);

  const loadProfile = useCallback(async () => {
    try {
      const profile = await fetchUserProfile();
      tokenStore.setUser({
        id: profile.id,
        user_name: profile.user_name,
        name: profile.name,
        email: profile.email
      });
    } catch {
      // Keep whatever we already have. If the session was genuinely invalid the
      // token store was already cleared, which sends the user back to login.
    }
  }, []);

  // If a persisted session exists on first load, replace the cached profile with
  // the authoritative one from the API.
  useEffect(() => {
    if (hasSession()) void loadProfile();
  }, [loadProfile]);

  const signIn = useCallback(
    async (credentials: Login) => {
      const tokens = await sendLoginRequest(credentials);
      tokenStore.setTokens(tokens.access_token, tokens.refresh_token);
      // Show something right away, then replace it with the real profile.
      tokenStore.setUser(deriveSessionUser(credentials));
      await loadProfile();
    },
    [loadProfile],
  );

  const signOut = useCallback(async () => {
    if (tokenStore.getRefreshToken()) {
      try {
        await logoutSession();
      } catch {
        // Best effort: even if the server call fails we still clear locally.
      }
    }
    tokenStore.clear();
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, isAuthenticated, signIn, signOut }),
    [user, isAuthenticated, signIn, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
