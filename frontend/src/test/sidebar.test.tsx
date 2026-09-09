import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { Sidebar } from "../components/navigation/Sidebar";
import { TestProviders } from "./render";

describe("Sidebar", () => {
  it("renders workspace and system navigation", () => {
    render(
      <TestProviders>
        <Sidebar
          collapsed={false}
          mobileOpen
          onClose={() => undefined}
          onToggle={() => undefined}
        />
      </TestProviders>,
    );

    expect(screen.getByText("AI-FORGE")).toBeInTheDocument();
    expect(screen.getByText("Investigations")).toBeInTheDocument();
    expect(screen.getByText("Evidence")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "System" })).toBeInTheDocument();
  });

  it("exposes a keyboard-operable collapse control", async () => {
    const user = userEvent.setup();
    const onToggle = vi.fn();

    render(
      <TestProviders>
        <Sidebar
          collapsed={false}
          mobileOpen
          onClose={() => undefined}
          onToggle={onToggle}
        />
      </TestProviders>,
    );

    await user.click(screen.getByRole("button", { name: "Collapse sidebar" }));
    expect(onToggle).toHaveBeenCalledOnce();
  });
});
