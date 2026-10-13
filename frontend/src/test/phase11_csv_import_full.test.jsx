import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import CsvImport from "../components/admin/CsvImport/CsvImport";

function makeFile(name, content = "a,b\n1,2\n", type = "text/csv") {
  return new File([content], name, { type });
}

function forceUpload(input, file) {
  fireEvent.change(input, { target: { files: [file] } });
}

describe("Phase 11 — CSV import (full flow)", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  // -------------------------------------------------------
  // FRM-11.1 — full valid flow: validate then import
  // -------------------------------------------------------
  it("FRM-11.1: all-valid CSV → VALID banner → Import → success screen", async () => {
    const user = userEvent.setup();
    let importCalled = false;

    render(
      <CsvImport
        entity="departments"
        isOpen
        onClose={() => {}}
        onValidate={() => Promise.resolve({
          success: true,
          valid: true,
          total_rows: 2,
          valid_rows: 2,
          invalid_rows: 0,
          duplicate_rows: 0,
          summary: { warning_count: 0 },
          rows: [
            { row_number: 1, status: "valid", data: { department_code: "CSE", department_name: "CS" }, issues: [] },
            { row_number: 2, status: "valid", data: { department_code: "ECE", department_name: "EC" }, issues: [] },
          ],
        })}
        onImport={() => {
          importCalled = true;
          return Promise.resolve({
            success: true,
            summary: {
              total_rows: 2,
              imported_rows: 2,
              invalid_rows: 0,
              duplicate_rows: 0,
            },
          });
        }}
      />
    );

    forceUpload(screen.getByLabelText(/csv file/i), makeFile("departments.csv"));
    await user.click(screen.getByRole("button", { name: /validate csv/i }));

    expect(
      await screen.findByText(/VALID — all rows are ready to import/i)
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /import valid rows/i }));

    expect(await screen.findByText(/import completed/i)).toBeInTheDocument();
    expect(importCalled).toBe(true);
  });

  // -------------------------------------------------------
  // FRM-11.2 — per-row error rendering
  // -------------------------------------------------------
  it("FRM-11.2: invalid rows show their error message in the preview", async () => {
    const user = userEvent.setup();

    render(
      <CsvImport
        entity="departments"
        isOpen
        onClose={() => {}}
        onValidate={() => Promise.resolve({
          success: true,
          valid: false,
          total_rows: 2,
          valid_rows: 1,
          invalid_rows: 1,
          duplicate_rows: 0,
          summary: { warning_count: 0 },
          rows: [
            { row_number: 1, status: "valid",   data: { department_code: "CSE" }, issues: [] },
            { row_number: 2, status: "invalid", data: { department_code: "" },    issues: [{ severity: "error", message: "Department code is required" }] },
          ],
        })}
        onImport={() => Promise.resolve({})}
      />
    );

    forceUpload(screen.getByLabelText(/csv file/i), makeFile("departments.csv"));
    await user.click(screen.getByRole("button", { name: /validate csv/i }));

    expect(
      await screen.findByText(/department code is required/i)
    ).toBeInTheDocument();
  });

  // -------------------------------------------------------
  // FRM-11.3 — validate call failure surfaces error
  // -------------------------------------------------------
  it("FRM-11.3: validate error shows the error banner", async () => {
    const user = userEvent.setup();

    render(
      <CsvImport
        entity="departments"
        isOpen
        onClose={() => {}}
        onValidate={() => Promise.reject(new Error("Server unavailable."))}
        onImport={() => Promise.resolve({})}
      />
    );

    forceUpload(screen.getByLabelText(/csv file/i), makeFile("departments.csv"));
    await user.click(screen.getByRole("button", { name: /validate csv/i }));

    expect(
      await screen.findByText(/server unavailable/i)
    ).toBeInTheDocument();
  });

  // -------------------------------------------------------
  // FRM-11.4 — import failure surfaces error
  // -------------------------------------------------------
  it("FRM-11.4: import error shows the error banner", async () => {
    const user = userEvent.setup();

    render(
      <CsvImport
        entity="departments"
        isOpen
        onClose={() => {}}
        onValidate={() => Promise.resolve({
          success: true, valid: true,
          total_rows: 1, valid_rows: 1, invalid_rows: 0, duplicate_rows: 0,
          summary: { warning_count: 0 },
          rows: [{ row_number: 1, status: "valid", data: {}, issues: [] }],
        })}
        onImport={() => Promise.reject(new Error("DB write failed."))}
      />
    );

    forceUpload(screen.getByLabelText(/csv file/i), makeFile("departments.csv"));
    await user.click(screen.getByRole("button", { name: /validate csv/i }));
    await screen.findByText(/VALID — all rows are ready to import/i);
    await user.click(screen.getByRole("button", { name: /import valid rows/i }));

    expect(await screen.findByText(/DB write failed/i)).toBeInTheDocument();
  });

  // -------------------------------------------------------
  // FRM-11.5 — Choose Another File resets state
  // -------------------------------------------------------
  it("FRM-11.5: choosing another file resets the preview", async () => {
    const user = userEvent.setup();

    render(
      <CsvImport
        entity="departments"
        isOpen
        onClose={() => {}}
        onValidate={() => Promise.resolve({
          success: true, valid: true,
          total_rows: 1, valid_rows: 1, invalid_rows: 0, duplicate_rows: 0,
          summary: { warning_count: 0 },
          rows: [],
        })}
        onImport={() => Promise.resolve({})}
      />
    );

    forceUpload(screen.getByLabelText(/csv file/i), makeFile("departments.csv"));
    await user.click(screen.getByRole("button", { name: /validate csv/i }));
    await screen.findByText(/VALID — all rows are ready to import/i);

    await user.click(screen.getByRole("button", { name: /choose another file/i }));

    // After reset, the preview banner should be gone.
    expect(
      screen.queryByText(/VALID — all rows are ready to import/i)
    ).not.toBeInTheDocument();
  });
});