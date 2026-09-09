import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { DataTable } from "../components/ui/DataTable";
import { FilterChip } from "../components/ui/FilterChip";
import { Panel } from "../components/ui/Panel";
import { BREAKPOINTS } from "../hooks/useMediaQuery";

describe("phase 11b responsive foundation", () => {
  it("exposes enterprise viewport breakpoints", () => {
    expect(BREAKPOINTS.tablet).toContain("640px");
    expect(BREAKPOINTS.laptop).toContain("1024px");
    expect(BREAKPOINTS.desktop).toContain("1440px");
  });

  it("collapses and expands panels without unmounting body", async () => {
    const user = userEvent.setup();
    render(
      <Panel title="Timeline">
        <p>Preserved scroll content</p>
      </Panel>,
    );
    expect(screen.getByText("Preserved scroll content")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Collapse panel" }));
    expect(screen.getByRole("button", { name: "Expand panel" })).toHaveAttribute(
      "aria-expanded",
      "false",
    );
    expect(screen.getByText("Preserved scroll content")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Expand panel" }));
    expect(screen.getByRole("button", { name: "Collapse panel" })).toHaveAttribute(
      "aria-expanded",
      "true",
    );
  });

  it("renders filter chips with pressed state", async () => {
    const user = userEvent.setup();
    let active = false;
    const { rerender } = render(
      <FilterChip
        active={active}
        onClick={() => {
          active = true;
        }}
      >
        Images
      </FilterChip>,
    );
    await user.click(screen.getByRole("button", { name: "Images" }));
    rerender(
      <FilterChip active onClear={() => undefined}>
        Images
      </FilterChip>,
    );
    expect(screen.getByRole("button", { name: /Images/i })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("supports mobile card rows in data tables", () => {
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      writable: true,
      value: 375,
    });
    render(
      <DataTable
        columns={[
          { key: "name", header: "Name", priority: "primary", value: (row) => row.name },
          {
            key: "status",
            header: "Status",
            priority: "secondary",
            value: (row) => row.status,
          },
        ]}
        rowKey={(row) => row.id}
        rows={[
          { id: "1", name: "Alpha", status: "OPEN" },
          { id: "2", name: "Beta", status: "CLOSED" },
        ]}
      />,
    );
    expect(screen.getByText("Alpha")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Next" })).toBeInTheDocument();
  });
});
