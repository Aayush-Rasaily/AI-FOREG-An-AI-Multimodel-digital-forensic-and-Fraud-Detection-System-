import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AppRoutes } from "../routes/AppRoutes";
import { TestProviders } from "./render";

const dummyModel = {
  id: "00000000-0000-0000-0000-000000000061",
  name: "dummy",
  version: "1.0.0",
  framework: "NATIVE",
  author: "AI-FORGE Engineering",
  license: "Proprietary",
  input_type: "ANY",
  output_type: "INFRASTRUCTURE",
  model_hash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  required_device: "ANY",
  status: "LOADED",
  current_device: "cpu",
  last_loaded_at: "2026-08-31T00:00:01Z",
  last_latency_ms: 3.2,
  supported_tasks: ["infrastructure_check"],
  cache_state: { loaded: true, device: "cpu", hits: 1 },
  health: { loaded: true, status: "healthy" },
  metadata: {},
  created_at: "2026-08-31T00:00:00Z",
  updated_at: "2026-08-31T00:00:01Z",
};

function response(data: unknown) {
  return Promise.resolve({
    ok: true,
    json: async () => ({ success: true, data }),
  });
}

function requestUrl(input: RequestInfo | URL): string {
  if (typeof input === "string") {
    return input;
  }
  if (input instanceof URL) {
    return input.href;
  }
  return input.url;
}

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation((input: RequestInfo | URL) => {
      const url = requestUrl(input);
      if (url.includes("/inference/jobs")) {
        return response({
          items: [
            {
              id: "00000000-0000-0000-0000-000000000062",
              model_record_id: dummyModel.id,
              model_name: "dummy",
              model_version: "1.0.0",
              task: "infrastructure_check",
              device: "cpu",
              status: "SUCCEEDED",
              latency_ms: 3.2,
              batch_size: 1,
              error_code: null,
              error_message: null,
              metadata: {},
              started_at: "2026-08-31T00:00:01Z",
              finished_at: "2026-08-31T00:00:02Z",
              created_at: "2026-08-31T00:00:01Z",
              logs: [],
            },
          ],
          total: 1,
          limit: 50,
          offset: 0,
        });
      }
      if (url.includes("/models") && !url.includes("/reload")) {
        return response({
          items: [dummyModel],
          total: 1,
          limit: 50,
          offset: 0,
          cache_statistics: { hits: 1, misses: 0, evictions: 0, entries: 1 },
          devices: [{ device_type: "cpu", name: "cpu", available: true }],
        });
      }
      return response({ items: [], total: 0 });
    }),
  );
});

describe("Phase 6A AI models page", () => {
  it("shows registered models, device state, and inference jobs", async () => {
    render(
      <TestProviders initialEntries={["/ai-models"]}>
        <AppRoutes />
      </TestProviders>,
    );

    expect(
      await screen.findByRole("heading", { name: "AI Models" }),
    ).toBeInTheDocument();
    expect(await screen.findByText("Registered models")).toBeInTheDocument();
    expect(screen.getAllByText("dummy").length).toBeGreaterThan(0);
    expect(screen.getAllByText("LOADED").length).toBeGreaterThan(0);
    expect(screen.getByText("Recent inference jobs")).toBeInTheDocument();
    expect(screen.getAllByText("SUCCEEDED").length).toBeGreaterThan(0);
  });
});
