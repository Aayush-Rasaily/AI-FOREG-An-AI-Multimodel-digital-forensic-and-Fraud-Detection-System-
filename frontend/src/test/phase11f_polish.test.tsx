import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { KeyboardShortcutsHelp } from "../components/help/HelpChrome";
import { Dialog } from "../components/ui/Dialog";
import { OfflineBanner } from "../components/ui/OfflineBanner";
import {
  ForbiddenState,
  OfflineState,
  ServerErrorState,
  TimeoutState,
} from "../components/ui/StatusStates";
import { SettingsPage } from "../pages/SettingsPage";
import { PREF_KEYS } from "../hooks/useInvestigatorPreferences";
import { TestProviders } from "./render";

describe("phase 11f accessibility and polish", () => {
  it("exposes skip-to-content link in the app shell", async () => {
    const { AppShell } = await import("../layouts/AppShell");
    render(
      <TestProviders>
        <AppShell>
          <p>Content</p>
        </AppShell>
      </TestProviders>,
    );
    const skip = screen.getByRole("link", { name: /skip to content/i });
    expect(skip).toHaveAttribute("href", "#main-content");
    expect(document.getElementById("main-content")).toBeTruthy();
  });

  it("renders polished status states with retry affordances", () => {
    const onRetry = () => undefined;
    render(
      <TestProviders>
        <OfflineState onRetry={onRetry} />
        <ForbiddenState />
        <ServerErrorState onRetry={onRetry} />
        <TimeoutState onRetry={onRetry} />
      </TestProviders>,
    );
    expect(screen.getByText("You are offline")).toBeInTheDocument();
    expect(screen.getByText("Access forbidden")).toBeInTheDocument();
    expect(screen.getByText(/Something went wrong \(500\)/)).toBeInTheDocument();
    expect(screen.getByText("Request timed out")).toBeInTheDocument();
  });

  it("closes accessible dialogs with Escape", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(
      <TestProviders>
        <Dialog onClose={onClose} open title="Accessible dialog">
          <button type="button">Inside</button>
        </Dialog>
      </TestProviders>,
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    await user.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalled();
  });

  it("shows keyboard shortcuts reference", () => {
    render(
      <TestProviders>
        <KeyboardShortcutsHelp onClose={() => undefined} open />
      </TestProviders>,
    );
    expect(screen.getByText("Keyboard shortcuts")).toBeInTheDocument();
    expect(screen.getByText(/Open command palette/i)).toBeInTheDocument();
  });

  it("persists workspace settings controls locally", async () => {
    const user = userEvent.setup();
    render(
      <TestProviders>
        <SettingsPage />
      </TestProviders>,
    );
    expect(screen.getByRole("heading", { name: "Settings" })).toBeInTheDocument();
    expect(screen.getByLabelText("Default dashboard")).toBeInTheDocument();
    expect(screen.getByLabelText("Sidebar behavior")).toBeInTheDocument();
    await user.selectOptions(
      screen.getByLabelText("Default dashboard"),
      "/analytics",
    );
    expect(localStorage.getItem(PREF_KEYS.defaultDashboard)).toContain(
      "/analytics",
    );
    await user.click(screen.getByLabelText("Toggle job notifications"));
  });

  it("hides offline banner while online", () => {
    render(
      <TestProviders>
        <OfflineBanner />
      </TestProviders>,
    );
    expect(screen.queryByText(/You are offline/i)).not.toBeInTheDocument();
  });
});
