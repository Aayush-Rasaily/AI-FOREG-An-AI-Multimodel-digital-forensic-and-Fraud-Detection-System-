import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CaseAccessPanel } from "../components/security/CaseAccessPanel";
import { CompliancePanel } from "../components/security/CompliancePanel";
import { PermissionsPanel } from "../components/security/PermissionsPanel";
import { PolicyViolationsPanel } from "../components/security/PolicyViolationsPanel";
import { SecurityPanel } from "../components/security/SecurityPanel";
import { SecurityStatusBadge } from "../components/security/SecurityStatusBadge";
import { TestProviders } from "./render";

const caseId = "case-8f";

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
            error: { message: "failed", code: "ERR", request_id: "r1" },
          },
  });
}

describe("Phase 8F security UI", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/security/roles")) {
          return response({
            items: [
              {
                code: "ADMIN",
                name: "Admin",
                description: "Full enterprise administration.",
                permissions: ["security.manage"],
                policy_version: "1.0",
              },
            ],
            total: 1,
          });
        }
        if (url.includes("/security/permissions")) {
          return response({
            items: [
              {
                code: "case.view",
                resource: "Cases",
                action: "view",
                description: "View cases",
                roles: ["ADMIN"],
                policy_version: "1.0",
              },
            ],
            total: 1,
          });
        }
        if (url.includes("/security/violations")) {
          return response({
            items: [
              {
                id: "v1",
                case_id: caseId,
                policy_code: "evidence_security",
                severity: "HIGH",
                message: "Evidence hash integrity gap detected.",
                details: {},
                detected_at: "2026-09-06T00:00:00Z",
                resolved_at: null,
                policy_version: "1.0",
              },
            ],
            total: 1,
          });
        }
        if (url.includes("/access")) {
          return response({
            items: [
              {
                id: "a1",
                case_id: caseId,
                user_id: "u1",
                access_level: "Owner",
                granted_by: null,
                reason: "case owner",
                active: true,
                granted_at: "2026-09-06T00:00:00Z",
                revoked_at: null,
              },
            ],
            total: 1,
          });
        }
        if (url.includes("/compliance")) {
          return response({
            status: "PARTIAL",
            case_id: caseId,
            chain_of_custody_complete: true,
            evidence_integrity_ok: true,
            audit_complete: false,
            workflow_compliant: true,
            report_approval_compliant: true,
            missing_approvals: [],
            missing_provenance: ["fusion_provenance"],
            policy_violations: [],
            details: {},
            generated_at: "2026-09-06T00:00:00Z",
            policy_version: "1.0",
            engine_version: "8f.1.0",
          });
        }
        return response({}, 500);
      }),
    );
  });

  it("renders security roles and permissions", async () => {
    render(
      <TestProviders>
        <SecurityPanel />
        <PermissionsPanel />
        <SecurityStatusBadge status="COMPLIANT" />
      </TestProviders>,
    );
    expect(await screen.findByText("Admin")).toBeInTheDocument();
    expect(await screen.findByText("case.view")).toBeInTheDocument();
    expect(screen.getByText("COMPLIANT")).toBeInTheDocument();
  });

  it("renders case access, compliance, and violations", async () => {
    render(
      <TestProviders>
        <CaseAccessPanel caseId={caseId} />
        <CompliancePanel caseId={caseId} />
        <PolicyViolationsPanel caseId={caseId} />
      </TestProviders>,
    );
    expect(await screen.findByText("Owner")).toBeInTheDocument();
    expect(await screen.findByText("PARTIAL")).toBeInTheDocument();
    expect(
      await screen.findByText("Evidence hash integrity gap detected."),
    ).toBeInTheDocument();
  });

  it("shows empty and error states", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/security/violations")) {
          return response({ items: [], total: 0 });
        }
        if (url.includes("/access")) {
          return response({}, 500);
        }
        return response({ items: [], total: 0 });
      }),
    );

    render(
      <TestProviders>
        <PolicyViolationsPanel />
        <CaseAccessPanel caseId={caseId} />
      </TestProviders>,
    );
    expect(await screen.findByText("No violations")).toBeInTheDocument();
    expect(await screen.findByText("Error")).toBeInTheDocument();
  });
});
