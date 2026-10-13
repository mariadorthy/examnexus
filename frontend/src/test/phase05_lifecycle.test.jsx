import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

import ApprovalPanel from "../pages/admin/allocations/ApprovalPanel";
import { stubFetch, jsonResponse } from "./helpers";

describe("Phase 5 — Examination lifecycle", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  const EXAMS = [
    { id: 7, name: "End Sem CSE", exam_type: "THEORY", start_date: "2026-11-01", status: "GENERATED" },
  ];

  // -------------------------------------------------------
  // LFC-04 — Publish blocked when validation is not VALID
  // -------------------------------------------------------
  it("LFC-04: action is disabled when validators are not VALID", async () => {
    stubFetch([
      ["GET /api/examinations/7", () => jsonResponse({
        id: 7, name: "End Sem CSE", status: "GENERATED",
      })],
      ["GET /api/allocations/validate/7", () => jsonResponse({
        status: "INVALID", errors: ["Some students unallocated."],
      })],
      ["GET /api/allocations/invigilators/validate/7", () => jsonResponse({
        status: "VALID",
      })],
      ["*", () => jsonResponse({}, { status: 404 })],
    ]);

    render(
      <ApprovalPanel
        examinations={EXAMS}
        selectedExamination="7"
        onSelectExamination={() => {}}
        onMessage={() => {}}
      />
    );

    // Blocking banner appears.
    expect(
      await screen.findByText(/this action is currently blocked/i)
    ).toBeInTheDocument();

    // And the button is disabled.
    const action = screen.getByRole("button", { name: /mark as validated/i });
    expect(action).toBeDisabled();
  });

  // -------------------------------------------------------
  // LFC-04b — validators VALID ⇒ button enabled
  // -------------------------------------------------------
  it("LFC-04b: action is enabled when both validators are VALID", async () => {
    stubFetch([
      ["GET /api/examinations/7", () => jsonResponse({
        id: 7, name: "End Sem CSE", status: "GENERATED",
      })],
      ["GET /api/allocations/validate/7", () => jsonResponse({ status: "VALID" })],
      ["GET /api/allocations/invigilators/validate/7", () => jsonResponse({ status: "VALID" })],
      ["*", () => jsonResponse({}, { status: 404 })],
    ]);

    render(
      <ApprovalPanel
        examinations={EXAMS}
        selectedExamination="7"
        onSelectExamination={() => {}}
        onMessage={() => {}}
      />
    );

    await waitFor(() =>
      expect(
        screen.queryByText(/this action is currently blocked/i)
      ).not.toBeInTheDocument()
    );

    const action = screen.getByRole("button", { name: /mark as validated/i });
    expect(action).toBeEnabled();
  });

  // -------------------------------------------------------
  // LFC-04c — validator load failure blocks the action
  // -------------------------------------------------------
  it("LFC-04c: validator load failure keeps the action disabled", async () => {
    stubFetch([
      ["GET /api/examinations/7", () => jsonResponse({
        id: 7, name: "End Sem CSE", status: "GENERATED",
      })],
      ["GET /api/allocations/validate/7", () => jsonResponse({ message: "boom" }, { status: 500 })],
      ["GET /api/allocations/invigilators/validate/7", () => jsonResponse({ status: "VALID" })],
      ["*", () => jsonResponse({}, { status: 404 })],
    ]);

    render(
      <ApprovalPanel
        examinations={EXAMS}
        selectedExamination="7"
        onSelectExamination={() => {}}
        onMessage={() => {}}
      />
    );

    await waitFor(() =>
      expect(
        screen.getByText(/this action is currently blocked/i)
      ).toBeInTheDocument()
    );

    const action = screen.getByRole("button", { name: /mark as validated/i });
    expect(action).toBeDisabled();
  });
});