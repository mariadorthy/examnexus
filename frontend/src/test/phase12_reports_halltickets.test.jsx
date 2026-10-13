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

describe("Phase 12 — Reports & Hall Tickets", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  // -------------------------------------------------------
  // RPT-01 — Reports page renders
  // -------------------------------------------------------
  it("RPT-01: Reports page renders with its heading", async () => {
    const user = userEvent.setup();
    stubFetch(buildAdminRoutesStubs({ reports: [] }));
    await goToPage("Reports", /report/i, user);

    expect(
      screen.getAllByRole("heading").some(
        (h) => /report/i.test(h.textContent || "")
      )
    ).toBe(true);
  });

  // -------------------------------------------------------
  // RPT-02 — Reports page renders without errors on empty payload
  // -------------------------------------------------------
  it("RPT-02: Reports page renders on empty payload without crashing", async () => {
    const user = userEvent.setup();
    stubFetch(buildAdminRoutesStubs({ reports: [] }));
    await goToPage("Reports", /report/i, user);

    // Page must have rendered SOMETHING (not blank).
    expect(document.body.textContent.length).toBeGreaterThan(50);
  });

  // -------------------------------------------------------
  // HT-01 — Hall Tickets page renders
  // -------------------------------------------------------
  it("HT-01: Hall Tickets page renders with its heading", async () => {
    const user = userEvent.setup();
    stubFetch(buildAdminRoutesStubs({ hallTickets: [] }));
    await goToPage("Hall Tickets", /hall ticket/i, user);

    expect(
      screen.getAllByRole("heading").some(
        (h) => /hall ticket/i.test(h.textContent || "")
      )
    ).toBe(true);
  });

  // -------------------------------------------------------
  // HT-02 — Hall Tickets page renders on empty payload
  // -------------------------------------------------------
  it("HT-02: Hall Tickets page renders on empty payload without crashing", async () => {
    const user = userEvent.setup();
    stubFetch(buildAdminRoutesStubs({ hallTickets: [] }));
    await goToPage("Hall Tickets", /hall ticket/i, user);

    expect(document.body.textContent.length).toBeGreaterThan(50);
  });

  // -------------------------------------------------------
  // HT-03 — Hall Tickets backend error
  // -------------------------------------------------------
  it("HT-03: Hall Tickets backend error surfaces an error message", async () => {
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
      ["GET /api/hall-tickets", () =>
        jsonResponse(
          { message: "Hall tickets unavailable." },
          { status: 500 },
        )],
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
        (b) => b.textContent.trim() === "Hall Tickets"
      )
    );

    await waitFor(
      () =>
        expect(
          screen.queryByText(/unavailable|could not|unable to|error|failed/i)
        ).toBeInTheDocument(),
      { timeout: 8000 }
    );
  });
});

const err = new Error("This ticket has been superseded by a newer arrangement.");
err.response = {
  valid: false,
  status: "SUPERSEDED",
  student_name: "Joel Antonio",
  student_code: "BAEN262A001",
  student_semester: 2,
  student_batch: "2026-2028",
  examination: "End Semester Examination 2026",
  exam_type: "REGULAR",
  message: "This ticket has been superseded by a newer arrangement.",
  timetable: [],
};