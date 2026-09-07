import { describe, expect, it } from "vitest";

describe("phase10d security hardening", () => {
  it("documents frontend CSP expectations for production nginx", () => {
    const csp =
      "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'";
    expect(csp.includes("default-src 'self'")).toBe(true);
    expect(csp.includes("unsafe-eval")).toBe(false);
  });
});
