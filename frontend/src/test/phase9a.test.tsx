import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ExportPanel } from "../components/interop/ExportPanel";
import { ImportPanel } from "../components/interop/ImportPanel";
import { IntegrityBadge } from "../components/interop/IntegrityBadge";
import { ManifestViewer } from "../components/interop/ManifestViewer";
import { PackageHistoryPanel } from "../components/interop/PackageHistoryPanel";
import { TestProviders } from "./render";

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

const exportJob = {
  id: "exp-1",
  case_id: "case-1",
  format: "json_package",
  status: "COMPLETED",
  package_version: "1.0",
  schema_version: "1.0",
  storage_key: "interop/packages/exp-1.zip",
  package_checksum: "pkghash",
  manifest_checksum: "manihash",
  evidence_ids: [],
  report_versions: [],
  timeline_version: null,
  policy_versions: {},
  error_message: null,
  created_by: null,
  engine_version: "9a.1.0",
  policy_version: "1.0",
  created_at: "2026-09-07T00:00:00Z",
  completed_at: "2026-09-07T00:00:01Z",
};

const importJob = {
  id: "imp-1",
  source_filename: "pkg.zip",
  status: "CONFLICTS",
  package_version: "1.0",
  schema_version: "1.0",
  integrity_status: "CONFLICTS",
  validation: { valid: false },
  conflicts: ["case_number:CASE-1"],
  package_checksum: "x",
  storage_key: null,
  target_case_id: null,
  error_message: null,
  created_by: null,
  engine_version: "9a.1.0",
  policy_version: "1.0",
  created_at: "2026-09-07T00:00:00Z",
  completed_at: "2026-09-07T00:00:01Z",
};

function stubApi() {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = (init?.method ?? "GET").toUpperCase();
      if (url.includes("/cases/") && url.includes("/export") && method === "POST") {
        return response(exportJob);
      }
      if (url.includes("/cases/import") && method === "POST") {
        return response(importJob);
      }
      if (url.includes("/exports/") && url.includes("/manifest")) {
        return response({
          export_job_id: "exp-1",
          manifest: {
            schema_version: "1.0",
            evidence_count: 1,
            report_count: 0,
            files: [{ path: "case.json", sha256: "abc123def456" }],
          },
          manifest_checksum: "manihash1234567890",
          package_checksum: "pkghash",
        });
      }
      if (url.includes("/exports")) {
        return response({ items: [exportJob], total: 1 });
      }
      if (url.includes("/imports")) {
        return response({ items: [importJob], total: 1 });
      }
      return response(null, 404);
    }),
  );
}

describe("Phase 9A interoperability UI", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    stubApi();
  });

  it("renders IntegrityBadge", () => {
    render(<IntegrityBadge status="VALID" label="Integrity" />);
    expect(screen.getByText(/Integrity: VALID/i)).toBeInTheDocument();
  });

  it("shows export UI and history", async () => {
    render(
      <TestProviders>
        <ExportPanel caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText(/json_package/i)).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: /Create package/i })).toBeInTheDocument();
  });

  it("runs export action", async () => {
    const user = userEvent.setup();
    render(
      <TestProviders>
        <ExportPanel caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Create package/i })).toBeInTheDocument();
    });
    await user.click(screen.getByRole("button", { name: /Create package/i }));
    await waitFor(() => {
      expect(screen.getAllByText(/COMPLETED/i).length).toBeGreaterThan(0);
    });
  });

  it("shows import UI and empty-to-list states", async () => {
    render(
      <TestProviders>
        <ImportPanel />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText(/pkg.zip/i)).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: /Validate package/i })).toBeInTheDocument();
  });

  it("shows package history", async () => {
    render(
      <TestProviders>
        <PackageHistoryPanel caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText(/^Exports$/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/^Imports$/i)).toBeInTheDocument();
  });

  it("shows manifest viewer empty and loaded states", async () => {
    render(
      <TestProviders>
        <ManifestViewer exportId={null} />
      </TestProviders>,
    );
    expect(screen.getByText(/No manifest selected/i)).toBeInTheDocument();

    render(
      <TestProviders>
        <ManifestViewer exportId="exp-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText(/case.json/i)).toBeInTheDocument();
    });
  });

  it("handles export errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => response(null, 500)),
    );
    render(
      <TestProviders>
        <ExportPanel caseId="case-1" />
      </TestProviders>,
    );
    await waitFor(() => {
      expect(screen.getByText(/Exports unavailable/i)).toBeInTheDocument();
    });
  });
});
