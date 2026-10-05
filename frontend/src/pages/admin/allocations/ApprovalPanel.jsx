import { useEffect, useState } from "react";

import {
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  PlayCircle,
  ShieldCheck,
  Send,
  Eye,
} from "lucide-react";

import {
  get,
  post,
} from "../../../services/api";


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
  },
  GENERATED: {
    label: "Mark as Validated",
    endpoint: "validate",
    hint: "Runs hall + invigilator validation first.",
  },
  VALIDATED: {
    label: "Start Review",
    endpoint: "review",
    hint: "Moves the examination into admin review.",
  },
  REVIEW: {
    label: "Approve Allocation",
    endpoint: "approve",
    hint: "Re-runs validation; refuses if invalid.",
  },
  APPROVED: {
    label: "Publish Examination",
    endpoint: "publish",
    hint: "Exposes hall tickets downstream.",
  },
  PUBLISHED: {
    label: "Published",
    endpoint: null,
    hint: "Lifecycle complete.",
  },
};


function ApprovalPanel({
  examinations,
  onMessage,
}) {
  const [selectedExamination, setSelectedExamination] =
    useState("");

  const [examination, setExamination] = useState(null);
  const [loading, setLoading] = useState(false);
  const [acting, setActing] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    if (selectedExamination) {
      loadExamination(selectedExamination);
    } else {
      setExamination(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedExamination]);

  const loadExamination = async (examinationId) => {
    try {
      setLoading(true);
      setError("");
      setSuccess("");

      const data = await get(
        `/examinations/${examinationId}`
      );

      // Backend may return either the examination object
      // or {success, examination}. Handle both.
      const exam =
        data?.examination ||
        (data?.id ? data : null);

      setExamination(exam);
    } catch (err) {
      console.error("Approval load error:", err);

      // Fallback: fetch list and filter
      try {
        const list = await get("/examinations/");
        const found = (list || []).find(
          (item) =>
            String(item.id) === String(examinationId)
        );
        setExamination(found || null);
      } catch (innerError) {
        console.error(innerError);
        setError(
          err.message ||
            "Unable to load examination."
        );
        setExamination(null);
      }
    } finally {
      setLoading(false);
    }
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

      await loadExamination(selectedExamination);
    } catch (err) {
      console.error("Lifecycle error:", err);

      // 400 responses carry structured errors
      const message =
        err.message || "Lifecycle transition failed.";

      setError(message);

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

              {examinations.map((item) => (
                <option key={item.id} value={item.id}>
                  {`Examination #${item.id}`} —{" "}
                  {item.name}
                </option>
              ))}
            </select>
          </div>

          {examination && nextStage?.endpoint && (
            <button
              type="button"
              onClick={handleAction}
              disabled={acting || loading}
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

      </section>

      {/* ============================================ */}
      {/* MESSAGES */}
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
      {/* STATE PREVIEW */}
      {/* ============================================ */}

      {examination && (
        <section className="grid gap-5 lg:grid-cols-3">

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

            <p className="mt-2 text-sm text-text-muted">
              Validation runs automatically at the{" "}
              <span className="font-semibold text-text">
                VALIDATED
              </span>{" "}
              and{" "}
              <span className="font-semibold text-text">
                APPROVED
              </span>{" "}
              stages.
            </p>

          </div>

          <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">

            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-text-muted">
                Publishing
              </p>
              <Send size={18} className="text-accent" />
            </div>

            <p className="mt-2 text-sm text-text-muted">
              Hall tickets become available only after{" "}
              <span className="font-semibold text-text">
                PUBLISHED
              </span>
              .
            </p>

          </div>

        </section>
      )}

      {/* ============================================ */}
      {/* EMPTY STATE */}
      {/* ============================================ */}

      {!examination && !loading && (
        <div className="rounded-2xl border border-dashed border-border bg-surface p-12 text-center">

          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-accent-light text-primary">
            <PlayCircle size={27} />
          </div>

          <h3 className="mt-5 text-lg font-bold text-text">
            Select an examination
          </h3>

          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-text-muted">
            Pick an examination above to walk through the
            review, approval, and publishing lifecycle.
          </p>

        </div>
      )}

    </>
  );
}


export default ApprovalPanel;