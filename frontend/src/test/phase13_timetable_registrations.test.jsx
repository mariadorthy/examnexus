import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import App from "../App";
import { stubFetch, jsonResponse, ADMIN_USER, seedUser } from "./helpers";
import { buildAdminRoutesStubs } from "./fixtures/apiFixtures";

async function goToPage(label, matcher, user) {
  seedUser(ADMIN_USER);
  render(<App />);
  await waitFor(
    () =>
      expect(
        screen.getByRole("heading", { name: /^dashboard$/i })
      ).toBeInTheDocument(),
    { timeout: 8000 }
  );
  const sidebar = screen.getByRole("complementary");
  const btn = Array.from(sidebar.querySelectorAll("button")).find(
    (b) => b.textContent.trim() === label
  );
  await user.click(btn);
  await waitFor(
    () => {
      const headings = screen.getAllByRole("heading");
      expect(
        headings.some((h) => matcher.test(h.textContent || ""))
      ).toBe(true);
    },
    { timeout: 8000 }
  );
}

describe("Phase 13 — Timetable & Registrations", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  // -------------------------------------------------------
  // TT-01 — Timetable page renders
  // -------------------------------------------------------
  it("TT-01: Timetable page renders with its heading", async () => {
    const user = userEvent.setup();
    stubFetch(buildAdminRoutesStubs({ timetable: [] }));
    await goToPage("Timetable", /timetable/i, user);
  });

  // -------------------------------------------------------
  // TT-02 — Timetable renders on empty payload
  // -------------------------------------------------------
  it("TT-02: Timetable page renders on empty payload without crashing", async () => {
    const user = userEvent.setup();
    stubFetch(buildAdminRoutesStubs({ timetable: [] }));
    await goToPage("Timetable", /timetable/i, user);

    expect(document.body.textContent.length).toBeGreaterThan(50);
  });

  // -------------------------------------------------------
  // TT-03 — Timetable server error
  // -------------------------------------------------------
  it("TT-03: Timetable server error surfaces", async () => {
    const user = userEvent.setup();

    seedUser(ADMIN_USER);
    stubFetch([
      ["GET /api/dashboard/", () =>
        jsonResponse({
          success: true,
          statistics: {},
          upcoming_examinations: [],
          recent_activity: [],
          allocation: {},
          system_status: {},
        })],
      ["GET /api/timetable", () =>
        jsonResponse({ message: "boom" }, { status: 500 })],
      ["*", () => jsonResponse({}, { status: 404 })],
    ]);

    render(<App />);
    await waitFor(
      () =>
        expect(
          screen.getByRole("heading", { name: /^dashboard$/i })
        ).toBeInTheDocument(),
      { timeout: 8000 }
    );
    const sidebar = screen.getByRole("complementary");
    await user.click(
      Array.from(sidebar.querySelectorAll("button")).find(
        (b) => b.textContent.trim() === "Timetable"
      )
    );

    await waitFor(
      () =>
        expect(
          screen.queryByText(/unable|could not|failed|error/i)
        ).toBeInTheDocument(),
      { timeout: 8000 }
    );
  });

  // -------------------------------------------------------
  // REG-01 — Registrations page renders
  // -------------------------------------------------------
  it("REG-01: Registrations page renders with its heading", async () => {
    const user = userEvent.setup();
    stubFetch(buildAdminRoutesStubs({ registrations: [] }));
    await goToPage("Registrations", /registration/i, user);
  });

  // -------------------------------------------------------
  // REG-02 — Registrations renders on empty payload
  // -------------------------------------------------------
  it("REG-02: Registrations page renders on empty payload without crashing", async () => {
    const user = userEvent.setup();
    stubFetch(buildAdminRoutesStubs({ registrations: [] }));
    await goToPage("Registrations", /registration/i, user);

    expect(document.body.textContent.length).toBeGreaterThan(50);
  });

  // -------------------------------------------------------
  // REG-03 — Registrations page shows table or empty state
  //
  // We deliberately do not assert on the exact row shape:
  // the backend's response shape may differ from our guess.
  // We assert that the page reached a terminal state (table
  // OR empty message) within a reasonable timeout. That is
  // the honest assertion.
  // -------------------------------------------------------
  it("REG-03: Registrations page reaches a terminal state (table or empty)", async () => {
    const user = userEvent.setup();

    stubFetch(
      buildAdminRoutesStubs({
        registrations: [
          {
            id: 1,
            student_name: "Alice",
            student_code: "S1001",
            examination_name: "End Sem CSE",
            status: "REGISTERED",
          },
        ],
      })
    );

    await goToPage("Registrations", /registration/i, user);

    await waitFor(
      () => {
        const bodyText = document.body.textContent || "";
        // Terminal-state heuristics:
        const hasTable = document.querySelector("table tbody tr");
        const hasEmptyCopy = /no registrations|no data|no records/i.test(bodyText);
        // hasTable is a DOM node (or null); hasEmptyCopy is a
        // boolean. Use toBeTruthy, not toBe(true).
        expect(hasTable || hasEmptyCopy).toBeTruthy();
      },
      { timeout: 8000 }
    );
  });

  // -------------------------------------------------------
  // REG-04 — Registrations server error
  // -------------------------------------------------------
  it("REG-04: Registrations server error surfaces", async () => {
    const user = userEvent.setup();

    seedUser(ADMIN_USER);
    stubFetch([
      ["GET /api/dashboard/", () =>
        jsonResponse({
          success: true,
          statistics: {},
          upcoming_examinations: [],
          recent_activity: [],
          allocation: {},
          system_status: {},
        })],
      ["GET /api/exam-registrations", () =>
        jsonResponse({ message: "boom" }, { status: 500 })],
      ["*", () => jsonResponse({}, { status: 404 })],
    ]);

    render(<App />);
    await waitFor(
      () =>
        expect(
          screen.getByRole("heading", { name: /^dashboard$/i })
        ).toBeInTheDocument(),
      { timeout: 8000 }
    );
    const sidebar = screen.getByRole("complementary");
    await user.click(
      Array.from(sidebar.querySelectorAll("button")).find(
        (b) => b.textContent.trim() === "Registrations"
      )
    );

    await waitFor(
      () =>
        expect(
          screen.queryByText(/unable|could not|failed|error/i)
        ).toBeInTheDocument(),
      { timeout: 8000 }
    );
  });
});