import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AppRoutes } from "../routes/AppRoutes";
import { TestProviders } from "./render";

const caseRecord = {
  id: "00000000-0000-0000-0000-000000000021",
  case_number: "CASE-000021",
  title: "Extraction test",
  description: "Phase 5A",
  status: "OPEN",
  priority: "HIGH",
  created_at: "2026-08-31T00:00:00Z",
  updated_at: "2026-08-31T00:00:00Z",
};

const evidenceRecord = {
  id: "00000000-0000-0000-0000-000000000022",
  case_id: caseRecord.id,
  evidence_number: "EVID-000021",
  original_filename: "invoice.pdf",
  stored_filename: "original.pdf",
  mime_type: "application/pdf",
  file_size: 128,
  sha256_hash: "a".repeat(64),
  status: "READY_FOR_ANALYSIS",
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
  let extracted = false;
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith(`/cases/${caseRecord.id}`)) {
        return response(caseRecord);
      }
      if (url.includes(`/cases/${caseRecord.id}/evidence`)) {
        return response({ items: [evidenceRecord], total: 1 });
      }
      if (url.includes(`/evidence/${evidenceRecord.id}/processing`)) {
        return response({
          items: [
            {
              id: "00000000-0000-0000-0000-000000000023",
              evidence_id: evidenceRecord.id,
              job_type: "PREPROCESSING",
              status: "SUCCEEDED",
            },
          ],
          total: 1,
        });
      }
      if (url.includes(`/evidence/${evidenceRecord.id}/extractions`)) {
        return response({
          status: extracted ? "SUCCEEDED" : "UNAVAILABLE",
          error_code: extracted ? null : "EXTRACTION_NOT_RUN",
          items: extracted
            ? [
                {
                  id: "00000000-0000-0000-0000-000000000024",
                  evidence_id: evidenceRecord.id,
                  artifact_id: null,
                  extraction_type: "TEXT",
                  source_type: "ORIGINAL",
                  source_identifier: "invoice.pdf",
                  page_number: 1,
                  frame_number: null,
                  timestamp_ms: null,
                  content: "Invoice No: 12345",
                  confidence: 0.97,
                  location: null,
                  normalized_location: null,
                  method: "pdf_text",
                  version: "1.0",
                  metadata: {},
                },
              ]
            : [],
          total: extracted ? 1 : 0,
        });
      }
      if (url.includes(`/evidence/${evidenceRecord.id}/regions`)) {
        return response({
          status: extracted ? "SUCCEEDED" : "UNAVAILABLE",
          error_code: null,
          items: [],
          total: 0,
        });
      }
      if (url.includes(`/evidence/${evidenceRecord.id}/extraction-artifacts`)) {
        return response({
          items: extracted
            ? [
                {
                  id: "00000000-0000-0000-0000-000000000025",
                  evidence_id: evidenceRecord.id,
                  artifact_type: "DOCUMENT_STRUCTURE",
                  mime_type: "application/json",
                  file_size: 128,
                  sha256_hash: "b".repeat(64),
                  created_at: "2026-08-31T00:00:01Z",
                  metadata: {},
                },
              ]
            : [],
          total: extracted ? 1 : 0,
        });
      }
      if (url.endsWith(`/evidence/${evidenceRecord.id}/extract`)) {
        extracted = true;
        return response({
          id: "00000000-0000-0000-0000-000000000023",
          evidence_id: evidenceRecord.id,
          job_type: "EXTRACTION",
          status: "QUEUED",
        });
      }
      return response({ items: [], total: 0 });
    }),
  );
});

describe("Phase 5A extraction workspace", () => {
  it("displays extraction status, text, and derived artifacts", async () => {
    const user = userEvent.setup();
    render(
      <TestProviders initialEntries={[`/investigations/${caseRecord.id}`]}>
        <AppRoutes />
      </TestProviders>,
    );

    await user.click(
      await screen.findByRole("button", { name: "Extract evidence" }),
    );
    expect((await screen.findAllByText("SUCCEEDED")).length).toBeGreaterThan(0);
    expect(screen.getByText("Invoice No: 12345")).toBeInTheDocument();
    expect(screen.getByText("DOCUMENT_STRUCTURE · 128 bytes")).toBeInTheDocument();
  });
});
