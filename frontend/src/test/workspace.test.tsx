import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, vi } from "vitest";

import { AppRoutes } from "../routes/AppRoutes";
import { TestProviders } from "./render";

const caseData = {
  id: "00000000-0000-0000-0000-000000000001",
  case_number: "CASE-PENDING",
  title: "Connected investigation",
  description: null,
  status: "OPEN",
  priority: "MEDIUM",
  created_at: "2026-08-31T00:00:00Z",
  updated_at: "2026-08-31T00:00:00Z",
};

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/evidence")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            success: true,
            data: { items: [], total: 0 },
          }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({
          success: true,
          data: caseData,
        }),
      });
    }),
  );
});

describe("investigation workspace", () => {
  it("renders the investigation shell without fabricated evidence", async () => {
    render(
      <TestProviders initialEntries={["/investigations/CASE-PENDING"]}>
        <AppRoutes />
      </TestProviders>,
    );

    expect(
      await screen.findByText("Case ID: CASE-PENDING", {}, { timeout: 10000 }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("No evidence registered").length).toBeGreaterThan(0);
    expect(screen.getAllByText("No evidence selected").length).toBeGreaterThan(0);
  });

  it("switches to the future jury tab", async () => {
    const user = userEvent.setup();

    render(
      <TestProviders initialEntries={["/investigations/CASE-PENDING"]}>
        <AppRoutes />
      </TestProviders>,
    );

    await user.click(
      await screen.findByRole("tab", { name: "AI Jury" }, { timeout: 10000 }),
    );

    expect(screen.getByText("No evidence selected")).toBeInTheDocument();
  });
});

