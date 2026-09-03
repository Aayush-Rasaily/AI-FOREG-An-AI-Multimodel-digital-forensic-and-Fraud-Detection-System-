import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";

import { ProtectedRoute } from "../components/auth/ProtectedRoute";
import { RoleGuard } from "../components/auth/RoleGuard";
import { AuthProvider } from "../context/AuthContext";
import { UnauthorizedPage } from "../pages/UnauthorizedPage";
import { LoginPage } from "../pages/LoginPage";
import { clearTokens, setTokens } from "../services/api/tokenStore";

const adminUser = {
  id: "00000000-0000-0000-0000-000000000a01",
  username: "admin",
  display_name: "Administrator",
  email: null,
  is_active: true,
  is_locked: false,
  roles: ["Administrator"],
  permissions: ["admin.manage_users", "system.monitor", "case.view"],
  last_login_at: null,
  created_at: "2026-09-02T00:00:00Z",
};

function response(data: unknown, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    headers: { get: () => null },
    json: async () =>
      status >= 200 && status < 300
        ? { success: true, data }
        : {
            success: false,
            error: {
              message: status === 401 ? "Authentication is required." : "Error.",
              code: status === 401 ? "UNAUTHENTICATED" : "API_ERROR",
              request_id: null,
            },
          },
  });
}

function Providers({
  children,
  initialEntries = ["/"],
}: {
  children: ReactNode;
  initialEntries?: string[];
}) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>
        <AuthProvider>{children}</AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

beforeEach(() => {
  clearTokens();
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response({})));
});

describe("Phase 8A authentication frontend", () => {
  it("renders the unauthorized page", () => {
    render(
      <Providers>
        <UnauthorizedPage />
      </Providers>,
    );
    expect(screen.getByText("Unauthorized")).toBeInTheDocument();
  });

  it("renders the login page", async () => {
    render(
      <Providers initialEntries={["/login"]}>
        <LoginPage />
      </Providers>,
    );
    expect(
      await screen.findByRole("heading", { name: "Sign in" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Username")).toBeInTheDocument();
  });

  it("redirects protected routes when unauthenticated", async () => {
    render(
      <Providers initialEntries={["/dashboard"]}>
        <Routes>
          <Route element={<div>Login screen</div>} path="/login" />
          <Route
            element={
              <ProtectedRoute>
                <div>Secret workspace</div>
              </ProtectedRoute>
            }
            path="/dashboard"
          />
        </Routes>
      </Providers>,
    );

    expect(await screen.findByText("Login screen")).toBeInTheDocument();
    expect(screen.queryByText("Secret workspace")).not.toBeInTheDocument();
  });

  it("renders protected content when authenticated", async () => {
    setTokens("access-token", "refresh-token", false);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: RequestInfo) => {
        if (String(input).includes("/auth/me")) {
          return response(adminUser);
        }
        return response({});
      }),
    );

    render(
      <Providers initialEntries={["/dashboard"]}>
        <ProtectedRoute>
          <div>Secret workspace</div>
        </ProtectedRoute>
      </Providers>,
    );

    expect(await screen.findByText("Secret workspace")).toBeInTheDocument();
  });

  it("blocks unauthorized roles", async () => {
    setTokens("access-token", "refresh-token", false);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: RequestInfo) => {
        if (String(input).includes("/auth/me")) {
          return response({
            ...adminUser,
            roles: ["Viewer"],
            permissions: ["case.view"],
          });
        }
        return response({});
      }),
    );

    render(
      <Providers initialEntries={["/users"]}>
        <RoleGuard
          fallback={<div>Access denied</div>}
          permission="admin.manage_users"
        >
          <div>User admin panel</div>
        </RoleGuard>
      </Providers>,
    );

    expect(await screen.findByText("Access denied")).toBeInTheDocument();
    expect(screen.queryByText("User admin panel")).not.toBeInTheDocument();
  });

  it("keeps authorized content for matching permissions", async () => {
    setTokens("access-token", "refresh-token", false);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: RequestInfo) => {
        if (String(input).includes("/auth/me")) {
          return response(adminUser);
        }
        return response({});
      }),
    );

    render(
      <Providers>
        <RoleGuard permission="admin.manage_users">
          <div>User admin panel</div>
        </RoleGuard>
      </Providers>,
    );

    expect(await screen.findByText("User admin panel")).toBeInTheDocument();
  });
});
