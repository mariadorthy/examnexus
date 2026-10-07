import { useEffect, useMemo, useState } from "react";

import {
  getAllocations,
  simulateReallocation,
  applyReallocation,
} from "../../../services/allocationService";

import {
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  ShieldAlert,
  ArrowRight,
  XCircle,
} from "lucide-react";

export default function WhatIfReallocation({
  examinationId,
  onApplied,
}) {
  const [allocations, setAllocations] = useState([]);
  const [excluded, setExcluded] = useState([]);
  const [proposal, setProposal] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");

  useEffect(() => {
    let alive = true;

    if (!examinationId) return;

    setError("");
    setInfo("");
    setProposal(null);
    setExcluded([]);

    getAllocations(examinationId)
      .then((rows) => {
        if (alive) setAllocations(rows || []);
      })
      .catch((err) => {
        if (alive) setError(err.message);
      });

    return () => {
      alive = false;
    };
  }, [examinationId]);

  const uniqueHalls = useMemo(() => {
    const map = new Map();

    for (const row of allocations) {
      if (!map.has(row.hall_id)) {
        map.set(row.hall_id, row);
      }
    }

    return Array.from(map.values());
  }, [allocations]);

  function toggleHall(hallId) {
    setProposal(null);
    setError("");
    setInfo("");

    setExcluded((prev) =>
      prev.includes(hallId)
        ? prev.filter((id) => id !== hallId)
        : [...prev, hallId]
    );
  }

  async function handleSimulate() {
    if (excluded.length === 0) {
      setError(
        "Select at least one hall to mark unavailable."
      );
      return;
    }

    setBusy(true);
    setError("");
    setInfo("");

    try {
      const result = await simulateReallocation(
        examinationId,
        excluded
      );

      setProposal(result);
    } catch (err) {
      setError(err.message);
      setProposal(null);
    } finally {
      setBusy(false);
    }
  }

  async function handleApply() {
    if (!proposal) return;

    const confirmed = window.confirm(
      "Apply this proposed reallocation?\n\n" +
      "The current hall, seat and invigilator allocation " +
      "will be replaced with the proposed arrangement."
    );

    if (!confirmed) return;

    setBusy(true);
    setError("");
    setInfo("");

    try {
      const result = await applyReallocation(
        examinationId,
        excluded
      );

      setInfo(
        result.requires_reapproval
          ? "Reallocation applied successfully. The examination has been returned to REVIEW and requires re-approval."
          : "Reallocation applied successfully. Hall, seat, and invigilator allocations were regenerated."
      );

      setProposal(null);
      setExcluded([]);

      if (onApplied) {
        onApplied(result);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function handleReject() {
    setProposal(null);
    setExcluded([]);
    setInfo(
      "Proposal discarded. No changes were applied."
    );
    setError("");
  }

  return (
    <section className="mt-6 rounded-2xl border border-border bg-surface p-5 shadow-sm md:p-6">

      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <div className="flex flex-col gap-4 border-b border-border pb-5 md:flex-row md:items-start md:justify-between">

        <div>
          <div className="flex items-center gap-2">
            <ShieldAlert
              size={19}
              className="text-primary"
            />

            <p className="text-sm font-semibold uppercase tracking-wider text-accent">
              Report Incident / What-If
            </p>
          </div>

          <h3 className="mt-1 text-lg font-bold text-text">
            Dynamic Reallocation
          </h3>

          <p className="mt-1 max-w-2xl text-sm leading-6 text-text-muted">
            Mark one or more halls unavailable to preview
            a safe alternative arrangement.
            Nothing is written to the database until you
            approve the proposal.
          </p>
        </div>

        <div className="inline-flex w-fit items-center gap-2 rounded-full bg-accent-light px-3 py-1.5 text-xs font-semibold text-primary">
          <ShieldAlert size={14} />
          What-If Simulation
        </div>

      </div>

      {/* ================================================= */}
      {/* HALL SELECTION */}
      {/* ================================================= */}

      <div className="mt-5">

        <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">

          <div>
            <h4 className="text-sm font-bold text-text">
              Select Unavailable Halls
            </h4>

            <p className="mt-1 text-xs text-text-muted">
              Select halls that should be treated as
              unavailable for this simulation.
            </p>
          </div>

          {excluded.length > 0 && (
            <span className="inline-flex w-fit rounded-full bg-yellow-50 px-3 py-1 text-xs font-semibold text-warning">
              {excluded.length} hall
              {excluded.length !== 1 ? "s" : ""} selected
            </span>
          )}

        </div>

        {uniqueHalls.length === 0 ? (
          <div className="mt-4 rounded-xl border border-dashed border-border bg-surface-muted px-5 py-8 text-center">

            <AlertCircle
              size={24}
              className="mx-auto text-text-muted"
            />

            <p className="mt-3 text-sm font-semibold text-text">
              No allocated halls found
            </p>

            <p className="mt-1 text-xs text-text-muted">
              Generate a hall allocation before running
              a What-If simulation.
            </p>

          </div>
        ) : (
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">

            {uniqueHalls.map((row) => {
              const isSelected =
                excluded.includes(row.hall_id);

              return (
                <label
                  key={row.hall_id}
                  className={`flex cursor-pointer items-start gap-3 rounded-xl border p-4 transition ${
                    isSelected
                      ? "border-primary bg-accent-light shadow-sm"
                      : "border-border bg-surface hover:border-accent hover:bg-surface-muted"
                  }`}
                >

                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() =>
                      toggleHall(row.hall_id)
                    }
                    disabled={busy}
                    className="mt-1 h-4 w-4 accent-primary"
                  />

                  <div className="min-w-0 flex-1">

                    <div className="flex items-center justify-between gap-2">

                      <p className="truncate text-sm font-semibold text-text">
                        {row.hall || `Hall #${row.hall_id}`}
                      </p>

                      {isSelected && (
                        <CheckCircle2
                          size={16}
                          className="shrink-0 text-primary"
                        />
                      )}

                    </div>

                    <p className="mt-1 text-xs text-text-muted">
                      Capacity{" "}
                      {row.examination_capacity ?? "—"}
                    </p>

                  </div>

                </label>
              );
            })}

          </div>
        )}

      </div>

      {/* ================================================= */}
      {/* SIMULATION ACTION */}
      {/* ================================================= */}

      {uniqueHalls.length > 0 && (
        <div className="mt-5 flex flex-col gap-3 rounded-xl bg-surface-muted p-4 sm:flex-row sm:items-center sm:justify-between">

          <div>
            <p className="text-sm font-semibold text-text">
              Ready to simulate?
            </p>

            <p className="mt-1 text-xs text-text-muted">
              The allocator will calculate an alternative
              arrangement without changing the database.
            </p>
          </div>

          <button
            type="button"
            onClick={handleSimulate}
            disabled={
              busy ||
              excluded.length === 0
            }
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-sidebar px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-sidebar/10 transition hover:bg-primary disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
          >
            {busy ? (
              <>
                <RefreshCw
                  size={17}
                  className="animate-spin"
                />
                Working...
              </>
            ) : (
              <>
                <ShieldAlert size={17} />
                Generate Proposed Reallocation
              </>
            )}
          </button>

        </div>
      )}

      {/* ================================================= */}
      {/* ERROR */}
      {/* ================================================= */}

      {error && (
        <div className="mt-5 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">

          <AlertCircle
            size={19}
            className="mt-0.5 shrink-0"
          />

          <span>{error}</span>

        </div>
      )}

      {/* ================================================= */}
      {/* INFO */}
      {/* ================================================= */}

      {info && (
        <div className="mt-5 flex items-start gap-3 rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">

          <CheckCircle2
            size={19}
            className="mt-0.5 shrink-0"
          />

          <span>{info}</span>

        </div>
      )}

      {/* ================================================= */}
      {/* PROPOSAL */}
      {/* ================================================= */}

      {proposal && (
        <div className="mt-6 rounded-2xl border border-border bg-surface-muted p-5 md:p-6">

          {/* Proposal Header */}

          <div className="flex items-start gap-3 border-b border-border pb-5">

            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent-light text-primary">
              <ShieldAlert size={20} />
            </div>

            <div>
              <h4 className="text-base font-bold text-text">
                Impact Detected
              </h4>

              <p className="mt-1 text-xs leading-5 text-text-muted">
                The following changes were identified by
                the reallocation engine.
              </p>
            </div>

          </div>

          {/* Impact Summary */}

          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">

            <ImpactCard
              label="Affected Students"
              value={
                proposal.diff?.affected_students ?? 0
              }
            />

            <ImpactCard
              label="Halls Removed"
              value={
                proposal.diff?.removed_halls?.length ?? 0
            }
            />

            <ImpactCard
              label="Halls Added"
              value={
                proposal.diff?.added_halls?.length ?? 0
              }
            />

            <ImpactCard
              label="Unallocated Students"
              value={
                proposal.diff?.unallocated_students ?? 0
              }
            />

          </div>

          {/* Proposed Allocation */}

          <div className="mt-6">

            <div className="mb-3 flex items-center gap-2">
              <ArrowRight
                size={17}
                className="text-primary"
              />

              <h4 className="text-sm font-bold text-text">
                Proposed Reallocation
              </h4>
            </div>

            <div className="overflow-x-auto rounded-xl border border-border bg-surface">

              <table className="w-full min-w-[620px]">

                <thead>
                  <tr className="border-b border-border bg-surface-muted">

                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                      Timetable
                    </th>

                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                      Hall
                    </th>

                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                      Capacity
                    </th>

                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                      Purpose
                    </th>

                  </tr>
                </thead>

                <tbody>

                  {proposal.proposed?.per_hall?.map(
                    (row, i) => (
                      <tr
                        key={i}
                        className="border-b border-border last:border-0 hover:bg-surface-muted"
                      >

                        <td className="px-4 py-3 text-sm text-text">
                          #{row.timetable_id}
                        </td>

                        <td className="px-4 py-3 text-sm font-semibold text-text">
                          #{row.hall_id}
                        </td>

                        <td className="px-4 py-3 text-sm font-semibold text-primary">
                          {row.allocated_capacity}
                        </td>

                        <td className="px-4 py-3">

                          <span className="inline-flex rounded-full bg-accent-light px-2.5 py-1 text-xs font-semibold text-primary">
                            {row.purpose || "NORMAL"}
                          </span>

                        </td>

                      </tr>
                    )
                  )}

                </tbody>

              </table>

            </div>

          </div>

          {/* Validation */}

          <div className="mt-6">

            <h4 className="text-sm font-bold text-text">
              Validation
            </h4>

            <div
              className={`mt-3 flex items-center gap-2 rounded-xl border px-4 py-3 text-sm font-semibold ${
                proposal.validation?.status === "VALID"
                  ? "border-green-200 bg-green-50 text-green-700"
                  : "border-red-200 bg-red-50 text-red-700"
              }`}
            >
              {proposal.validation?.status === "VALID" ? (
                <CheckCircle2 size={18} />
              ) : (
                <AlertCircle size={18} />
              )}

              {proposal.validation?.status || "UNKNOWN"}
            </div>

            {proposal.validation?.errors?.length > 0 && (
              <div className="mt-3 rounded-xl border border-red-200 bg-red-50 p-4">

                <p className="text-xs font-semibold uppercase tracking-wider text-red-700">
                  Validation Errors
                </p>

                <ul className="mt-2 space-y-1 text-sm text-red-700">
                  {proposal.validation.errors.map(
                    (e, i) => (
                      <li key={i}>• {e}</li>
                    )
                  )}
                </ul>

              </div>
            )}

          </div>

          {/* Reasons */}

          {proposal.explanations?.length > 0 && (
            <div className="mt-6">

              <h4 className="text-sm font-bold text-text">
                Reallocation Reasons
              </h4>

              <div className="mt-3 space-y-2">

                {proposal.explanations.map(
                  (ex, i) => (
                    <div
                      key={i}
                      className="rounded-xl border border-border bg-surface px-4 py-3"
                    >

                      <p className="text-sm text-text">

                        <span className="font-semibold">
                          {ex.hall}:
                        </span>{" "}

                        {ex.reason}

                      </p>

                    </div>
                  )
                )}

              </div>

            </div>
          )}

          {/* Reapproval Warning */}

          {proposal.requires_reapproval && (
            <div className="mt-6 flex items-start gap-3 rounded-xl border border-yellow-200 bg-yellow-50 px-4 py-3">

              <AlertCircle
                size={19}
                className="mt-0.5 shrink-0 text-warning"
              />

              <div>
                <p className="text-sm font-semibold text-yellow-800">
                  Re-approval Required
                </p>

                <p className="mt-1 text-sm text-yellow-700">
                  This examination is currently APPROVED.
                  Applying this change will return it to
                  REVIEW and require re-approval.
                </p>
              </div>

            </div>
          )}

          {/* Actions */}

          <div className="mt-6 flex flex-col gap-3 border-t border-border pt-5 sm:flex-row sm:justify-end">

            <button
              type="button"
              onClick={handleReject}
              disabled={busy}
              className="flex items-center justify-center gap-2 rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold text-sidebar transition hover:border-red-200 hover:bg-red-50 hover:text-red-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <XCircle size={17} />
              Reject
            </button>

            <button
              type="button"
              onClick={handleApply}
              disabled={
                busy ||
                proposal.validation?.status !== "VALID"
              }
              className="flex items-center justify-center gap-2 rounded-xl bg-sidebar px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-sidebar/10 transition hover:bg-primary disabled:cursor-not-allowed disabled:opacity-60"
            >
              {busy ? (
                <>
                  <RefreshCw
                    size={17}
                    className="animate-spin"
                  />
                  Applying...
                </>
              ) : (
                <>
                  <CheckCircle2 size={17} />
                  Approve Reallocation
                </>
              )}
            </button>

          </div>

        </div>
      )}

    </section>
  );
}

function ImpactCard({ label, value }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-4">

      <p className="text-xs font-medium text-text-muted">
        {label}
      </p>

      <p className="mt-2 text-2xl font-bold text-text">
        {value}
      </p>

    </div>
  );
}