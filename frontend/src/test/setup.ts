import "@testing-library/jest-dom/vitest";

import { configure } from "@testing-library/react";
import { afterEach, vi } from "vitest";

import { clearTokens } from "../services/api/tokenStore";
import { PREF_KEYS } from "../hooks/useInvestigatorPreferences";

// CI machines intermittently miss the default 1s findBy* window when the
// full suite runs in parallel; 5s removes that load-related flakiness.
configure({ asyncUtilTimeout: 5000 });

Object.defineProperty(window, "matchMedia", {
  writable: true,
  configurable: true,
  value: (query: string) => {
    const width =
      typeof window.innerWidth === "number" && window.innerWidth > 0
        ? window.innerWidth
        : 1280;
    let matches = false;
    if (query.includes("prefers-color-scheme: dark")) {
      matches = true;
    }
    const minMatch = /min-width:\s*(\d+(?:\.\d+)?)(px|rem)/.exec(query);
    const maxMatch = /max-width:\s*(\d+(?:\.\d+)?)(px|rem)/.exec(query);
    const toPx = (value: string, unit: string) =>
      unit === "rem" ? Number(value) * 16 : Number(value);
    if (minMatch) {
      matches = width >= toPx(minMatch[1], minMatch[2]);
    }
    if (maxMatch) {
      matches = width <= toPx(maxMatch[1], maxMatch[2]);
    }
    return {
      matches,
      media: query,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      addListener: () => undefined,
      removeListener: () => undefined,
      dispatchEvent: () => false,
    };
  },
});

Object.defineProperty(window, "innerWidth", {
  writable: true,
  configurable: true,
  value: 1280,
});


afterEach(() => {
  vi.restoreAllMocks();
  clearTokens();
  for (const key of Object.values(PREF_KEYS)) {
    localStorage.removeItem(key);
  }
});

