import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { CommandPalette } from "../components/command/CommandPalette";
import { EvidenceList } from "../components/evidence/EvidenceList";
import { PREF_KEYS } from "../hooks/useInvestigatorPreferences";
import { TestProviders } from "./render";

describe("phase 11c investigator productivity", () => {
  it("opens command palette with Ctrl+K", async () => {
    const user = userEvent.setup();
    render(
      <TestProviders>
        <CommandPalette />
      </TestProviders>,
    );
    await user.keyboard("{Control>}k{/Control}");
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByLabelText("Command search")).toBeInTheDocument();
  });

  it("filters evidence client-side without API changes", async () => {
    const user = userEvent.setup();
    render(
      <EvidenceList
        items={[
          {
            id: "1",
            case_id: "c1",
            evidence_number: "EVID-1",
            original_filename: "invoice.pdf",
            stored_filename: "a.pdf",
            mime_type: "application/pdf",
            file_size: 100,
            sha256_hash: "a".repeat(64),
            status: "REGISTERED",
            metadata: {},
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
            custody_events: [],
          },
          {
            id: "2",
            case_id: "c1",
            evidence_number: "EVID-2",
            original_filename: "photo.jpg",
            stored_filename: "b.jpg",
            mime_type: "image/jpeg",
            file_size: 200,
            sha256_hash: "b".repeat(64),
            status: "REGISTERED",
            metadata: {},
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
            custody_events: [],
          },
        ]}
        showDetails={false}
      />,
    );
    await user.type(screen.getByLabelText("Filter evidence"), "invoice");
    expect(screen.getByText("invoice.pdf")).toBeInTheDocument();
    expect(screen.queryByText("photo.jpg")).not.toBeInTheDocument();
  });

  it("defines local preference keys for session restore", () => {
    expect(PREF_KEYS.openInvestigationTabs).toContain("open-investigation");
    expect(PREF_KEYS.activeTabByCase).toContain("active-tabs");
    expect(PREF_KEYS.panelSizes).toContain("panel-sizes");
  });
});
