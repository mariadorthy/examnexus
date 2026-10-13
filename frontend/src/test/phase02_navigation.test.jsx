import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import App from "../App";
import { stubFetch, jsonResponse, ADMIN_USER, seedUser } from "./helpers";
import {
  POPULATED_DASHBOARD,
  buildAdminRoutesStubs,
} from "./fixtures/apiFixtures";

// =========================================================
// PHASE 2 — NAVIGATION (corrected)
//
// Split into small per-page tests (jsdom is slow; putting all
// 12 pages in one test exceeded the default timeout).
//
// Assertions use `getAllByRole` because Admin pages render
// several headings that share a keyword (e.g. "Timetable" h1,
// "Timetable" h2, "Existing Timetables" h3).
// =========================================================

async function renderLoggedInAdmin(fetchRules) {
  seedUser(ADMIN_USER);
  stubFetch(fetchRules);

  // Guard: the hash router must start on Dashboard.
  expect(
    ["", "#/", "#/Dashboard"].includes(window.location.hash)
  ).toBe(true);

  render(<App />);
  await waitFor(
    () => expect(screen.getByRole("heading", { name: /^dashboard$/i })).toBeInTheDocument(),
    { timeout: 8000 }
  );
}

function sidebarButton(label) {
  const sidebar = screen.getByRole("complementary");
  return within(sidebar).getByRole("button", { name: new RegExp(`^${label}$`, "i") });
}

async function clickSidebarAndWait(label, matcher) {
  const user = userEvent.setup();
  await user.click(sidebarButton(label));
  await waitFor(() => {
    const nodes = screen.getAllByRole("heading");
    const found = nodes.some((n) => matcher.test(n.textContent || ""));
    expect(found).toBe(true);
  }, { timeout: 8000 });
}

describe("Phase 2 — Navigation", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  // -------------------------------------------------------
  // NAV-01a..l — one test per sidebar entry
  // -------------------------------------------------------
  const PAGES = [
    { label: "Departments",   matcher: /departments/i },
    { label: "Courses",       matcher: /courses/i },
    { label: "Subjects",      matcher: /subjects/i },
    { label: "Students",      matcher: /students/i },
    { label: "Staff",         matcher: /staff/i },
    { label: "Examinations",  matcher: /examinations/i },
    { label: "Timetable",     matcher: /timetable/i },
    { label: "Registrations", matcher: /registration/i },
    { label: "Halls",         matcher: /hall/i },
    { label: "Allocations",   matcher: /allocation/i },
    { label: "Hall Tickets",  matcher: /hall ticket/i },
    { label: "Reports",       matcher: /report/i },
  ];

  for (const page of PAGES) {
    it(`NAV-01: sidebar "${page.label}" opens the ${page.label} page`, async () => {
      await renderLoggedInAdmin(buildAdminRoutesStubs());
      await clickSidebarAndWait(page.label, page.matcher);
    });
  }

  // -------------------------------------------------------
  // NAV-02 — dashboard Quick Actions
  // -------------------------------------------------------
  it("NAV-02a: Quick Action 'Create Examination' opens Examinations", async () => {
    const user = userEvent.setup();
    await renderLoggedInAdmin(buildAdminRoutesStubs({ dashboard: POPULATED_DASHBOARD }));

    await user.click(screen.getByRole("button", { name: /create examination/i }));
    await waitFor(() => {
      const headings = screen.getAllByRole("heading");
      expect(headings.some((h) => /examinations/i.test(h.textContent || ""))).toBe(true);
    }, { timeout: 8000 });
  });

  it("NAV-02b: Quick Action 'Manage Timetable' opens Timetable", async () => {
    const user = userEvent.setup();
    await renderLoggedInAdmin(buildAdminRoutesStubs({ dashboard: POPULATED_DASHBOARD }));

    await user.click(screen.getByRole("button", { name: /manage timetable/i }));
    await waitFor(() => {
      const headings = screen.getAllByRole("heading");
      expect(headings.some((h) => /timetable/i.test(h.textContent || ""))).toBe(true);
    }, { timeout: 8000 });
  });

  it("NAV-02c: Quick Action 'Examination Allocation' opens Allocations", async () => {
    const user = userEvent.setup();
    await renderLoggedInAdmin(buildAdminRoutesStubs({ dashboard: POPULATED_DASHBOARD }));

    await user.click(screen.getByRole("button", { name: /examination allocation/i }));
    await waitFor(() => {
      const headings = screen.getAllByRole("heading");
      expect(headings.some((h) => /allocation/i.test(h.textContent || ""))).toBe(true);
    }, { timeout: 8000 });
  });

  // -------------------------------------------------------
  // NAV-05 — no user ⇒ Login
  // -------------------------------------------------------
  it("NAV-05: without a stored user, only Login is rendered", () => {
    stubFetch(buildAdminRoutesStubs());
    render(<App />);

    expect(screen.getByRole("heading", { name: /welcome back/i })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /^dashboard$/i })).not.toBeInTheDocument();
  });

  // -------------------------------------------------------
  // NAV-06 — unknown role ⇒ Login
  // -------------------------------------------------------
  it("NAV-06: unknown role falls back to Login", async () => {
    seedUser({ id: 99, name: "Weird", email: "x@y.z", role: "guest" });
    stubFetch(buildAdminRoutesStubs());

    const errSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    render(<App />);

    await waitFor(() =>
      expect(screen.getByRole("heading", { name: /welcome back/i })).toBeInTheDocument()
    );
    errSpy.mockRestore();
  });

  // -------------------------------------------------------
  // NAV-07 — public verify route needs no auth
  // -------------------------------------------------------
  it("NAV-07: /verify-hall-ticket/* renders without authentication", async () => {
    window.history.pushState({}, "", "/verify-hall-ticket/abc123");
    stubFetch([["*", () => jsonResponse({ message: "no verification" }, { status: 404 })]]);
    render(<App />);

    await waitFor(() =>
      expect(screen.queryByRole("heading", { name: /welcome back/i })).not.toBeInTheDocument()
    );
    window.history.pushState({}, "", "/");
  });

  // -------------------------------------------------------
  // Regression lock — DEF-01
  // -------------------------------------------------------
  it("REGRESSION-LOCK DEF-01: unknown pathname still opens on Dashboard", async () => {
    window.history.pushState({}, "", "/something-not-a-real-route");
    await renderLoggedInAdmin(buildAdminRoutesStubs());
    expect(screen.getByRole("heading", { name: /^dashboard$/i })).toBeInTheDocument();
    window.history.pushState({}, "", "/");
  });
});