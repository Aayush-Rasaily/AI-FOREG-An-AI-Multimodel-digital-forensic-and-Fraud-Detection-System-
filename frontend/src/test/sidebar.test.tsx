import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import { Sidebar } from "../components/navigation/Sidebar";

describe("Sidebar", () => {
  it("renders workspace and system navigation", () => {
    render(
      <MemoryRouter>
        <Sidebar
          collapsed={false}
          mobileOpen={false}
          onClose={() => undefined}
          onToggle={() => undefined}
        />
      </MemoryRouter>,
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
      <MemoryRouter>
        <Sidebar
          collapsed={false}
          mobileOpen={false}
          onClose={() => undefined}
          onToggle={onToggle}
        />
      </MemoryRouter>,
    );

    await user.click(screen.getByRole("button", { name: "Collapse sidebar" }));
    expect(onToggle).toHaveBeenCalledOnce();
  });
});

