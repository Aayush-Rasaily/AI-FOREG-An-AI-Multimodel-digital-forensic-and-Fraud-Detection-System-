import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";

import { AuthProvider } from "../context/AuthContext";
import { setTokens } from "../services/api/tokenStore";
import type { AuthUser } from "../types/auth";

/** Authenticated administrator used by investigation UI tests. */
export const TEST_USER: AuthUser = {
  id: "00000000-0000-0000-0000-000000000a01",
  username: "admin",
  display_name: "Administrator",
  email: null,
  is_active: true,
  is_locked: false,
  roles: ["Administrator"],
  permissions: [
    "case.create",
    "case.view",
    "case.edit",
    "case.delete",
    "evidence.upload",
    "evidence.view",
    "evidence.delete",
    "ai.run",
    "ai.view",
    "fusion.run",
    "fusion.view",
    "timeline.run",
    "timeline.view",
    "correlation.run",
    "correlation.view",
    "entity.run",
    "entity.view",
    "report.generate",
    "report.view",
    "report.download",
    "report.approve",
    "audit.view",
    "admin.manage_users",
    "system.monitor",
    "comment.create",
    "comment.view",
    "collab.manage_members",
    "collab.assign",
    "task.manage",
    "review.decide",
    "workflow.transition",
    "security.view",
    "security.manage",
    "interop.export",
    "interop.import",
    "knowledge_graph.run",
    "knowledge_graph.view",
    "investigation_intelligence.run",
    "investigation_intelligence.view",
    "decision_support.run",
    "decision_support.view",
    "case_review.run",
    "case_review.view",
    "integrity.run",
    "integrity.view",
    "analytics.run",
    "analytics.view",
    "platform_validation.run",
    "platform_validation.view",
  ],
  last_login_at: null,
  created_at: "2026-09-02T00:00:00Z",
};

export function TestProviders({
  children,
  initialEntries = ["/dashboard"],
  authenticated = true,
}: {
  children: ReactNode;
  initialEntries?: string[];
  authenticated?: boolean;
}) {
  if (authenticated) {
    setTokens("test-access-token", "test-refresh-token", false);
  }

  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>
        <AuthProvider initialUser={authenticated ? TEST_USER : null}>
          {children}
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
}
