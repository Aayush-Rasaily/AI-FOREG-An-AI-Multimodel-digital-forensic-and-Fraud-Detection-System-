import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { authApi } from "../services/api/auth";
import { ApiClientError } from "../services/api/client";
import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  hasRememberedSession,
  setTokens,
} from "../services/api/tokenStore";
import type { AuthUser, LoginPayload } from "../types/auth";

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(() => Boolean(getAccessToken()));

  const refreshProfile = useCallback(async () => {
    if (!getAccessToken()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const response = await authApi.me();
      setUser(response.data);
    } catch (error) {
      if (error instanceof ApiClientError && error.status === 401) {
        clearTokens();
        setUser(null);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!getAccessToken()) {
        if (!cancelled) {
          setLoading(false);
        }
        return;
      }
      try {
        await refreshProfile();
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [refreshProfile]);

  const login = useCallback(async (payload: LoginPayload) => {
    const response = await authApi.login(payload);
    setTokens(
      response.data.access_token,
      response.data.refresh_token,
      Boolean(payload.remember_me),
    );
    setUser(response.data.user);
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout(getRefreshToken());
    } catch {
      // Best-effort logout against a revoked session.
    } finally {
      clearTokens();
      setUser(null);
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      login,
      logout,
      refreshProfile,
      hasPermission: (permission: string) =>
        Boolean(user?.permissions.includes(permission)),
      hasRole: (role: string) => Boolean(user?.roles.includes(role)),
    }),
    [user, loading, login, logout, refreshProfile],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}

export function useOptionalAuth(): AuthContextValue | null {
  return useContext(AuthContext);
}

export function useRememberedSession(): boolean {
  return hasRememberedSession();
}
