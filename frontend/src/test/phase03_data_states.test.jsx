import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

import App from "../App";
import { stubFetch, jsonResponse, htmlResponse, ADMIN_USER, seedUser } from "./helpers";
import { buildAdminRoutesStubs } from "./fixtures/apiFixtures";

// =========================================================
// PHASE 3 — DATA STATES
//
// Loading, empty, error, and the empty-vs-error distinction.
// =========================================================

async function mountDepartments(rules) {
  seedUser(ADMIN_USER);
  stubFetch(rules);
  render(<App />);

  // Wait for dashboard then click Departments.
  await waitFor(() =>
    expect(screen.getByRole("heading", { name: /^dashboard$/i })).toBeInTheDocument()
  );
  const sidebar = screen.getByRole("complementary");
  const btn = Array.from(sidebar.querySelectorAll("button")).find(
    (b) => b.textContent.trim() === "Departments"
  );
  btn.click();

  return await screen.findByPlaceholderText(/search departments/i);
}

describe("Phase 3 — Data states", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  // -------------------------------------------------------
  // STA-02 — empty state
  // -------------------------------------------------------
  it("STA-02: empty Departments shows the 'no data' message, not an error", async () => {
    await mountDepartments(
      buildAdminRoutesStubs({ departments: [] })
    );

    expect(await screen.findByText(/no departments yet/i)).toBeInTheDocument();
    expect(screen.queryByText(/unable to load departments/i)).not.toBeInTheDocument();
  });

  // -------------------------------------------------------
  // STA-03 — filtered-empty state (search)
  // -------------------------------------------------------
  it("STA-03: search with no matches shows 'No departments found'", async () => {
    await mountDepartments(
      buildAdminRoutesStubs({
        departments: [
          { id: 1, department_code: "CSE", department_name: "Computer Science", is_active: true },
        ],
      })
    );

    expect(await screen.findByText(/computer science/i)).toBeInTheDocument();

    const searchBox = screen.getByPlaceholderText(/search departments/i);
    const { default: userEvent } = await import("@testing-library/user-event");
    const user = userEvent.setup();
    await user.type(searchBox, "zzzz-no-match");

    await waitFor(() =>
      expect(screen.getByText(/no departments found/i)).toBeInTheDocument()
    );
  });

  // -------------------------------------------------------
  // STA-04 — backend error
  // -------------------------------------------------------
  it("STA-04: backend error shows the error banner with Retry", async () => {
    seedUser(ADMIN_USER);
    stubFetch([
      ["GET /api/dashboard/", () => jsonResponse({ success: true, statistics: {}, upcoming_examinations: [], recent_activity: [], allocation: {}, system_status: {} })],
      ["GET /api/departments", () => jsonResponse({ message: "boom" }, { status: 500 })],
      ["*", () => jsonResponse({}, { status: 404 })],
    ]);

    render(<App />);
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: /^dashboard$/i })).toBeInTheDocument()
    );

    const sidebar = screen.getByRole("complementary");
    const btn = Array.from(sidebar.querySelectorAll("button")).find(
      (b) => b.textContent.trim() === "Departments"
    );
    btn.click();

    expect(
      await screen.findByText(/unable to load departments/i)
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });

  // -------------------------------------------------------
  // STA-04b — DEF-12 REGRESSION LOCK
  //
  // Confirmed defect: on API failure, Departments ALSO
  // renders the "No departments yet — Create your first
  // department" copy, which is misleading. When DEF-12 is
  // fixed, this test will fail and must be flipped to assert
  // the error copy alone.
  // -------------------------------------------------------
  it("DEF-12 fixed: error state does NOT also show the empty-state message", async () => {
  seedUser(ADMIN_USER);
  stubFetch([
    ["GET /api/dashboard/", () => jsonResponse({ success: true, statistics: {}, upcoming_examinations: [], recent_activity: [], allocation: {}, system_status: {} })],
    ["GET /api/departments", () => jsonResponse({ message: "boom" }, { status: 500 })],
    ["*", () => jsonResponse({}, { status: 404 })],
  ]);

  render(<App />);
  await waitFor(() =>
    expect(screen.getByRole("heading", { name: /^dashboard$/i })).toBeInTheDocument()
  );

  const sidebar = screen.getByRole("complementary");
  const btn = Array.from(sidebar.querySelectorAll("button")).find(
    (b) => b.textContent.trim() === "Departments"
  );
  btn.click();

      await screen.findByText(/unable to load departments/i);

    // Fixed: only the error appears, not the empty-state copy.
    expect(screen.queryByText(/no departments yet/i)).not.toBeInTheDocument();
    expect(
      screen.getByText(/could not load departments/i)
    ).toBeInTheDocument();
});

// -------------------------------------------------------
// STA-04c — non-JSON HTML error body (server up, bad body)
// -------------------------------------------------------
it("STA-04c: HTML 500 does not crash the Departments page", async () => {
  seedUser(ADMIN_USER);
  stubFetch([
    ["GET /api/dashboard/", () => jsonResponse({ success: true, statistics: {}, upcoming_examinations: [], recent_activity: [], allocation: {}, system_status: {} })],
    ["GET /api/departments", () => htmlResponse("<html>502 Bad Gateway</html>", { status: 500 })],
    ["*", () => jsonResponse({}, { status: 404 })],
  ]);

  render(<App />);
  await waitFor(() =>
    expect(screen.getByRole("heading", { name: /^dashboard$/i })).toBeInTheDocument()
  );

  const sidebar = screen.getByRole("complementary");
  const btn = Array.from(sidebar.querySelectorAll("button")).find(
    (b) => b.textContent.trim() === "Departments"
  );
  btn.click();

  // Must show a readable message; must NOT throw.
  expect(
    await screen.findByText(/unable to load departments/i)
  ).toBeInTheDocument();
});

// -------------------------------------------------------
// STA-05 — connection refused
// -------------------------------------------------------
it("STA-05: ECONNREFUSED shows an error (dashboard)", async () => {
  seedUser(ADMIN_USER);
  stubFetch([
    ["GET /api/dashboard/", () => Promise.reject(new TypeError("Failed to fetch"))],
    ["*", () => jsonResponse({ message: "Not stubbed" }, { status: 500 })],
  ]);
  render(<App />);

  // Dashboard shows its own error banner.
  expect(
    await screen.findByText(/unable to load dashboard data/i)
  ).toBeInTheDocument();
});
});