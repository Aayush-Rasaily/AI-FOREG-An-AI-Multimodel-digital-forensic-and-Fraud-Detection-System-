import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AppRoutes } from "../routes/AppRoutes";
import { TestProviders } from "./render";

const caseRecord = {
  id: "00000000-0000-0000-0000-000000000011",
  case_number: "CASE-000011",
  title: "Processing pipeline test",
  description: "Phase 4 processing",
  status: "OPEN",
  priority: "HIGH",
  created_at: "2026-08-31T00:00:00Z",
  updated_at: "2026-08-31T00:00:00Z",
};

const evidenceRecord = {
  id: "00000000-0000-0000-0000-000000000012",
  case_id: caseRecord.id,
  evidence_number: "EVID-000011",
  original_filename: "invoice.pdf",
  stored_filename: "original.pdf",
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
  let processed = false;
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith(`/cases/${caseRecord.id}`)) {
        return response(caseRecord);
      }
      if (url.includes(`/cases/${caseRecord.id}/evidence`)) {
        return response({ items: [evidenceRecord], total: 1 });
      }
      if (url.includes(`/evidence/${evidenceRecord.id}/extractions`)) {
        return response({
          status: "UNAVAILABLE",
          error_code: "EXTRACTION_NOT_RUN",
          items: [],
          total: 0,
        });
      }
      if (url.includes(`/evidence/${evidenceRecord.id}/regions`)) {
        return response({
          status: "UNAVAILABLE",
          error_code: "EXTRACTION_NOT_RUN",
          items: [],
          total: 0,
        });
      }
      if (
        url.includes(`/evidence/${evidenceRecord.id}/extraction-artifacts`)
      ) {
        return response({ items: [], total: 0 });
      }
      if (url.includes(`/evidence/${evidenceRecord.id}/processing`)) {
        return response({
          items: processed
            ? [
                {
                  id: "00000000-0000-0000-0000-000000000013",
                  evidence_id: evidenceRecord.id,
                  job_type: "PREPROCESSING",
                  status: "SUCCEEDED",
                  priority: 0,
                  attempt: 1,
                  max_attempts: 1,
                  created_at: "2026-08-31T00:00:00Z",
                  started_at: "2026-08-31T00:00:00Z",
                  completed_at: "2026-08-31T00:00:01Z",
                  updated_at: "2026-08-31T00:00:01Z",
                  error_code: null,
                  error_message: null,
                  metadata: { classification: "DOCUMENT" },
                },
              ]
            : [],
          total: processed ? 1 : 0,
          limit: 20,
          offset: 0,
        });
      }
      if (url.includes(`/evidence/${evidenceRecord.id}/artifacts`)) {
        return response({
          items: processed
            ? [
                {
                  id: "00000000-0000-0000-0000-000000000014",
                  evidence_id: evidenceRecord.id,
                  artifact_type: "CLASSIFICATION",
                  mime_type: "application/json",
                  file_size: 64,
                  sha256_hash: "b".repeat(64),
                  created_at: "2026-08-31T00:00:01Z",
                  metadata: { classification: "DOCUMENT" },
                },
              ]
            : [],
          total: processed ? 1 : 0,
          limit: 50,
          offset: 0,
        });
      }
      if (init?.method === "POST" && url.endsWith(`/evidence/${evidenceRecord.id}/process`)) {
        processed = true;
        return response({
          id: "00000000-0000-0000-0000-000000000013",
          evidence_id: evidenceRecord.id,
          job_type: "PREPROCESSING",
          status: "QUEUED",
        });
      }
      return response({ items: [], total: 0 });
    }),
  );
});

describe("Phase 4 evidence processing", () => {
  it("starts processing and displays the successful job and artifact", async () => {
    const user = userEvent.setup();
    render(
      <TestProviders initialEntries={[`/investigations/${caseRecord.id}`]}>
        <AppRoutes />
      </TestProviders>,
    );

    expect(await screen.findByText("No artifacts yet")).toBeInTheDocument();
    await user.click(
      await screen.findByRole("button", { name: "Process evidence" }),
    );
    expect(fetch).toHaveBeenCalledWith(
      `/api/v1/evidence/${evidenceRecord.id}/process`,
      expect.objectContaining({ method: "POST" }),
    );
    expect(await screen.findByText("SUCCEEDED")).toBeInTheDocument();
    expect(await screen.findByText("CLASSIFICATION")).toBeInTheDocument();
    expect(
      screen.getByText(`SHA-256: ${"b".repeat(64)}`),
    ).toBeInTheDocument();
  });

});
