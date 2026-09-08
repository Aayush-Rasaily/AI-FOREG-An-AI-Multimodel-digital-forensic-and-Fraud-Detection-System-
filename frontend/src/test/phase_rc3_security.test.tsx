import { render, screen } from "@testing-library/react";
import { Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { ProtectedRoute } from "../components/auth/ProtectedRoute";
import {
  clearTokens,
  getAccessToken,
  setTokens,
} from "../services/api/tokenStore";
import { TestProviders } from "./render";

afterEach(() => {
  clearTokens();
});

describe("RC3 frontend security", () => {
  it("redirects unauthenticated users away from protected routes", async () => {
    clearTokens();
    render(
      <TestProviders authenticated={false} initialEntries={["/dashboard"]}>
        <Routes>
          <Route element={<div>Login screen</div>} path="/login" />
          <Route
            element={
              <ProtectedRoute>
                <div>Secret workspace</div>
              </ProtectedRoute>
            }
            path="/dashboard"
          />
        </Routes>
      </TestProviders>,
    );
    expect(await screen.findByText("Login screen")).toBeInTheDocument();
    expect(screen.queryByText("Secret workspace")).not.toBeInTheDocument();
  });

  it("renders user-supplied text as text, not HTML", () => {
    const injected = "<img src=x onerror=alert(1) /><script>alert(1)</script>";
    render(
      <TestProviders>
        <p>{injected}</p>
      </TestProviders>,
    );
    expect(screen.getByText(injected)).toBeInTheDocument();
    expect(document.querySelector("img")).toBeNull();
    expect(document.querySelector("script")).toBeNull();
  });

  it("stores tokens in sessionStorage unless remember-me is set", () => {
    clearTokens();
    setTokens("access-token-value", "refresh-token-value", false);
    expect(getAccessToken()).toBe("access-token-value");
    expect(window.sessionStorage.getItem("aiforge.access_token")).toBe(
      "access-token-value",
    );
    expect(window.localStorage.getItem("aiforge.access_token")).toBeNull();
    clearTokens();
  });
});
