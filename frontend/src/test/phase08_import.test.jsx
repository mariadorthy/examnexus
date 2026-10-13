import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import CsvImport from "../components/admin/CsvImport/CsvImport";

function makeFile(name, content = "a,b\n1,2\n", type = "text/csv") {
  return new File([content], name, { type });
}

// user-event refuses to "upload" a file whose MIME type or
// extension violates the input's `accept=` attribute. For
// tests that specifically exercise that rejection, we bypass
// the accept filter with fireEvent.change.
function forceUpload(input, file) {
  fireEvent.change(input, { target: { files: [file] } });
}

describe("Phase 8 — CSV import", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  // -------------------------------------------------------
  // FRM-06 — non-CSV rejection
  // -------------------------------------------------------
  it("FRM-06: selecting a non-CSV file is rejected client-side", async () => {
    render(
      <CsvImport
        entity="departments"
        isOpen
        onClose={() => {}}
        onValidate={() => Promise.resolve({})}
        onImport={() => Promise.resolve({})}
      />
    );

    const input = screen.getByLabelText(/csv file/i);
    forceUpload(input, makeFile("notes.txt", "hello", "text/plain"));

    expect(
      await screen.findByText(/please select a csv file/i)
    ).toBeInTheDocument();
  });

  // -------------------------------------------------------
  // FRM-07a — partial validity banner
  // -------------------------------------------------------
  it("FRM-07a: partial validity shows a PARTIAL banner", async () => {
    const user = userEvent.setup();

    render(
      <CsvImport
        entity="departments"
        isOpen
        onClose={() => {}}
        onValidate={() => Promise.resolve({
          success: true, valid: false,
          total_rows: 5, valid_rows: 3, invalid_rows: 1, duplicate_rows: 1,
          summary: { warning_count: 0 },
          rows: [
            { row_number: 1, status: "valid", data: { department_code: "CSE" }, issues: [] },
            { row_number: 2, status: "invalid", data: {}, issues: [{ severity: "error", message: "Missing code" }] },
            { row_number: 3, status: "duplicate", data: { department_code: "CSE" }, issues: [{ severity: "warning", message: "Duplicate" }] },
          ],
        })}
        onImport={() => Promise.resolve({})}
      />
    );

    const input = screen.getByLabelText(/csv file/i);
    forceUpload(input, makeFile("departments.csv"));
    await user.click(screen.getByRole("button", { name: /validate csv/i }));

    expect(
      await screen.findByText(/^PARTIAL/i)
    ).toBeInTheDocument();
  });

  // -------------------------------------------------------
  // FRM-07b — Import disabled when zero valid rows
  // -------------------------------------------------------
  it("FRM-07b: Import is disabled when there are zero valid rows", async () => {
    const user = userEvent.setup();

    render(
      <CsvImport
        entity="departments"
        isOpen
        onClose={() => {}}
        onValidate={() => Promise.resolve({
          success: true, valid: false,
          total_rows: 3, valid_rows: 0, invalid_rows: 3, duplicate_rows: 0,
          summary: { warning_count: 0 },
          rows: [],
        })}
        onImport={() => Promise.resolve({})}
      />
    );

    const input = screen.getByLabelText(/csv file/i);
    forceUpload(input, makeFile("departments.csv"));
    await user.click(screen.getByRole("button", { name: /validate csv/i }));

    // Assert on the specific banner text — the summary card
    // also contains the word "Invalid", so a loose regex
    // matched twice.
    expect(
      await screen.findByText(/^INVALID —/i)
    ).toBeInTheDocument();

    expect(screen.getByRole("button", { name: /import valid rows/i })).toBeDisabled();
  });
});