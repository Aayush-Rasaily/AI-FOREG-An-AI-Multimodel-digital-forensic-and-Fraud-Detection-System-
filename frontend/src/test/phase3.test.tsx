import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AppRoutes } from "../routes/AppRoutes";
import { TestProviders } from "./render";

const caseRecord = {
  id: "00000000-0000-0000-0000-000000000001",
  case_number: "CASE-000001",
  title: "Banking evidence review",
  description: "Preservation test",
  status: "OPEN",
  priority: "HIGH",
  created_at: "2026-08-31T00:00:00Z",
  updated_at: "2026-08-31T00:00:00Z",
};

const evidenceRecord = {
  id: "00000000-0000-0000-0000-000000000002",
  case_id: caseRecord.id,
  evidence_number: "EVID-000001",
  original_filename: "statement.pdf",
  stored_filename: "generated.pdf",
  mime_type: "application/pdf",
  file_size: 128,
  sha256_hash: "a".repeat(64),
  status: "REGISTERED",
  metadata: {},
  created_at: "2026-08-31T00:00:00Z",
  updated_at: "2026-08-31T00:00:00Z",
  custody_events: [],
};

function response(data: unknown) {
  return Promise.resolve({
    ok: true,
    json: async () => ({ success: true, data }),
  });
}

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (init?.method === "POST" && url.endsWith("/cases")) {
        return response(caseRecord);
      }
      if (url.includes("/evidence")) {
        return response({ items: [evidenceRecord], total: 1 });
      }
      if (url.includes("/cases?")) {
        return response({ items: [caseRecord], total: 1, limit: 50, offset: 0 });
      }
      if (url.includes("/intelligence")) {
        return Promise.resolve({ ok: false, status: 404, json: async () => ({ success: false }) });
      }
      return response(caseRecord);
    }),
  );
});

describe("Phase 3 case and evidence workspace", () => {
  it("lists cases and creates a case through the API", async () => {
    const user = userEvent.setup();
    render(
      <TestProviders initialEntries={["/investigations"]}>
        <AppRoutes />
      </TestProviders>,
    );

    expect(await screen.findByText("CASE-000001")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /create investigation/i }));
    await user.type(screen.getByLabelText("Case title"), "New investigation");
    await user.click(screen.getByRole("button", { name: "Create case" }));

    expect(await screen.findByText("CASE-000001")).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(
      "/api/v1/cases",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("renders evidence metadata and hash in a connected case", async () => {
    render(
      <TestProviders
        initialEntries={[`/investigations/${caseRecord.id}`]}
      >
        <AppRoutes />
      </TestProviders>,
    );

    expect(
      await screen.findByText(/EVID-000001/, {}, { timeout: 5000 }),
    ).toBeInTheDocument();
    expect(screen.getAllByText(`SHA-256: ${"a".repeat(64)}`).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Select an original evidence file").length).toBeGreaterThan(0);
  });
});
