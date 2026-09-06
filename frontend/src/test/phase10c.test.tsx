import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { VirtualList } from "../components/ui/VirtualList";

describe("phase10c performance UI helpers", () => {
  it("renders compact lists without virtualization window", () => {
    render(
      <MemoryRouter>
        <VirtualList
          getKey={(item) => item}
          items={["alpha", "beta"]}
          renderRow={(item) => <div>{item}</div>}
        />
      </MemoryRouter>,
    );
    expect(screen.getByText("alpha")).toBeInTheDocument();
    expect(screen.getByText("beta")).toBeInTheDocument();
  });
});
