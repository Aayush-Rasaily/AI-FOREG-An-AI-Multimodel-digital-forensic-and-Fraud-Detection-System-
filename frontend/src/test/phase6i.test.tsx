import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AiJuryPanel } from "../components/investigation/AiJuryPanel";
import { ForensicReportPanel } from "../components/investigation/ForensicReportPanel";
import { TestProviders } from "./render";

const evidence = {
  id: "00000000-0000-0000-0000-000000000701",
  case_id: "00000000-0000-0000-0000-000000000702",
  evidence_number: "EVID-701",
  original_filename: "sample.pdf",
  stored_filename: "sample.pdf",
  mime_type: "application/pdf",
  file_size: 1024,
  sha256_hash: "a".repeat(64),
  status: "ANALYZED" as const,
  metadata: {},
  created_at: "2026-08-31T00:00:00Z",
  updated_at: "2026-08-31T00:00:01Z",
  custody_events: [],
};

function response(data: unknown, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: async () => ({ success: true, data }),
  });
}

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response({})));
});

describe("Phase 6I frontend failure safety", () => {
  it("AiJuryPanel handles partial fusion payloads without crashing", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/fusion-analysis/latest")) {
          return response({
            id: "00000000-0000-0000-0000-000000000703",
            evidence_id: evidence.id,
            status: "SUCCEEDED",
            engine_version: "1.0",
            policy_version: "1.0",
            verdict: "inconclusive",
            risk_score: null,
            confidence: null,
            findings_count: 0,
            conflicts_count: 0,
            metadata: {},
            provenance: {},
          });
        }
        return response({});
      }),
    );
    render(
      <TestProviders>
        <AiJuryPanel evidence={evidence} />
      </TestProviders>,
    );
    expect(await screen.findByText("inconclusive")).toBeInTheDocument();
  });

  it("ForensicReportPanel handles generating state without crashing", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/reports/latest")) {
          return response({
            id: "00000000-0000-0000-0000-000000000704",
            case_id: evidence.case_id,
            status: "GENERATING",
            report_version: "1.0",
            engine_version: "1.0",
            fusion_policy_version: null,
            case_intelligence_policy_version: null,
            case_intelligence_run_id: null,
            evidence_count: 0,
            evidence_hashes: [],
            pdf_sha256: null,
            has_pdf: false,
            created_at: "2026-08-31T00:00:00Z",
            started_at: "2026-08-31T00:00:00Z",
            completed_at: null,
            error_code: null,
            error_message: null,
            metadata: {},
            provenance: {},
            content: {},
            executive_summary: {},
            explainability: {},
          });
        }
        return response({});
      }),
    );
    render(
      <TestProviders>
        <ForensicReportPanel caseId={evidence.case_id} />
      </TestProviders>,
    );
    expect(await screen.findByText("GENERATING")).toBeInTheDocument();
    expect(screen.getByText(/Generating forensic report/i)).toBeInTheDocument();
  });
});
