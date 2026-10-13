import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import AllocationForm from "../pages/admin/allocations/AllocationForm";
import { stubFetch, jsonResponse } from "./helpers";

describe("Phase 4 — Forms & validation", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  const HALLS = [
    { id: 1, name: "Hall A", building_name: "B1", floor_no: 1, examination_capacity: 30, is_accessible: false },
    { id: 2, name: "Hall B", building_name: "B1", floor_no: 2, examination_capacity: 40, is_accessible: true },
  ];

  function renderForm({ allocation, onSuccess = () => {}, onClose = () => {} } = {}) {
    return render(
      <AllocationForm
        allocation={allocation}
        onSuccess={onSuccess}
        onClose={onClose}
      />
    );
  }

  // -------------------------------------------------------
  // FRM-01 — required field: no hall
  // -------------------------------------------------------
  it("FRM-01: submitting without a hall shows an inline error", async () => {
    const user = userEvent.setup();
    stubFetch([["GET /api/halls/", () => jsonResponse(HALLS)]]);

    const onSuccess = vi.fn();
    renderForm({
      allocation: { id: 10, hall_id: "", allocated_capacity: 20, purpose: "NORMAL" },
      onSuccess,
    });

    await screen.findByRole("option", { name: /hall a/i });
    await user.click(screen.getByRole("button", { name: /save changes/i }));

    expect(await screen.findByText(/please select a hall/i)).toBeInTheDocument();
    expect(onSuccess).not.toHaveBeenCalled();
  });

  // -------------------------------------------------------
  // FRM-02 — invalid capacity (0)
  // -------------------------------------------------------
  it("FRM-02: capacity of 0 is rejected", async () => {
    const user = userEvent.setup();
    stubFetch([["GET /api/halls/", () => jsonResponse(HALLS)]]);

    renderForm({
      allocation: { id: 10, hall_id: 1, allocated_capacity: 0, purpose: "NORMAL" },
    });

    await screen.findByRole("option", { name: /hall a/i });
    await user.click(screen.getByRole("button", { name: /save changes/i }));

    expect(
      await screen.findByText(/must be greater than zero/i)
    ).toBeInTheDocument();
  });

  // -------------------------------------------------------
  // FRM-02b — negative capacity
  // -------------------------------------------------------
  it("FRM-02b: negative capacity is rejected", async () => {
    const user = userEvent.setup();
    stubFetch([["GET /api/halls/", () => jsonResponse(HALLS)]]);

    renderForm({
      allocation: { id: 10, hall_id: 1, allocated_capacity: -5, purpose: "NORMAL" },
    });

    await screen.findByRole("option", { name: /hall a/i });
    await user.click(screen.getByRole("button", { name: /save changes/i }));

    expect(
      await screen.findByText(/must be greater than zero/i)
    ).toBeInTheDocument();
  });

  // -------------------------------------------------------
  // FRM-03 — server 4xx surfaces
  // -------------------------------------------------------
  it("FRM-03: server error on save is shown to the user", async () => {
    const user = userEvent.setup();
    stubFetch([
      ["GET /api/halls/", () => jsonResponse(HALLS)],
      ["PATCH /api/allocations/", () => jsonResponse({ message: "Capacity exceeds hall." }, { status: 422 })],
    ]);

    renderForm({
      allocation: { id: 10, hall_id: 1, allocated_capacity: 50, purpose: "NORMAL" },
    });

    await screen.findByRole("option", { name: /hall a/i });
    await user.click(screen.getByRole("button", { name: /save changes/i }));

    expect(
      await screen.findByText(/capacity exceeds hall/i)
    ).toBeInTheDocument();
  });

  // -------------------------------------------------------
  // FRM-04 — double-click safety
  // -------------------------------------------------------
  it("FRM-04: rapid double-click on Save sends only one PATCH", async () => {
    const user = userEvent.setup();

    let patchCount = 0;
    stubFetch([
      ["GET /api/halls/", () => jsonResponse(HALLS)],
      ["PATCH /api/allocations/", () => {
        patchCount += 1;
        // Slow enough that the second click lands while the first is in-flight.
        return new Promise((resolve) =>
          setTimeout(() => resolve(jsonResponse({ success: true })), 80)
        );
      }],
    ]);

    renderForm({
      allocation: { id: 10, hall_id: 1, allocated_capacity: 20, purpose: "NORMAL" },
    });

    await screen.findByRole("option", { name: /hall a/i });
    const save = screen.getByRole("button", { name: /save changes/i });

    await user.click(save);
    await user.click(save); // second click while disabled

    await waitFor(() => expect(patchCount).toBe(1), { timeout: 1000 });
  });
});