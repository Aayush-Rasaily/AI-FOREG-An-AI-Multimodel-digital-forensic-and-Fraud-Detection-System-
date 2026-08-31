import { render, screen } from "@testing-library/react";
import { beforeEach, vi } from "vitest";

import { AppRoutes } from "../routes/AppRoutes";
import { TestProviders } from "./render";

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        success: true,
        data: {
          status: "healthy",
          database: "healthy",
          version: "0.1.0",
          environment: "test",
        },
      }),
    }),
  );
});

describe("application routing", () => {
  it("renders the dashboard route", async () => {
    render(
      <TestProviders initialEntries={["/dashboard"]}>
        <AppRoutes />
      </TestProviders>,
    );

    expect(await screen.findByRole("heading", { name: "Investigation dashboard" })).toBeInTheDocument();
  });

  it("renders the 404 route", async () => {
    render(
      <TestProviders initialEntries={["/not-a-real-route"]}>
        <AppRoutes />
      </TestProviders>,
    );

    expect(await screen.findByRole("heading", { name: "Page not found" })).toBeInTheDocument();
  });
});

