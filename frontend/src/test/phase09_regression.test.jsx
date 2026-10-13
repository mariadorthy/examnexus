import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

import App from "../App";
import { stubFetch, jsonResponse, ADMIN_USER, seedUser } from "./helpers";
import { buildAdminRoutesStubs } from "./fixtures/apiFixtures";

describe("Phase 9 — Regression", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
    window.history.pushState({}, "", "/");
  });

  it("REG-01: no React key warnings during Admin Dashboard mount", async () => {
    const errSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    seedUser(ADMIN_USER);
    stubFetch(buildAdminRoutesStubs());
    render(<App />);

    await waitFor(() =>
      expect(screen.getByRole("heading", { name: /^dashboard$/i })).toBeInTheDocument()
    );

    const joined = errSpy.mock.calls.flat().map(String).join("\n");
    expect(joined).not.toMatch(/unique "key" prop/i);
    errSpy.mockRestore();
  });

  // -------------------------------------------------------
  // REG-02 — verify route is reachable without auth.
  //
  // Simulates "user opens the verify URL fresh" (full reload).
  // A pushState-only variant would require URL reactivity
  // (DEF-01) that the app does not yet have. When FIX-G is
  // applied, an additional pushState-based test can be added.
  // -------------------------------------------------------
  it("REG-02: opening /verify-hall-ticket/* fresh never renders Login", async () => {
    localStorage.clear(); // no user
    window.history.pushState({}, "", "/verify-hall-ticket/tok-123");

    stubFetch([["*", () => jsonResponse({ message: "not verified" }, { status: 404 })]]);

    render(<App />);

    await waitFor(() =>
      expect(
        screen.queryByRole("heading", { name: /welcome back/i })
      ).not.toBeInTheDocument()
    );

    window.history.pushState({}, "", "/");
  });
});