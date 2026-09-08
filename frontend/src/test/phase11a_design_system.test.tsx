import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { Button } from "../components/ui/Button";
import { DataTable } from "../components/ui/DataTable";
import { PageState } from "../components/ui/PageState";
import { ThemeToggle } from "../components/theme/ThemeToggle";
import { TestProviders } from "./render";

describe("phase 11a design system", () => {
  it("renders button variants including outline and loading", () => {
    const { rerender } = render(<Button variant="outline">Export</Button>);
    expect(screen.getByRole("button", { name: "Export" })).toBeInTheDocument();
    rerender(
      <Button loading variant="primary">
        Save
      </Button>,
    );
    expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();
  });

  it("persists theme preference", async () => {
    const user = userEvent.setup();
    render(
      <TestProviders>
        <ThemeToggle />
      </TestProviders>,
    );
    await user.click(screen.getByRole("button", { name: "Light" }));
    expect(localStorage.getItem("ai-forge-theme")).toBe("light");
    expect(document.documentElement.dataset.theme).toBe("light");
  });

  it("renders page empty and permission states", () => {
    const { rerender } = render(<PageState kind="empty" title="No records" />);
    expect(screen.getByRole("heading", { name: "No records" })).toBeInTheDocument();
    rerender(<PageState kind="permission" />);
    expect(
      screen.getByRole("heading", { name: "Permission denied" }),
    ).toBeInTheDocument();
  });

  it("filters and paginates table rows", async () => {
    const user = userEvent.setup();
    render(
      <DataTable
        columns={[
          { key: "name", header: "Name", sortable: true, value: (row) => row.name },
        ]}
        pageSize={1}
        rowKey={(row) => row.id}
        rows={[
          { id: "1", name: "Alpha" },
          { id: "2", name: "Beta" },
        ]}
      />,
    );
    expect(screen.getByText("Alpha")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Next" }));
    expect(screen.getByText("Beta")).toBeInTheDocument();
  });
});
