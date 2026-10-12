import { useEffect, useState } from "react";

import {
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  PlayCircle,
  ShieldCheck,
  Send,
  Eye,
  Building2,
  Armchair,
  Users,
  ExternalLink,
} from "lucide-react";

import {
  get,
  post,
} from "../../../services/api";

import AllocationValidation from "./AllocationValidation";


const STAGES = [
  "DRAFT",
  "GENERATED",
  "VALIDATED",
  "REVIEW",
  "APPROVED",
  "PUBLISHED",
];


const STAGE_ACTION = {
  DRAFT: {
    label: "Mark as Generated",
    endpoint: "generate",
    hint: "Requires hall allocation to exist.",
    requiresValidation: false,
  },
  GENERATED: {
    label: "Mark as Validated",
    endpoint: "validate",
    hint: "Runs hall + invigilator validation first.",
    requiresValidation: true,
  },
  VALIDATED: {
    label: "Start Review",
    endpoint: "review",
    hint: "Moves the examination into admin review.",
    requiresValidation: false,
  },
  REVIEW: {
    label: "Approve Allocation",
    endpoint: "approve",
    hint: "Re-runs validation; refuses if invalid.",
    requiresValidation: true,
  },
  APPROVED: {
    label: "Publish Examination",
    endpoint: "publish",
    hint: "Exposes hall tickets downstream.",
    requiresValidation: true,
  },
  PUBLISHED: {
    label: "Published",
    endpoint: null,
    hint: "Lifecycle complete.",
    requiresValidation: false,
  },
};

// Tabs the parent (Allocations.jsx) understands. Used by the
// "Fix in…" links. If onNavigateTab is not provided, links are
// simply hidden.
const FIX_TABS = {
  hall: "hall",
  seat: "seat",
  invigilator: "invigilator",
};


function ApprovalPanel({
  examinations,
  selectedExamination: selectedExaminationProp,
  onSelectExamination,
  onMessage,
  onNavigateTab,
}) {
  const [internalSelection, setInternalSelection] =
    useState(selectedExaminationProp || "");

  const selectedExamination = onSelectExamination
    ? (selectedExaminationProp || "")
    : internalSelection;

  const setSelectedExamination = (value) => {
    if (onSelectExamination) {
      onSelectExamination(value);
    } else {
      setInternalSelection(value);
    }
  };

  const [examination, setExamination] = useState(null);
  const [hallValidation, setHallValidation] = useState(null);
  const [invigValidation, setInvigValidation] = useState(null);

  // loadState tracks each source independently so we never treat
  // a failed fetch as "ready".  Values:
  //   "idle" | "loading" | "ok" | "failed"
  const [examLoad, setExamLoad] = useState("idle");
  const [hallLoad, setHallLoad] = useState("idle");
  const [invigLoad, setInvigLoad] = useState("idle");

  const [acting, setActing] = useState(false);
  const [error, setError] = useState("");
  const [actionErrors, setActionErrors] = useState([]);
  const [success, setSuccess] = useState("");

  // ---------------------------------------------------------
  // CLEAR STALE DATA IMMEDIATELY ON SELECTION CHANGE
  //
  // This is the fix for "no stale details shown as if they
  // belong to the newly selected examination".
  // ---------------------------------------------------------
  useEffect(() => {
    // Wipe everything the previous examination produced BEFORE
    // the new fetch begins.
    setExamination(null);
    setHallValidation(null);
    setInvigValidation(null);
    setError("");
    setActionErrors([]);
    setSuccess("");
    setExamLoad("idle");
    setHallLoad("idle");
    setInvigLoad("idle");

    if (selectedExamination) {
      loadReadiness(selectedExamination);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedExamination]);

  const loadReadiness = async (examinationId) => {
    // ---------------------------------------------------------
    // Three independent fetches. Each tracks its own load state.
    // A failed one is NEVER treated as a success.
    // ---------------------------------------------------------

    // Exam detail
    setExamLoad("loading");
    const examPromise = get(
      `/examinations/${examinationId}`
    )
      .then((data) => {
        // Backend returns the exam object directly for
        // GET /examinations/:id (per routes/examinations.py).
        // Keep the tolerant shape in case a wrapper is added.
        const exam =
          data?.examination ||
          (data?.id ? data : null);

        if (!exam) {
          throw new Error(
            "Examination response was empty."
          );
        }
        setExamination(exam);
        setExamLoad("ok");
        return exam;
      })
      .catch((err) => {
        console.error("Approval load error:", err);
        setExamLoad("failed");
        setError(
          err.message ||
            "Unable to load examination."
        );
        // Do NOT fall back to a list lookup. Honest failure.
        return null;
      });

    // Hall + seat validation
    setHallLoad("loading");
    const hallPromise = get(
      `/allocations/validate/${examinationId}`
    )
      .then((data) => {
        setHallValidation(data);
        setHallLoad("ok");
        return data;
      })
      .catch((err) => {
        console.error("Hall validation error:", err);
        setHallValidation(null);
        setHallLoad("failed");
        return null;
      });

    // Invigilator validation — soft-fail like
    // AllocationValidation does, but record the failure
    // so we never render a false VALID.
    setInvigLoad("loading");
    const invigPromise = get(
      `/allocations/invigilators/validate/${examinationId}`
    )
      .then((data) => {
        setInvigValidation(data);
        setInvigLoad("ok");
        return data;
      })
      .catch((err) => {
        console.error(
          "Invigilator validation error:",
          err
        );
        // Preserve the error message as an INVALID result,
        // exactly as AllocationValidation does, but mark
        // the source as failed so the gate treats it as
        // unknown rather than "not generated".
        setInvigValidation({
          status: "INVALID",
          errors: [
            err.message ||
              "Unable to validate invigilator allocation.",
          ],
          __loadFailed: true,
        });
        setInvigLoad("failed");
        return null;
      });

    await Promise.allSettled([
      examPromise,
      hallPromise,
      invigPromise,
    ]);
  };

  const handleAction = async () => {
    if (!selectedExamination || !examination) {
      return;
    }

    const stage = examination.status || "DRAFT";
    const action = STAGE_ACTION[stage];

    if (!action || !action.endpoint) {
      return;
    }

    const confirmed = window.confirm(
      `${action.label} for this examination?`
    );

    if (!confirmed) return;

    try {
      setActing(true);
      setError("");
      setActionErrors([]);
      setSuccess("");

      const data = await post(
        `/examinations/${selectedExamination}/${action.endpoint}`,
        {}
      );

      if (!data.success) {
        throw new Error(
          data.message ||
            "Lifecycle transition failed."
        );
      }

      setSuccess(
        data.message ||
          `Moved to ${data.status || "next stage"}`
      );

      if (onMessage) {
        onMessage(
          data.message ||
            `Moved to ${data.status || "next stage"}`,
          "success"
        );
      }

      // Refresh the exam + both validators so the readiness
      // cards reflect the post-transition reality.
      await loadReadiness(selectedExamination);
    } catch (err) {
      console.error("Lifecycle error:", err);

      const message =
        err.message || "Lifecycle transition failed.";

      setError(message);

      // Surface structured backend errors (from
      // transition_status's errors[]) if present.
      if (Array.isArray(err.errors) && err.errors.length) {
        setActionErrors(err.errors);
      }

      if (onMessage) {
        onMessage(message, "error");
      }
    } finally {
      setActing(false);
    }
  };

  const currentStage =
    examination?.status || "DRAFT";

  const currentStageIndex = STAGES.indexOf(
    currentStage
  );

  const nextStage = STAGE_ACTION[currentStage];

  // ---------------------------------------------------------
  // READINESS DERIVATION
  //
  // We never invent rules. We only read what the backend
  // validators returned.
  // ---------------------------------------------------------

  const hallStatus = hallValidation?.status || null;
  const invigStatus = invigValidation?.status || null;

  const readinessUnknown =
    examLoad === "loading" ||
    hallLoad === "loading" ||
    invigLoad === "loading";

  const readinessFailed =
    examLoad === "failed" ||
    hallLoad === "failed" ||
    invigLoad === "failed";

  const validationPasses =
    hallStatus === "VALID" &&
    invigStatus === "VALID";

  const validationNotGenerated =
    hallStatus === "NOT GENERATED";

  const combinedValidationStatus = readinessUnknown
    ? "LOADING"
    : readinessFailed
    ? "UNKNOWN"
    : validationPasses
    ? "VALID"
    : validationNotGenerated
    ? "NOT GENERATED"
    : "INVALID";

  // Reason shown under the action button when the action is
  // blocked. Prefer specific validator errors; fall back to a
  // short derived explanation.
  const blockingReasons = (() => {
    const reasons = [];

    if (!nextStage?.endpoint) return reasons;

    if (examLoad === "failed") {
      reasons.push(
        "Examination details could not be loaded."
      );
    }

    if (
      nextStage.requiresValidation &&
      hallLoad === "failed"
    ) {
      reasons.push(
        "Hall/seat validation could not be loaded."
      );
    }

    if (
      nextStage.requiresValidation &&
      invigLoad === "failed"
    ) {
      reasons.push(
        "Invigilator validation could not be loaded."
      );
    }

    if (
      nextStage.requiresValidation &&
      hallStatus &&
      hallStatus !== "VALID"
    ) {
      if (hallStatus === "NOT GENERATED") {
        reasons.push(
          "Hall / seat allocation has not been generated."
        );
      } else {
        const first =
          hallValidation?.errors?.[0] ||
          "Hall / seat allocation is invalid.";
        reasons.push(first);
      }
    }

    if (
      nextStage.requiresValidation &&
      invigStatus &&
      invigStatus !== "VALID"
    ) {
      const first =
        invigValidation?.errors?.[0] ||
        "Invigilator allocation is invalid.";
      reasons.push(first);
    }

    return reasons;
  })();

  const actionDisabled =
    acting ||
    readinessUnknown ||
    // Never treat an unknown readiness as ready.
    (readinessFailed && nextStage?.requiresValidation) ||
    // Blocked when the backend validator says the data isn't valid.
    (nextStage?.requiresValidation && !validationPasses);

  // ---------------------------------------------------------
  // RENDER
  // ---------------------------------------------------------

  return (
    <>
      {/* ============================================ */}
      {/* SELECTOR */}
      {/* ============================================ */}

      <section className="mb-6 rounded-2xl border border-border bg-surface p-5 shadow-sm md:p-6">

        <div className="grid gap-5 lg:grid-cols-[1fr_auto] lg:items-end">

          <div>
            <label
              htmlFor="approval-examination"
              className="mb-2 block text-sm font-semibold text-sidebar"
            >
              Select Examination
            </label>

            <select
              id="approval-examination"
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

              {examinations.map((item) => {
                // Enrich with fields already returned by
                // GET /examinations/. Falls back gracefully
                // when a field is missing.
                const bits = [
                  `Examination #${item.id}`,
                  item.name,
                  item.exam_type,
                  item.start_date,
                  item.status,
                ].filter(Boolean);

                return (
                  <option key={item.id} value={item.id}>
                    {bits.join(" · ")}
                  </option>
                );
              })}
            </select>
          </div>

          {examination && nextStage?.endpoint && (
            <button
              type="button"
              onClick={handleAction}
              disabled={actionDisabled}
              title={
                actionDisabled && blockingReasons.length
                  ? blockingReasons[0]
                  : undefined
              }
              className="flex items-center justify-center gap-2 rounded-xl bg-sidebar px-5 py-3.5 text-sm font-semibold text-white shadow-lg shadow-sidebar/10 transition hover:bg-primary disabled:cursor-not-allowed disabled:opacity-60"
            >
              {acting ? (
                <>
                  <RefreshCw
                    size={18}
                    className="animate-spin"
                  />
                  Working...
                </>
              ) : (
                <>
                  <PlayCircle size={18} />
                  {nextStage.label}
                </>
              )}
            </button>
          )}

        </div>

        {/* Blocking reason under the button */}

        {examination &&
          nextStage?.endpoint &&
          actionDisabled &&
          !acting &&
          blockingReasons.length > 0 && (
            <div className="mt-4 rounded-xl border border-yellow-200 bg-yellow-50 px-4 py-3 text-sm text-yellow-800">
              <p className="font-semibold">
                This action is currently blocked:
              </p>
              <ul className="mt-1 list-disc pl-5">
                {blockingReasons.map((reason, idx) => (
                  <li key={idx}>{reason}</li>
                ))}
              </ul>
            </div>
          )}

      </section>

      {/* ============================================ */}
      {/* MESSAGES */}
      {/* ============================================ */}

      {error && (
        <div className="mb-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <div className="flex items-start gap-3">
            <AlertCircle
              size={19}
              className="mt-0.5 shrink-0"
            />
            <span>{error}</span>
          </div>

          {actionErrors.length > 0 && (
            <ul className="mt-2 list-disc space-y-1 pl-8">
              {actionErrors.map((line, idx) => (
                <li key={idx}>{line}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {success && (
        <div className="mb-6 flex items-start gap-3 rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
          <CheckCircle2
            size={19}
            className="mt-0.5 shrink-0"
          />
          <span>{success}</span>
        </div>
      )}

      {/* ============================================ */}
      {/* STEPPER */}
      {/* ============================================ */}

      {examination && (
        <section className="mb-6 rounded-2xl border border-border bg-surface p-5 shadow-sm md:p-6">

          <h2 className="text-lg font-bold text-text">
            {examination.name}
          </h2>

          <p className="mt-1 text-sm text-text-muted">
            Lifecycle status:{" "}
            <span className="font-semibold text-primary">
              {currentStage}
            </span>
          </p>

          <ol className="mt-6 grid gap-3 md:grid-cols-6">

            {STAGES.map((stage, idx) => {
              const reached = idx <= currentStageIndex;
              const isCurrent = idx === currentStageIndex;

              return (
                <li
                  key={stage}
                  className={`rounded-xl border p-3 text-center transition ${
                    isCurrent
                      ? "border-primary bg-accent-light"
                      : reached
                      ? "border-success/30 bg-green-50"
                      : "border-border bg-surface-muted"
                  }`}
                >
                  <p
                    className={`text-[11px] font-semibold uppercase tracking-wider ${
                      isCurrent
                        ? "text-primary"
                        : reached
                        ? "text-success"
                        : "text-text-muted"
                    }`}
                  >
                    Step {idx + 1}
                  </p>

                  <p
                    className={`mt-1 text-sm font-bold ${
                      isCurrent
                        ? "text-primary"
                        : reached
                        ? "text-success"
                        : "text-text-muted"
                    }`}
                  >
                    {stage}
                  </p>
                </li>
              );
            })}

          </ol>

          {nextStage?.hint && (
            <p className="mt-5 text-xs text-text-muted">
              Next action: {nextStage.hint}
            </p>
          )}

        </section>
      )}

      {/* ============================================ */}
      {/* READINESS SUMMARY */}
      {/* ============================================ */}

      {examination && (
        <section className="mb-6 grid gap-5 lg:grid-cols-4">

          {/* Lifecycle */}

          <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-text-muted">
                Current Status
              </p>
              <Eye size={18} className="text-accent" />
            </div>

            <p className="mt-2 text-2xl font-bold text-primary">
              {currentStage}
            </p>
          </div>

          {/* Hall / Seat */}

          <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-text-muted">
                Hall / Seat
              </p>
              <Building2
                size={18}
                className="text-accent"
              />
            </div>

            <p
              className={`mt-2 text-2xl font-bold ${
                hallStatus === "VALID"
                  ? "text-success"
                  : hallStatus === "NOT GENERATED"
                  ? "text-warning"
                  : hallLoad === "failed"
                  ? "text-warning"
                  : "text-text"
              }`}
            >
              {hallLoad === "loading"
                ? "..."
                : hallLoad === "failed"
                ? "UNKNOWN"
                : hallStatus || "—"}
            </p>

            {hallValidation && (
              <dl className="mt-3 space-y-1 text-xs text-text-muted">
                <div className="flex items-center justify-between">
                  <dt>Eligible</dt>
                  <dd className="font-semibold text-text">
                    {hallValidation.eligible_students ?? 0}
                  </dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt>Allocated</dt>
                  <dd className="font-semibold text-text">
                    {hallValidation.allocated_capacity ?? 0}
                  </dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt>Unallocated</dt>
                  <dd className="font-semibold text-text">
                    {hallValidation.unallocated_students ?? 0}
                  </dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt>Halls used</dt>
                  <dd className="font-semibold text-text">
                    {hallValidation.halls_used ?? 0}
                  </dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt>Seat records</dt>
                  <dd className="font-semibold text-text">
                    {hallValidation.seat_records ?? 0}
                  </dd>
                </div>
              </dl>
            )}
          </div>

          {/* Invigilators */}

          <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-text-muted">
                Invigilators
              </p>
              <Users size={18} className="text-accent" />
            </div>

            <p
              className={`mt-2 text-2xl font-bold ${
                invigStatus === "VALID"
                  ? "text-success"
                  : invigLoad === "failed"
                  ? "text-warning"
                  : "text-text"
              }`}
            >
              {invigLoad === "loading"
                ? "..."
                : invigLoad === "failed"
                ? "UNKNOWN"
                : invigStatus || "—"}
            </p>

            {invigValidation && (
              <dl className="mt-3 space-y-1 text-xs text-text-muted">
                <div className="flex items-center justify-between">
                  <dt>Assignments</dt>
                  <dd className="font-semibold text-text">
                    {invigValidation.invigilator_assignments ?? 0}
                  </dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt>Distinct staff</dt>
                  <dd className="font-semibold text-text">
                    {invigValidation.distinct_staff ?? 0}
                  </dd>
                </div>
              </dl>
            )}
          </div>

          {/* Overall readiness */}

          <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-text-muted">
                Validation
              </p>
              <ShieldCheck
                size={18}
                className="text-accent"
              />
            </div>

            <p
              className={`mt-2 text-2xl font-bold ${
                combinedValidationStatus === "VALID"
                  ? "text-success"
                  : combinedValidationStatus ===
                      "NOT GENERATED" ||
                    combinedValidationStatus === "UNKNOWN"
                  ? "text-warning"
                  : combinedValidationStatus === "LOADING"
                  ? "text-text-muted"
                  : "text-warning"
              }`}
            >
              {combinedValidationStatus}
            </p>

            {readinessFailed && (
              <p className="mt-3 text-xs text-warning">
                Readiness could not be fully determined.
                Retry loading before acting.
              </p>
            )}
          </div>

        </section>
      )}

      {/* ============================================ */}
      {/* QUICK FIX LINKS */}
      {/* ============================================ */}

      {examination &&
        onNavigateTab &&
        (hallStatus === "INVALID" ||
          hallStatus === "NOT GENERATED" ||
          invigStatus === "INVALID") && (
          <section className="mb-6 flex flex-wrap gap-3">

            {(hallStatus === "INVALID" ||
              hallStatus === "NOT GENERATED") && (
              <button
                type="button"
                onClick={() =>
                  onNavigateTab(FIX_TABS.hall)
                }
                className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface px-4 py-2.5 text-sm font-semibold text-sidebar transition hover:border-accent hover:bg-surface-muted"
              >
                <ExternalLink size={16} />
                Fix Hall / Seat Allocation
              </button>
            )}

            {invigStatus === "INVALID" && (
              <button
                type="button"
                onClick={() =>
                  onNavigateTab(FIX_TABS.invigilator)
                }
                className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface px-4 py-2.5 text-sm font-semibold text-sidebar transition hover:border-accent hover:bg-surface-muted"
              >
                <ExternalLink size={16} />
                Fix Invigilator Allocation
              </button>
            )}

          </section>
        )}

      {/* ============================================ */}
      {/* FULL VALIDATION DETAIL (reused component) */}
      {/* ============================================ */}

      {examination && (
        <section className="mb-6">
          <AllocationValidation
            examinationId={selectedExamination}
            examination={examination}
          />
        </section>
      )}

      {/* ============================================ */}
      {/* EMPTY STATE */}
      {/* ============================================ */}

      {!examination &&
        examLoad !== "loading" &&
        !error && (
          <div className="rounded-2xl border border-dashed border-border bg-surface p-12 text-center">

            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-accent-light text-primary">
              <PlayCircle size={27} />
            </div>

            <h3 className="mt-5 text-lg font-bold text-text">
              Select an examination
            </h3>

            <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-text-muted">
              Pick an examination above to inspect its
              readiness and take the next permitted
              lifecycle action.
            </p>

          </div>
        )}

    </>
  );
}


export default ApprovalPanel;