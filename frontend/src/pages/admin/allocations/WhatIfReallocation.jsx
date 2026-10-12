import { useEffect, useMemo, useState } from "react";

import {
  getAllocations,
  simulateReallocation,
  applyReallocation,
  simulateEmergencyReallocation,
  applyEmergencyReallocation,
} from "../../../services/allocationService";
import {
  reportHallIncident,
  listHallIncidents,
} from "../../../services/hallIncidentService";

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
const [incidentOpen, setIncidentOpen] = useState(false);
const [incidentHallId, setIncidentHallId] = useState(null);
const [incidentCategory, setIncidentCategory] = useState("MAINTENANCE");
const [incidentDescription, setIncidentDescription] = useState("");
const [incidentScope, setIncidentScope] = useState("GLOBAL");
const [incidentSubmitting, setIncidentSubmitting] = useState(false);
const [incidentError, setIncidentError] = useState("");
const [incidentInfo, setIncidentInfo] = useState("");
const [emergencyMode, setEmergencyMode] = useState(false);
const [openIncidents, setOpenIncidents] = useState([]);
const [selectedIncidentId, setSelectedIncidentId] = useState("");
const [acknowledgeInProgress, setAcknowledgeInProgress] = useState(false);
const [inProgress, setInProgress] = useState(false);

  useEffect(() => {
    let alive = true;

    if (!examinationId) return;

    setError("");
    setInfo("");
    setProposal(null);
    setExcluded([]);
    setEmergencyMode(false);
    setSelectedIncidentId("");
    setAcknowledgeInProgress(false);
    setInProgress(false);

    getAllocations(examinationId)
      .then((rows) => {
        if (alive) setAllocations(rows || []);
      })
      .catch((err) => {
        if (alive) setError(err.message);
      });

    // Preload the incident list and switch on emergency mode
    // as soon as we know the parent passed us an examination
    // that is already PUBLISHED. The Allocations page only
    // mounts this component for PUBLISHED exams.
    (async () => {
      if (!alive) return;
      await reloadOpenIncidents();
      if (alive) setEmergencyMode(true);
    })();

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

  async function reloadOpenIncidents() {
    try {
      const data = await listHallIncidents({
        status: "OPEN",
        examinationId,
      });
      setOpenIncidents(data.incidents || []);
    } catch (err) {
      // Non-fatal — the dropdown will just be empty and the
      // admin will see the reason when they try to simulate.
      console.error("Failed to load open incidents:", err);
    }
  }  

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

    if (emergencyMode && !selectedIncidentId) {
      setError(
        "Select an open incident to authorize the emergency reallocation."
      );
      return;
    }

    setBusy(true);
    setError("");
    setInfo("");

    try {
      const result = emergencyMode
        ? await simulateEmergencyReallocation(
            examinationId,
            Number(selectedIncidentId),
            excluded
          )
        : await simulateReallocation(
            examinationId,
            excluded
          );

      setProposal(result);

      if (result.in_progress_state === "IN_PROGRESS") {
        setInProgress(true);
      } else {
        setInProgress(false);
      }
    } catch (err) {
      // Detect the published-exam refusal and switch to
      // emergency mode instead of showing a dead-end error.

      if (
        !emergencyMode &&
        typeof err.message === "string" &&
        err.message.includes("PUBLISHED")
      ) {
        setEmergencyMode(true);
        setError("");
        await reloadOpenIncidents();
      } else {      
      setError(err.message);
        setProposal(null);
      }
    } finally {
      setBusy(false);
    }
  }

     async function handleApply() {
    if (!proposal) return;

    // Emergency apply requires an in-progress acknowledgement
    // when the examination is currently running.
    if (
      emergencyMode &&
      inProgress &&
      !acknowledgeInProgress
    ) {
      setError(
        "This examination is currently in progress. Tick the " +
        "acknowledgement box to confirm the operational " +
        "situation has been assessed before applying."
      );
      return;
    }

    const confirmed = window.confirm(
      emergencyMode
        ? "Apply this emergency reallocation?\n\n" +
          "Existing hall tickets will be superseded by new " +
          "tickets and old QR codes will no longer verify as " +
          "current. The examination stays published."
        : "Apply this proposed reallocation?\n\n" +
          "The current hall, seat and invigilator allocation " +
          "will be replaced with the proposed arrangement."
    );

    if (!confirmed) return;

    setBusy(true);
    setError("");
    setInfo("");

    try {
      let result;

      if (emergencyMode) {
        if (!selectedIncidentId) {
          setError(
            "Select an open incident to authorize the emergency reallocation."
          );
          return;
        }

        result = await applyEmergencyReallocation(
          examinationId,
          Number(selectedIncidentId),
          excluded,
          acknowledgeInProgress
        );

        setInfo(
          `Emergency reallocation applied. ` +
          `${result.tickets_superseded || 0} ticket(s) superseded, ` +
          `${result.tickets_issued || 0} reissued. ` +
          `The examination stays published.`
        );
      } else {
        result = await applyReallocation(
          examinationId,
          excluded
        );

        setInfo(
          result.requires_reapproval
            ? "Reallocation applied successfully. The examination has been returned to REVIEW and requires re-approval."
            : "Reallocation applied successfully. Hall, seat, and invigilator allocations were regenerated."
        );
      }

      setProposal(null);
      setExcluded([]);
      setAcknowledgeInProgress(false);

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

  function openIncidentModal(hallId) {
  setIncidentHallId(hallId);
  setIncidentCategory("MAINTENANCE");
  setIncidentDescription("");
  setIncidentScope("GLOBAL");
  setIncidentError("");
  setIncidentInfo("");
  setIncidentOpen(true);
}

function closeIncidentModal() {
  if (incidentSubmitting) return;
  setIncidentOpen(false);
  setIncidentHallId(null);
}
async function submitIncident() {
  if (!incidentDescription.trim()) {
    setIncidentError("Description is required.");
    return;
  }

  setIncidentSubmitting(true);
  setIncidentError("");
  setIncidentInfo("");

  try {
    const result = await reportHallIncident(incidentHallId, {
      category: incidentCategory,
      description: incidentDescription.trim(),
      scope: incidentScope,
      examinationId:
        incidentScope === "EXAM_SPECIFIC"
          ? examinationId
          : null,
    });

    setIncidentInfo(
      `Incident recorded (id ${result.incident?.id}). ` +
      (incidentScope === "GLOBAL"
        ? "This hall will be excluded from future allocation planning until the incident is resolved."
        : "This hall will be excluded from planning for this examination only.")
    );

    // The admin's next step is to authorise an emergency
    // reallocation with the incident they just created. Refresh
    // the dropdown from the server (which now filters to
    // incidents that apply to this examination), turn on
    // emergency mode, and pre-select the new incident so the
    // admin does not have to hunt for it.
    await reloadOpenIncidents();
    setEmergencyMode(true);

    if (result.incident?.id) {
      setSelectedIncidentId(String(result.incident.id));
    }

    setIncidentDescription("");
  } catch (err) {
    setIncidentError(err.message || "Failed to record incident.");
  } finally {
    setIncidentSubmitting(false);
  }
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

<button
  type="button"
  onClick={(event) => {
    event.preventDefault();
    event.stopPropagation();
    openIncidentModal(row.hall_id);
  }}
  disabled={busy}
  className="mt-2 text-xs font-semibold text-primary underline-offset-2 hover:underline"
>
  Report as incident
</button>

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
      {uniqueHalls.length > 0 &&
        excluded.length > 0 &&
        (!emergencyMode || openIncidents.length > 0) && (
        <div className="mt-5 flex flex-col gap-3 rounded-xl bg-surface-muted p-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-semibold text-text">
              {emergencyMode
                ? "Emergency reallocation (published examination)"
                : "Ready to simulate?"}
            </p>
            <p className="mt-1 text-xs text-text-muted">
              {emergencyMode
                ? "Choose an OPEN incident. The proposal is a " +
                  "simulation; nothing changes until you approve."
                : "The allocator will calculate an alternative " +
                  "arrangement without changing the database."}
            </p>
          </div>

          <button
            type="button"
            onClick={handleSimulate}
            disabled={
              busy ||
              excluded.length === 0 ||
              (emergencyMode && !selectedIncidentId)
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
                {emergencyMode
                  ? "Generate Emergency Proposal"
                  : "Generate Proposed Reallocation"}
              </>
            )}
          </button>

        </div>
      )}

      {emergencyMode &&
        excluded.length > 0 &&
        openIncidents.length > 0 && (
        <div className="mt-4 rounded-xl border border-yellow-200 bg-yellow-50 p-4">

          <p className="text-sm font-semibold text-yellow-800">
            Emergency reallocation
          </p>

          <p className="mt-1 text-xs text-yellow-700">
            This examination is PUBLISHED. Pick an OPEN incident
            that authorizes the change. Existing hall tickets
            will be superseded by new tickets after approval.
          </p>

          <div className="mt-3">
            <label className="mb-1 block text-xs font-semibold text-yellow-800">
              Authorizing incident
            </label>

            <select
              value={selectedIncidentId}
              onChange={(e) =>
                setSelectedIncidentId(e.target.value)
              }
              disabled={busy || openIncidents.length === 0}
              className="w-full rounded-xl border border-yellow-300 bg-white px-3 py-2 text-sm disabled:opacity-60"
            >
              <option value="">
                {openIncidents.length === 0
                  ? "No open incidents yet — use 'Report as incident' on a hall below"
                  : "Select an incident"}
              </option>
              {openIncidents.map((incident) => (
                <option
                  key={incident.id}
                  value={incident.id}
                >
                  #{incident.id} — {incident.category} —{" "}
                  {incident.hall_name
                    ? `${incident.hall_name} — `
                    : ""}
                  {incident.scope === "GLOBAL"
                    ? "Global"
                    : `Examination #${incident.examination_id}`}
                </option>
              ))}
            </select>
          </div>

          {inProgress && (
            <label className="mt-3 flex items-start gap-2 text-xs text-yellow-800">
              <input
                type="checkbox"
                checked={acknowledgeInProgress}
                onChange={(e) =>
                  setAcknowledgeInProgress(e.target.checked)
                }
                disabled={busy}
                className="mt-0.5"
              />
              <span>
                I confirm the examination is currently in
                progress and I have assessed the operational
                situation. Apply only if moving students is
                safe.
              </span>
            </label>
          )}

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

          <div className="mt-6">

            <h4 className="text-sm font-bold text-text">
              Reallocation Reasons
            </h4>

            {Array.isArray(proposal.explanations) &&
            proposal.explanations.length > 0 ? (
              <div className="mt-3 space-y-2">
                {proposal.explanations.map((ex, i) => (
                  <ExplanationCard key={i} explanation={ex} />
                ))}
              </div>
            ) : (
              <div className="mt-3 rounded-xl border border-border bg-surface px-4 py-3">
                <p className="text-sm text-text-muted">
                  No specific explanation was returned.
                </p>
              </div>
            )}

          </div>

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
                proposal.validation?.status !== "VALID" ||
                (emergencyMode && inProgress && !acknowledgeInProgress)
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
                  {emergencyMode
                    ? "Approve Emergency Reallocation"
                    : "Approve Reallocation"}
                </>
              )}
            </button>

          </div>

        </div>
      )}

{incidentOpen && (
  <div
    className="fixed inset-0 z-[80] flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm"
    onMouseDown={(event) => {
      if (event.target === event.currentTarget) closeIncidentModal();
    }}
  >
    <div className="w-full max-w-xl rounded-2xl bg-surface shadow-2xl">

      <div className="flex items-center justify-between border-b border-border px-6 py-5">
        <div>
          <h2 className="text-lg font-bold text-text">
            Report Hall Incident
          </h2>
          <p className="mt-1 text-sm text-text-muted">
            Persist this hall as unavailable. This is a
            separate action from the What-If simulation.
          </p>
        </div>

        <button
          type="button"
          onClick={closeIncidentModal}
          disabled={incidentSubmitting}
          className="rounded-lg p-2 text-text-muted hover:bg-surface-muted"
        >
          ×
        </button>
      </div>

      <div className="space-y-4 p-6">

        <div>
          <label className="mb-2 block text-sm font-semibold text-sidebar">
            Category
          </label>
          <select
            value={incidentCategory}
            onChange={(e) => setIncidentCategory(e.target.value)}
            disabled={incidentSubmitting}
            className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-sm"
          >
            <option value="MAINTENANCE">Maintenance</option>
            <option value="EQUIPMENT_FAILURE">Equipment failure</option>
            <option value="FACILITY_DAMAGE">Facility damage</option>
            <option value="TEMPORARY_UNAVAILABLE">Temporary unavailability</option>
            <option value="OTHER">Other</option>
          </select>
        </div>

        <div>
          <label className="mb-2 block text-sm font-semibold text-sidebar">
            Description
          </label>
          <textarea
            rows={3}
            value={incidentDescription}
            onChange={(e) => setIncidentDescription(e.target.value)}
            disabled={incidentSubmitting}
            placeholder="Describe the issue briefly."
            className="w-full resize-none rounded-xl border border-border bg-surface px-4 py-3 text-sm"
          />
        </div>

        <div>
          <label className="mb-2 block text-sm font-semibold text-sidebar">
            Scope
          </label>
          <select
            value={incidentScope}
            onChange={(e) => setIncidentScope(e.target.value)}
            disabled={incidentSubmitting}
            className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-sm"
          >
            <option value="GLOBAL">
              Global — affects every examination until resolved
            </option>
            <option value="EXAM_SPECIFIC">
              Exam-specific — affects this examination only
            </option>
          </select>
        </div>

        {incidentError && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {incidentError}
          </div>
        )}

        {incidentInfo && (
          <div className="rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
            {incidentInfo}
          </div>
        )}

        <div className="flex justify-end gap-3 border-t border-border pt-5">
          <button
            type="button"
            onClick={closeIncidentModal}
            disabled={incidentSubmitting}
            className="rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold text-sidebar"
          >
            Close
          </button>

          <button
            type="button"
            onClick={submitIncident}
            disabled={incidentSubmitting}
            className="rounded-xl bg-sidebar px-5 py-3 text-sm font-semibold text-white disabled:opacity-60"
          >
            {incidentSubmitting ? "Saving…" : "Report Incident"}
          </button>
        </div>

      </div>
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
function ExplanationCard({ explanation }) {
  if (!explanation || typeof explanation !== "object") {
    return (
      <div className="rounded-xl border border-border bg-surface px-4 py-3">
        <p className="text-sm text-text-muted">
          No specific explanation was returned.
        </p>
      </div>
    );
  }

  const hall = explanation.hall || "Unknown hall";
  const decision = explanation.decision || null;
  const reasons = Array.isArray(explanation.reasons)
    ? explanation.reasons
    : [];

  return (
    <div className="rounded-xl border border-border bg-surface px-4 py-3">

      <div className="flex items-center justify-between gap-2">
        <p className="text-sm font-semibold text-text">
          {hall}
        </p>

        {decision && (
          <span
            className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${
              decision === "SELECTED"
                ? "bg-green-50 text-green-700"
                : "bg-yellow-50 text-warning"
            }`}
          >
            {decision}
          </span>
        )}
      </div>

      {reasons.length === 0 ? (
        <p className="mt-2 text-sm text-text-muted">
          No specific explanation was returned.
        </p>
      ) : (
        <ul className="mt-2 space-y-1.5">
          {reasons.map((r, i) => (
            <li key={i} className="text-sm text-text">

              {r && r.code && (
                <span className="mr-1.5 inline-flex rounded bg-surface-muted px-1.5 py-0.5 font-mono text-[11px] text-text-muted">
                  {r.code}
                </span>
              )}

              <span>
                {r && r.message
                  ? r.message
                  : "No message provided."}
              </span>

            </li>
          ))}
        </ul>
      )}

    </div>
  );
}