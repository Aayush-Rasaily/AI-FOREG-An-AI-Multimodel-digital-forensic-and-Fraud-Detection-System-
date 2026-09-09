import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
    globals: true,
    // Must exceed setup.ts asyncUtilTimeout (5s) so waitFor cannot exhaust the test budget.
    testTimeout: 15_000,
  },
});
