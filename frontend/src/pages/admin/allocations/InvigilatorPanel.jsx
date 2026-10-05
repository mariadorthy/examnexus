import { useEffect, useState } from "react";

import {
  Users,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  ShieldCheck,
} from "lucide-react";

import {
  generateInvigilators,
  getInvigilators,
  validateInvigilators,
  getInvigilatorWorkload,
} from "../../../services/invigilatorService";


function InvigilatorPanel({
  examinations,
  onMessage,
}) {
  const [selectedExamination, setSelectedExamination] =
    useState("");

  const [assignments, setAssignments] = useState([]);
  const [workload, setWorkload] = useState([]);
  const [validation, setValidation] = useState(null);

  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [validating, setValidating] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    if (selectedExamination) {
      loadData(selectedExamination);
    } else {
      setAssignments([]);
      setWorkload([]);
      setValidation(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedExamination]);

  const loadData = async (examinationId) => {
    try {
      setLoading(true);
      setError("");

      const [listData, workloadData] = await Promise.all([
        getInvigilators(examinationId),
        getInvigilatorWorkload(examinationId),
      ]);

      setAssignments(listData || []);
      setWorkload(workloadData || []);

      // validation may return 400 INVALID; treat gracefully
      try {
        const validationData =
          await validateInvigilators(examinationId);
        setValidation(validationData);
      } catch (validationError) {
        // fallback: run a "not generated" style check
        setValidation({
          status: "INVALID",
          errors: [
            validationError?.message ||
              "Unable to validate invigilator allocation",
          ],
        });
      }
    } catch (err) {
      console.error("Invigilator load error:", err);
      setError(
        err.message ||
          "Unable to load invigilator data."
      );
      setAssignments([]);
      setWorkload([]);
      setValidation(null);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async (force = false) => {
    if (!selectedExamination) {
      setError("Please select an examination first.");
      return;
    }

    const confirmed = window.confirm(
      force
        ? "Regenerate invigilator allocation for this examination? This clears existing assignments."
        : "Generate invigilator allocation for this examination?"
    );

    if (!confirmed) return;

    try {
      setGenerating(true);
      setError("");
      setSuccess("");

      const data = await generateInvigilators(
        selectedExamination,
        force
      );

      if (!data.success) {
        throw new Error(
          data.message ||
            "Failed to generate invigilator allocation."
        );
      }

      setSuccess(
        data.message ||
          "Invigilator allocation generated."
      );

      if (onMessage) {
        onMessage(
          data.message ||
            "Invigilator allocation generated.",
          "success"
        );
      }

      await loadData(selectedExamination);
    } catch (err) {
      console.error("Invigilator generation error:", err);

      const message =
        err.message ||
        "Unable to generate invigilator allocation.";

      setError(message);

      if (onMessage) {
        onMessage(message, "error");
      }
    } finally {
      setGenerating(false);
    }
  };

  const handleValidate = async () => {
    if (!selectedExamination) return;

    try {
      setValidating(true);
      setError("");
      setSuccess("");

      const data = await validateInvigilators(
        selectedExamination
      );

      setValidation(data);

      if (data.status === "VALID") {
        setSuccess(
          "Invigilator allocation is valid."
        );
      } else {
        setError(
          "Invigilator allocation validation failed."
        );
      }
    } catch (err) {
      console.error("Invigilator validation error:", err);

      setValidation({
        status: "INVALID",
        errors: [
          err.message ||
            "Unable to validate invigilator allocation.",
        ],
      });

      setError(
        err.message ||
          "Unable to validate invigilator allocation."
      );
    } finally {
      setValidating(false);
    }
  };

  const isValid =
    validation &&
    validation.status === "VALID";

  return (
    <>
      {/* ============================================ */}
      {/* SELECTOR + ACTIONS */}
      {/* ============================================ */}

      <section className="mb-6 rounded-2xl border border-border bg-surface p-5 shadow-sm md:p-6">

        <div className="grid gap-5 lg:grid-cols-[1fr_auto_auto] lg:items-end">

          <div>
            <label
              htmlFor="invigilator-examination"
              className="mb-2 block text-sm font-semibold text-sidebar"
            >
              Select Examination
            </label>

            <select
              id="invigilator-examination"
              value={selectedExamination}
              onChange={(event) =>
                setSelectedExamination(
                  event.target.value
                )
              }
              className="w-full rounded-xl border border-border bg-surface px-4 py-3.5 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
            >
              <option value="">
                Select an examination
              </option>

              {examinations.map((examination) => (
                <option
                  key={examination.id}
                  value={examination.id}
                >
                  {`Examination #${examination.id}`} —{" "}
                  {examination.name}
                </option>
              ))}
            </select>
          </div>

          <button
            type="button"
            onClick={() => handleGenerate(false)}
            disabled={
              !selectedExamination ||
              generating ||
              loading
            }
            className="flex items-center justify-center gap-2 rounded-xl bg-sidebar px-5 py-3.5 text-sm font-semibold text-white shadow-lg shadow-sidebar/10 transition hover:bg-primary disabled:cursor-not-allowed disabled:opacity-60"
          >
            {generating ? (
              <>
                <RefreshCw
                  size={18}
                  className="animate-spin"
                />
                Generating...
              </>
            ) : (
              <>
                <Sparkles size={18} />
                Generate Invigilators
              </>
            )}
          </button>

          <button
            type="button"
            onClick={handleValidate}
            disabled={
              !selectedExamination || validating || loading
            }
            className="flex items-center justify-center gap-2 rounded-xl border border-border px-5 py-3.5 text-sm font-semibold text-sidebar transition hover:border-accent hover:bg-surface-muted disabled:cursor-not-allowed disabled:opacity-50"
          >
            {validating ? (
              <>
                <RefreshCw
                  size={18}
                  className="animate-spin"
                />
                Validating...
              </>
            ) : (
              <>
                <ShieldCheck size={18} />
                Validate
              </>
            )}
          </button>

        </div>

        {/* Force regenerate (secondary action) */}

        {selectedExamination &&
          assignments.length > 0 && (
            <div className="mt-4 flex justify-end">
              <button
                type="button"
                onClick={() => handleGenerate(true)}
                disabled={generating}
                className="text-xs font-semibold text-text-muted underline-offset-4 transition hover:text-primary hover:underline disabled:opacity-50"
              >
                Force regenerate
              </button>
            </div>
          )}

      </section>

      {/* ============================================ */}
      {/* ERROR / SUCCESS */}
      {/* ============================================ */}

      {error && (
        <div className="mb-6 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertCircle size={19} className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="mb-6 flex items-start gap-3 rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
          <CheckCircle2 size={19} className="mt-0.5 shrink-0" />
          <span>{success}</span>
        </div>
      )}

      {/* ============================================ */}
      {/* SUMMARY CARDS */}
      {/* ============================================ */}

      {selectedExamination && (
        <section className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">

          <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
            <p className="text-sm font-medium text-text-muted">
              Hall Slots Covered
            </p>
            <p className="mt-2 text-3xl font-bold text-text">
              {loading
                ? "..."
                : new Set(
                    assignments.map(
                      (assignment) =>
                        `${assignment.timetable_id}-${assignment.hall_id}`
                    )
                  ).size}
            </p>
          </div>

          <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
            <p className="text-sm font-medium text-text-muted">
              Invigilator Assignments
            </p>
            <p className="mt-2 text-3xl font-bold text-text">
              {loading ? "..." : assignments.length}
            </p>
          </div>

          <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
            <p className="text-sm font-medium text-text-muted">
              Distinct Staff
            </p>
            <p className="mt-2 text-3xl font-bold text-text">
              {loading ? "..." : workload.length}
            </p>
          </div>

          <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
            <p className="text-sm font-medium text-text-muted">
              Validation
            </p>
            <p
              className={`mt-2 text-2xl font-bold ${
                isValid ? "text-success" : "text-warning"
              }`}
            >
              {validation
                ? validation.status
                : "NOT RUN"}
            </p>
          </div>

        </section>
      )}

      {/* ============================================ */}
      {/* VALIDATION ERRORS */}
      {/* ============================================ */}

      {validation &&
        validation.status === "INVALID" &&
        Array.isArray(validation.errors) &&
        validation.errors.length > 0 && (
          <div className="mb-6 rounded-2xl border border-red-200 bg-red-50 p-5">

            <p className="text-sm font-bold text-red-800">
              Validation errors
            </p>

            <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-red-700">
              {validation.errors.map((errorLine, idx) => (
                <li key={idx}>{errorLine}</li>
              ))}
            </ul>

          </div>
        )}

      {/* ============================================ */}
      {/* WORKLOAD TABLE */}
      {/* ============================================ */}

      {selectedExamination && (
        <section className="mb-6 rounded-2xl border border-border bg-surface shadow-sm">

          <div className="border-b border-border p-5 md:p-6">
            <h2 className="font-bold text-text">
              Invigilator Workload
            </h2>
            <p className="mt-1 text-sm text-text-muted">
              Duty count per staff member for this examination.
            </p>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw
                size={24}
                className="animate-spin text-accent"
              />
              <span className="ml-3 text-sm text-text-muted">
                Loading workload...
              </span>
            </div>
          ) : workload.length === 0 ? (
            <div className="px-5 py-12 text-center">
              <Users
                size={28}
                className="mx-auto text-text-muted"
              />
              <p className="mt-3 font-semibold text-text">
                No invigilator assignments yet
              </p>
              <p className="mt-1 text-sm text-text-muted">
                Generate invigilator allocation to populate
                this table.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px]">
                <thead>
                  <tr className="border-b border-border bg-surface-muted">
                    <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                      Staff ID
                    </th>
                    <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                      Name
                    </th>
                    <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                      Email
                    </th>
                    <th className="px-5 py-4 text-right text-xs font-semibold uppercase tracking-wider text-text-muted">
                      Duties
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {workload.map((entry) => (
                    <tr
                      key={entry.staff_id}
                      className="border-b border-border last:border-0 hover:bg-surface-muted"
                    >
                      <td className="px-5 py-4 text-sm font-semibold text-sidebar">
                        #{entry.staff_id}
                      </td>
                      <td className="px-5 py-4 text-sm text-text">
                        {entry.staff_name || "—"}
                      </td>
                      <td className="px-5 py-4 text-sm text-text-muted">
                        {entry.email || "—"}
                      </td>
                      <td className="px-5 py-4 text-right text-sm font-bold text-primary">
                        {entry.duties}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

        </section>
      )}

      {/* ============================================ */}
      {/* ASSIGNMENT TABLE */}
      {/* ============================================ */}

      {selectedExamination && assignments.length > 0 && (
        <section className="rounded-2xl border border-border bg-surface shadow-sm">

          <div className="border-b border-border p-5 md:p-6">
            <h2 className="font-bold text-text">
              Invigilator Assignments
            </h2>
            <p className="mt-1 text-sm text-text-muted">
              Staff scheduled per examination slot and hall.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[960px]">
              <thead>
                <tr className="border-b border-border bg-surface-muted">
                  <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Date
                  </th>
                  <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Session
                  </th>
                  <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Time
                  </th>
                  <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Hall
                  </th>
                  <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Staff
                  </th>
                  <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Role
                  </th>
                </tr>
              </thead>
              <tbody>
                {assignments.map((row) => (
                  <tr
                    key={row.id}
                    className="border-b border-border last:border-0 hover:bg-surface-muted"
                  >
                    <td className="px-5 py-4 text-sm text-text">
                      {row.exam_date || "—"}
                    </td>
                    <td className="px-5 py-4 text-sm font-semibold text-sidebar">
                      {row.session || "—"}
                    </td>
                    <td className="px-5 py-4 text-sm text-text-muted">
                      {row.start_time && row.end_time
                        ? `${row.start_time} - ${row.end_time}`
                        : "—"}
                    </td>
                    <td className="px-5 py-4 text-sm text-text">
                      {row.hall || "—"}
                    </td>
                    <td className="px-5 py-4 text-sm text-text">
                      {row.staff_name || "—"}
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-flex rounded-full bg-accent-light px-3 py-1 text-xs font-semibold text-primary">
                        {row.role || "INVIGILATOR"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

        </section>
      )}

    </>
  );
}


export default InvigilatorPanel;