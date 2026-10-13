import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";

import App from "../App";
import { stubFetch, jsonResponse, ADMIN_USER, seedUser } from "./helpers";
import { buildAdminRoutesStubs } from "./fixtures/apiFixtures";

describe("Phase 14 — Cross-cutting behavior", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
    if (window.location.hash) {
      window.history.replaceState(null, "", window.location.pathname);
    }
  });

  // -------------------------------------------------------
  // X-01 — hash router reads hash on mount
  // -------------------------------------------------------
  it("X-01: App reads the initial hash and opens the matching page", async () => {
    seedUser(ADMIN_USER);
    window.location.hash = "#/Departments";

    stubFetch(buildAdminRoutesStubs());
    render(<App />);

    await waitFor(() => {
      const headings = screen.getAllByRole("heading");
      expect(
        headings.some((h) => /departments/i.test(h.textContent || ""))
      ).toBe(true);
    }, { timeout: 8000 });
  });

  // -------------------------------------------------------
  // X-02 — hash router listens to hashchange
  // -------------------------------------------------------
  it("X-02: App responds to hashchange events", async () => {
    seedUser(ADMIN_USER);
    stubFetch(buildAdminRoutesStubs());
    render(<App />);

    await waitFor(() =>
      expect(screen.getByRole("heading", { name: /^dashboard$/i })).toBeInTheDocument()
    );

    // Simulate the user pasting a new hash.
    await act(async () => {
      window.location.hash = "#/Students";
      window.dispatchEvent(new HashChangeEvent("hashchange"));
    });

    await waitFor(() => {
      const headings = screen.getAllByRole("heading");
      expect(
        headings.some((h) => /students/i.test(h.textContent || ""))
      ).toBe(true);
    }, { timeout: 8000 });
  });

  // -------------------------------------------------------
  // X-03 — 401 from api.js dispatches examnexus:unauthorized
  // -------------------------------------------------------
  it("X-03: a 401 response logs the user out (via event)", async () => {
    seedUser(ADMIN_USER);

    stubFetch([
      ["GET /api/dashboard/", () =>
        jsonResponse({ message: "Authentication required.", success: false }, { status: 401 })],
      ["*", () => jsonResponse({}, { status: 404 })],
    ]);

    render(<App />);

    // After the 401, storage should be cleared and the Login
    // screen shown via the examnexus:unauthorized event.
    await waitFor(() =>
      expect(
        screen.getByRole("heading", { name: /welcome back/i })
      ).toBeInTheDocument()
    );

    expect(localStorage.getItem("examnexus_token")).toBeNull();
    expect(localStorage.getItem("examnexus_user")).toBeNull();
  });

  // -------------------------------------------------------
  // X-04 — unknown role fallback (already covered in NAV-06, this is a lock)
  // -------------------------------------------------------
  it("X-04: role value that is not admin/staff/student renders Login", async () => {
    seedUser({ id: 42, name: "X", email: "x@y.z", role: "curator" });
    stubFetch(buildAdminRoutesStubs());

    const errSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    render(<App />);

    await waitFor(() =>
      expect(
        screen.getByRole("heading", { name: /welcome back/i })
      ).toBeInTheDocument()
    );
    errSpy.mockRestore();
  });

  // -------------------------------------------------------
  // X-05 — corrupted localStorage (malformed JSON) → Login
  // -------------------------------------------------------
  it("X-05: corrupted examnexus_user JSON falls back to Login", () => {
    localStorage.setItem("examnexus_token", "junk");
    localStorage.setItem("examnexus_user", "{not-json");

    stubFetch([["*", () => jsonResponse({}, { status: 200 })]]);
    render(<App />);

    expect(
      screen.getByRole("heading", { name: /welcome back/i })
    ).toBeInTheDocument();
  });

  // -------------------------------------------------------
  // X-06 — user without role field → Login
  // -------------------------------------------------------
  it("X-06: user without a role field renders Login (not blank)", async () => {
    seedUser({ id: 1, name: "NoRole", email: "nr@x.y" });
    stubFetch(buildAdminRoutesStubs());

    const errSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    render(<App />);

    await waitFor(() =>
      expect(
        screen.getByRole("heading", { name: /welcome back/i })
      ).toBeInTheDocument()
    );
    errSpy.mockRestore();
  });

  // -------------------------------------------------------
  // X-07 — public route + logged-out user works
  // -------------------------------------------------------
  it("X-07: /verify-hall-ticket/xyz does not require auth", async () => {
    window.location.hash = ""; // ensure empty hash
    window.history.pushState({}, "", "/verify-hall-ticket/xyz");

    stubFetch([["*", () => jsonResponse({ message: "not verified" }, { status: 404 })]]);
    render(<App />);

    await waitFor(() =>
      expect(
        screen.queryByRole("heading", { name: /welcome back/i })
      ).not.toBeInTheDocument()
    );

    window.history.pushState({}, "", "/");
  });

  // -------------------------------------------------------
  // X-08 — logout clears hash AND storage
  // -------------------------------------------------------
  it("X-08: logging out clears both localStorage and the URL hash", async () => {
    seedUser(ADMIN_USER);
    window.location.hash = "#/Departments";

    stubFetch(buildAdminRoutesStubs());
    render(<App />);

    await waitFor(() => {
      const headings = screen.getAllByRole("heading");
      expect(
        headings.some((h) => /departments/i.test(h.textContent || ""))
      ).toBe(true);
    }, { timeout: 8000 });

    const sidebar = screen.getByRole("complementary");
    const logout = Array.from(sidebar.querySelectorAll("button")).find(
      (b) => /logout/i.test(b.textContent || "")
    );
    logout.click();

    await waitFor(() =>
      expect(
        screen.getByRole("heading", { name: /welcome back/i })
      ).toBeInTheDocument()
    );

    expect(localStorage.getItem("examnexus_token")).toBeNull();
    expect(window.location.hash).toBe(""); // cleared
  });
});