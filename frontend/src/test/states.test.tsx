import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { ErrorState } from "../components/ui/ErrorState";
import { NetworkErrorState } from "../components/ui/NetworkErrorState";

describe("error states", () => {
  it("shows a safe retryable error state", async () => {
    const user = userEvent.setup();
    const onRetry = vi.fn();

    render(<ErrorState onRetry={onRetry} />);

    expect(screen.getByText("Workspace unavailable")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Try again" }));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("explains when the backend cannot be reached", () => {
    render(<NetworkErrorState />);

    expect(screen.getByText("Cannot reach AI-FORGE services")).toBeInTheDocument();
    expect(screen.getByText(/API is unavailable/)).toBeInTheDocument();
  });
});

