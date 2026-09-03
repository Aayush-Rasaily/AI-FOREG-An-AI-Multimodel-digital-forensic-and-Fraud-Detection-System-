import "@testing-library/jest-dom/vitest";

import { afterEach, vi } from "vitest";

import { clearTokens } from "../services/api/tokenStore";

afterEach(() => {
  vi.restoreAllMocks();
  clearTokens();
});

