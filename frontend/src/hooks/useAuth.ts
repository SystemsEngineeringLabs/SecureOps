"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import type { ReactNode } from "react";
import { api } from "@/lib/api";
import type {
  AuthTokens,
  LoginRequest,
  Membership,
  RegisterRequest,
  Tenant,
  User,
} from "@/types/api";
import React from "react";

interface AuthState {
  user: User | null;
  tenant: Tenant | null;
  memberships: Membership[];
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [memberships, setMemberships] = useState<Membership[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const refreshTimerRef = useRef<ReturnType<typeof setTimeout>>();

  const clearAuth = useCallback(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
    setTenant(null);
    setMemberships([]);
    if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
  }, []);

  const scheduleRefresh = useCallback(
    (token: string) => {
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
      try {
        const payload = JSON.parse(atob(token.split(".")[1]));
        const expiresIn = payload.exp * 1000 - Date.now();
        const refreshAt = Math.max(expiresIn - 60_000, 5_000);
        refreshTimerRef.current = setTimeout(async () => {
          const rt = localStorage.getItem("refresh_token");
          if (!rt) return;
          try {
            const tokens = await api.post<AuthTokens>("/auth/refresh", {
              refresh_token: rt,
            });
            localStorage.setItem("access_token", tokens.access_token);
            localStorage.setItem("refresh_token", tokens.refresh_token);
            scheduleRefresh(tokens.access_token);
          } catch {
            clearAuth();
          }
        }, refreshAt);
      } catch {
        /* malformed token — ignore */
      }
    },
    [clearAuth],
  );

  const loadProfile = useCallback(async () => {
    try {
      const [u, t, m] = await Promise.all([
        api.get<User>("/auth/me"),
        api.get<Tenant>("/tenants/current"),
        api.get<Membership[]>("/auth/memberships"),
      ]);
      setUser(u);
      setTenant(t);
      setMemberships(m);
    } catch {
      clearAuth();
    }
  }, [clearAuth]);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      scheduleRefresh(token);
      loadProfile().finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
    return () => {
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    };
  }, [loadProfile, scheduleRefresh]);

  const login = useCallback(
    async (data: LoginRequest) => {
      const tokens = await api.post<AuthTokens>("/auth/login", data);
      localStorage.setItem("access_token", tokens.access_token);
      localStorage.setItem("refresh_token", tokens.refresh_token);
      scheduleRefresh(tokens.access_token);
      await loadProfile();
    },
    [loadProfile, scheduleRefresh],
  );

  const register = useCallback(
    async (data: RegisterRequest) => {
      const tokens = await api.post<AuthTokens>("/auth/register", data);
      localStorage.setItem("access_token", tokens.access_token);
      localStorage.setItem("refresh_token", tokens.refresh_token);
      scheduleRefresh(tokens.access_token);
      await loadProfile();
    },
    [loadProfile, scheduleRefresh],
  );

  const logout = useCallback(() => {
    clearAuth();
    window.location.href = "/login";
  }, [clearAuth]);

  const value = useMemo<AuthState>(
    () => ({
      user,
      tenant,
      memberships,
      isLoading,
      isAuthenticated: user !== null,
      login,
      register,
      logout,
    }),
    [user, tenant, memberships, isLoading, login, register, logout],
  );

  return React.createElement(AuthContext.Provider, { value }, children);
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
