import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import RequirementUnderstanding from "../components/admin/RequirementUnderstanding";
import { stubFetch, jsonResponse } from "./helpers";

describe("Phase 7 — AI-assisted features", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  const EXAM = { id: 42, name: "End Sem CSE", status: "DRAFT" };

  // -------------------------------------------------------
  // AI-01 — understand a supported requirement
  // -------------------------------------------------------
  it("AI-01: understanding a supported requirement lists recognised options", async () => {
    const user = userEvent.setup();

    stubFetch([
      ["POST /api/requirements/understand", () => jsonResponse({
        success: true,
        requirements: { minimize_halls: true, avoid_timetable_conflicts: true },
        unsupported_requirements: [],
        blocking_requirements: [],
      })],
      ["*", () => jsonResponse({}, { status: 404 })],
    ]);

    render(
      <RequirementUnderstanding
        examinationId="42"
        examination={EXAM}
        bulkExaminationIds={[]}
        onApplied={() => {}}
        onMessage={() => {}}
      />
    );

    await user.type(
      screen.getByLabelText(/examination requirement/i),
      "Use minimum number of halls, avoid timetable conflicts."
    );
    await user.click(
      screen.getByRole("button", { name: /understand requirements/i })
    );

    // Scope to the results panel so we don't match the textarea text.
    const panelHeading = await screen.findByRole(
      "heading",
      { name: /interpreted requirements/i }
    );
    const panel = panelHeading.closest("div")?.parentElement?.parentElement;
    const scope = panel ? within(panel) : screen;

    expect(scope.getByText(/minimize number of halls/i)).toBeInTheDocument();
    expect(scope.getByText(/avoid timetable conflicts/i)).toBeInTheDocument();
  });

  // -------------------------------------------------------
  // AI-02 — lifecycle instructions are refused
  // -------------------------------------------------------
  it("AI-02: lifecycle instructions are hard-blocked before preview", async () => {
    const user = userEvent.setup();

    stubFetch([
      ["POST /api/requirements/understand", () => jsonResponse({
        success: true,
        requirements: {},
        unsupported_requirements: [],
        blocking_requirements: [
          { requirement: "approve this examination", reason: "Lifecycle actions are admin-only." },
        ],
      })],
      ["*", () => jsonResponse({}, { status: 404 })],
    ]);

    render(
      <RequirementUnderstanding
        examinationId="42"
        examination={EXAM}
        bulkExaminationIds={[]}
        onApplied={() => {}}
        onMessage={() => {}}
      />
    );

    await user.type(
      screen.getByLabelText(/examination requirement/i),
      "Approve this examination and publish results."
    );
    await user.click(
      screen.getByRole("button", { name: /understand requirements/i })
    );

    expect(
      await screen.findByText(/administrator-only instructions/i)
    ).toBeInTheDocument();
  });

  // -------------------------------------------------------
  // AI-03 — unsupported requires acknowledgement
  // -------------------------------------------------------
  it("AI-03: unsupported requirements require acknowledgement before preview", async () => {
    const user = userEvent.setup();

    stubFetch([
      ["POST /api/requirements/understand", () => jsonResponse({
        success: true,
        requirements: { minimize_halls: true },
        unsupported_requirements: [
          { requirement: "magic quiet halls", reason: "Not supported by the allocator." },
        ],
        blocking_requirements: [],
      })],
      ["*", () => jsonResponse({}, { status: 404 })],
    ]);

    render(
      <RequirementUnderstanding
        examinationId="42"
        examination={EXAM}
        bulkExaminationIds={[]}
        onApplied={() => {}}
        onMessage={() => {}}
      />
    );

    await user.type(
      screen.getByLabelText(/examination requirement/i),
      "Use minimum halls and magic quiet halls."
    );
    await user.click(
      screen.getByRole("button", { name: /understand requirements/i })
    );

    // The section heading "Unsupported Requirements" is unique
    // by role (h3). The stray <p> hint and the checkbox label
    // are not headings, so this is unambiguous.
    await screen.findByRole(
      "heading",
      { name: /unsupported requirements/i }
    );

    const preview = screen.getByRole("button", { name: /preview proposal/i });
    expect(preview).toBeDisabled();

    // Acknowledge, then expect preview to enable.
    const checkbox = screen.getByRole("checkbox");
    await user.click(checkbox);
    await waitFor(() => expect(preview).toBeEnabled());
  });
});