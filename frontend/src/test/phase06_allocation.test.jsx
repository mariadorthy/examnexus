import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import App from "../App";
import { stubFetch, jsonResponse, ADMIN_USER, seedUser } from "./helpers";

async function goToAllocations(user) {
  seedUser(ADMIN_USER);
  render(<App />);
  await waitFor(() =>
    expect(screen.getByRole("heading", { name: /^dashboard$/i })).toBeInTheDocument()
  );
  const sidebar = screen.getByRole("complementary");
  const btn = Array.from(sidebar.querySelectorAll("button")).find(
    (b) => b.textContent.trim() === "Allocations"
  );
  await user.click(btn);
}

describe("Phase 6 — Allocation workspace", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  // -------------------------------------------------------
  // LFC-02 — no examination selected ⇒ Generate disabled
  // -------------------------------------------------------
  it("LFC-02: without a selected examination, Generate is disabled", async () => {
    const user = userEvent.setup();

    stubFetch([
      ["GET /api/dashboard/", () => jsonResponse({
        success: true, statistics: {}, upcoming_examinations: [],
        recent_activity: [], allocation: {}, system_status: {},
      })],
      ["GET /api/examinations/", () => jsonResponse([])],
      ["*", () => jsonResponse({}, { status: 404 })],
    ]);

    await goToAllocations(user);

    // The "Select an examination" heading appears (role=heading,
    // level 3, exact text). No ambiguity with <option>/<p>.
    await waitFor(() =>
      expect(
        screen.getByRole("heading", { level: 3, name: /^select an examination$/i })
      ).toBeInTheDocument()
    );

    const gen = screen.getByRole("button", { name: /generate allocation/i });
    expect(gen).toBeDisabled();
  });

  // -------------------------------------------------------
  // LFC-03 — selecting an exam loads summary
  // -------------------------------------------------------
  it("LFC-03: selecting an examination loads summary cards", async () => {
    const user = userEvent.setup();

    stubFetch([
      ["GET /api/dashboard/", () => jsonResponse({
        success: true, statistics: {}, upcoming_examinations: [],
        recent_activity: [], allocation: {}, system_status: {},
      })],
      ["GET /api/examinations/", () => jsonResponse([
        { id: 42, name: "End Sem CSE" },
      ])],
      ["GET /api/allocations/summary/42", () => jsonResponse({
        eligible_students: 55, halls_used: 2, allocated_capacity: 60, status: "VALID",
      })],
      ["GET /api/allocations/42", () => jsonResponse([])],
      ["*", () => jsonResponse({}, { status: 404 })],
    ]);

    await goToAllocations(user);

    const select = await screen.findByLabelText(/select examination/i);
    await user.selectOptions(select, "42");

    await waitFor(() =>
      expect(screen.getByText("55")).toBeInTheDocument()
    );
    expect(screen.getByText(/no hall allocations found/i)).toBeInTheDocument();
  });
});