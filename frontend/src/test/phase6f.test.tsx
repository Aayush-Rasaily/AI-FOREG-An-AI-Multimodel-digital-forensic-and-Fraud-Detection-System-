import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AiJuryPanel } from "../components/investigation/AiJuryPanel";
import { TestProviders } from "./render";

const evidence = {
  id: "00000000-0000-0000-0000-000000000301",
  case_id: "00000000-0000-0000-0000-000000000302",
  evidence_number: "EVID-000301",
  original_filename: "bundle.pdf",
  stored_filename: "bundle.pdf",
  mime_type: "application/pdf",
  file_size: 1024,
  sha256_hash: "a".repeat(64),
  status: "ANALYZED" as const,
  metadata: { classification: "DOCUMENT" },
  created_at: "2026-08-31T00:00:00Z",
  updated_at: "2026-08-31T00:00:01Z",
  custody_events: [],
};

const fusionDetail = {
  id: "00000000-0000-0000-0000-000000000303",
  evidence_id: evidence.id,
  status: "SUCCEEDED",
  engine_version: "1.0",
  policy_version: "1.0",
  verdict: "suspicious",
  risk_score: 62.5,
  confidence: 0.72,
  findings_count: 3,
  conflicts_count: 1,
  created_at: "2026-08-31T00:00:00Z",
  started_at: "2026-08-31T00:00:00Z",
  completed_at: "2026-08-31T00:00:01Z",
  error_code: null,
  error_message: null,
  metadata: {},
  provenance: { source_sha256: evidence.sha256_hash },
  modality_status: [
    {
      modality: "forensics",
      availability: "available",
      findings_count: 1,
      reason: null,
    },
    {
      modality: "audio_ai",
      availability: "unavailable",
      findings_count: 0,
      reason: "model_not_configured",
    },
  ],
  jury_assessments: [
    {
      role: "forensic_analyst",
      member_name: "Forensic Evidence Analyst",
      verdict: "suspicious",
      confidence: 0.7,
      availability: "available",
      supporting_finding_ids: ["forensics:1:metadata"],
      contradictory_finding_ids: [],
      explanation: "Forensic indicators suggest review.",
      limitations: null,
    },
    {
      role: "senior_judge",
      member_name: "Senior Forensic Judge",
      verdict: "suspicious",
      confidence: 0.72,
      availability: "available",
      supporting_finding_ids: [],
      contradictory_finding_ids: [],
      explanation: "Specialist consensus supports suspicious assessment.",
      limitations: null,
    },
  ],
  conflicts: [
    {
      conflict_id: "verdict_disagreement:forensics",
      conflict_type: "verdict_disagreement",
      severity: "HIGH",
      involved_finding_ids: ["forensics:1:metadata"],
      involved_modalities: ["forensics"],
      explanation: "Modalities disagree on suspicious versus genuine indicators.",
      resolution_status: "open",
    },
  ],
  agreement: {
    modality_agreement_ratio: 0.5,
    jury_agreement_ratio: 0.8,
    supporting_modalities: 1,
    contradictory_modalities: 0,
    unavailable_modalities: 1,
    inconclusive_modalities: 0,
    confidence_spread: 0.1,
    jury_votes_available: 4,
    jury_votes_total: 6,
  },
  explanation: "Final multimodal verdict: suspicious.",
  limitations: "Fusion uses deterministic weighting.",
  supporting_finding_ids: ["forensics:1:metadata"],
  contradictory_finding_ids: [],
  participating_modalities: ["forensics"],
  unavailable_modalities: ["audio_ai"],
};

function response(data: unknown, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: async () => ({ success: true, data }),
  });
}

function requestUrl(input: RequestInfo | URL): string {
  if (typeof input === "string") return input;
  if (input instanceof URL) return input.href;
  return input.url;
}

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation((input: RequestInfo | URL) => {
      const url = requestUrl(input);
      if (url.includes("/fusion-analysis/latest")) {
        return response(fusionDetail);
      }
      if (url.includes("/fusion-conflicts")) {
        return response(fusionDetail.conflicts);
      }
      if (url.includes("/fusion-analysis") && url.includes("/evidence/")) {
        return response({
          items: [fusionDetail],
          total: 1,
          limit: 50,
          offset: 0,
        });
      }
      return response({});
    }),
  );
});

describe("AiJuryPanel", () => {
  it("renders empty state without evidence", () => {
    render(
      <TestProviders>
        <AiJuryPanel />
      </TestProviders>,
    );
    expect(screen.getByText("No evidence selected")).toBeInTheDocument();
  });

  it("renders final assessment, jury, conflicts, and unavailable modalities", async () => {
    render(
      <TestProviders>
        <AiJuryPanel evidence={evidence} />
      </TestProviders>,
    );
    expect(await screen.findByText(/Risk: 62.5/)).toBeInTheDocument();
    expect(screen.getByText("Forensic Evidence Analyst")).toBeInTheDocument();
    expect(screen.getByText("Senior Forensic Judge")).toBeInTheDocument();
    expect(screen.getByText(/verdict disagreement/i)).toBeInTheDocument();
    expect(screen.getByText(/audio ai: unavailable/i)).toBeInTheDocument();
    expect(screen.getAllByText("suspicious").length).toBeGreaterThan(0);
    expect(screen.getByText(/Provenance SHA-256/)).toBeInTheDocument();
  });
});
