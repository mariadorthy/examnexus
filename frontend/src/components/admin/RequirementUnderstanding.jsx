import { useState } from "react";
import {
  Sparkles,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  Building2,
  Users,
  Armchair,
  X,
} from "lucide-react";

import {
  understandRequirements,
  applyRequirements,
  applyRequirementsBulk,
} from "../../services/requirementService";
const REQUIREMENT_LABELS = {
  minimize_halls: "Minimize number of halls",
  accessibility_required: "Accessibility requirement",
  exclude_maintenance_halls:
    "Exclude halls under maintenance",
  exclude_unavailable_halls:
    "Exclude unavailable halls",
  avoid_timetable_conflicts:
    "Avoid timetable conflicts",
  generate_invigilators:
    "Generate invigilators as part of apply",
};

function RequirementUnderstanding({
  examinationId,
  examination,
  bulkExaminationIds,
  onApplied,
  onMessage,
}) {

  const [requirement, setRequirement] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Phase 2 — proposal (non-mutating)
  const [proposal, setProposal] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  // Phase 3 — apply
  const [applying, setApplying] = useState(false);
  const [applied, setApplied] = useState(null);
  const [acknowledgeUnsupported, setAcknowledgeUnsupported] =
    useState(false);

  // Mode: "single" or "bulk"
  const [mode, setMode] = useState("single");

  const bulkIds = Array.isArray(bulkExaminationIds)
    ? bulkExaminationIds.map(String)
    : [];

  const hasBulk = bulkIds.length > 0;

  const effectiveIds =
    mode === "bulk" && hasBulk
      ? bulkIds
      : (examinationId ? [String(examinationId)] : []);

  const handleUnderstand = async () => {

    if (!requirement.trim()) {
      setError("Please enter a requirement.");
      setResult(null);
      setProposal(null);
      setApplied(null);
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);
    setProposal(null);
    setApplied(null);
    setAcknowledgeUnsupported(false);

    try {
      const data = await understandRequirements(requirement);
      setResult(data);
    } catch (err) {
      const message =
        err?.response?.data?.message ||
        err?.response?.data?.validation?.errors?.join(", ") ||
        err?.message ||
        "Unable to understand the requirement.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };
  const handlePreview = async () => {

    if (effectiveIds.length === 0) {
      setError("Select an examination first.");
      return;
    }

    if (!result?.success) {
      setError("Interpret the requirement first.");
      return;
    }

    if (hasBlocking) {
      setError(
        "The requirement contains administrator-only lifecycle instructions. Remove them before previewing.",
      );
      return;
    }

    setPreviewLoading(true);
    setError("");
    setProposal(null);
    setApplied(null);

    try {
      if (mode === "bulk" && hasBulk) {

        const data = await applyRequirementsBulk({
          examination_ids: effectiveIds,
          requirement: requirement.trim(),
          // no confirm — dry run
        });

        setProposal({
          ...data,
          mode: "preview",
          __bulk: true,
        });
      } else {

        const data = await applyRequirements(
          effectiveIds[0],
          {
            requirement: requirement.trim(),
          },
        );

        setProposal(data);
      }
    } catch (err) {

      const payload =
        err?.response?.data ||
        err?.payload ||
        null;

      const message =
        payload?.message ||
        err?.message ||
        "Unable to generate a proposal.";

      setError(message);

      if (payload) {
        setProposal({
          ...payload,
          mode: "refused",
        });
      }
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleDiscardProposal = () => {
    setProposal(null);
    setApplied(null);
    setError("");
  };

  const handleApply = async () => {

    if (!proposal) return;

    if (proposal.mode !== "preview") return;

    const confirmed = window.confirm(
      "Apply this allocation proposal?\n\n" +
      "The existing hall and seat allocation for the target " +
      "examination(s) will be regenerated. If the prompt " +
      "requested invigilators, they will also be generated. " +
      "This does NOT approve or publish the examination."
    );

    if (!confirmed) return;

    setApplying(true);
    setError("");

    try {
      if (proposal.__bulk) {

        const expectedMap = {};
        for (const row of proposal.results || []) {
          if (row?.examination?.updated_at) {
            expectedMap[String(row.examination_id)] =
              row.examination.updated_at;
          }
        }

        const data = await applyRequirementsBulk({
          examination_ids: proposal.examination_ids,
          requirement: requirement.trim(),
          confirm: true,
          acknowledge_unsupported: acknowledgeUnsupported,
          expected_updated_at_map: expectedMap,
        });

        setApplied({
          ...data,
          __bulk: true,
        });
        setProposal(null);

        if (typeof onApplied === "function") onApplied();
        if (typeof onMessage === "function") {
          const failed = (data.results || []).filter(
            (r) => r.status !== "APPLIED",
          );
          if (failed.length === 0) {
            onMessage(
              `Bulk proposal applied to ${data.results.length} examination(s).`,
              "success",
            );
          } else {
            onMessage(
              `Bulk applied with ${failed.length} issue(s). Review per-row results.`,
              "error",
            );
          }
        }
      } else {

        const expectedUpdatedAt =
          proposal?.examination?.updated_at || null;

        const singleId =
          proposal?.examination?.id || effectiveIds[0];

        if (!singleId) {
          setError(
            "Proposal is missing the examination id. " +
            "Re-run the preview.",
          );
          setApplying(false);
          return;
        }

        const body = {
          requirement: requirement.trim(),
          confirm: true,
          acknowledge_unsupported: acknowledgeUnsupported,
        };

        if (expectedUpdatedAt) {
          body.expected_updated_at = expectedUpdatedAt;
        }

        const data = await applyRequirements(singleId, body);

        setApplied(data);
        setProposal(null);

        if (typeof onApplied === "function") onApplied();
        if (typeof onMessage === "function") {
          onMessage(
            data?.message || "Proposal applied.",
            "success",
          );
        }
      }
    } catch (err) {

      const payload =
        err?.response?.data || null;

      const message =
        payload?.message ||
        err?.message ||
        "Unable to apply the proposal.";

      setError(message);

      if (typeof onMessage === "function") {
        onMessage(message, "error");
      }

      if (
        err?.response?.status === 409 ||
        err?.status === 409
      ) {
        setProposal(null);
      }
    } finally {
      setApplying(false);
    }
  };

  const recognizedRequirements =
    result?.requirements
      ? Object.entries(result.requirements).filter(
        ([, enabled]) => enabled === true,
      )
      : [];

  const unsupportedRequirements =
    result?.unsupported_requirements || [];

  const blockingRequirements =
    result?.blocking_requirements || [];

  const hasUnsupported = unsupportedRequirements.length > 0;
  const hasBlocking = blockingRequirements.length > 0;

    // Preview availability depends on the active mode:
  //   - single: requires a single exam id from the top dropdown
  //   - bulk:   requires at least one exam selected in the bulk selector
  const hasTargetForPreview =
    mode === "bulk" ? hasBulk : Boolean(examinationId);

  const proposalReady =
    proposal &&
    proposal.mode === "preview" &&
    proposal.validation?.status === "VALID" &&
    proposal.readiness?.ready_for_allocation === true;
  
  const proposalBlocked =
    proposal &&
    proposal.mode === "preview" &&
    !proposalReady;

  return (
    <div className="mb-8 overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">

      {/* HEADER */}
      <div className="border-b border-gray-200 bg-gray-50 px-6 py-5">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-sidebar text-white">
            <Sparkles size={19} />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              Natural-Language Requirement Understanding
            </h2>
            <p className="mt-1 max-w-3xl text-sm leading-6 text-gray-600">
              Describe examination requirements in plain
              language. The system interprets them and, when an
              examination is selected, proposes an allocation.
              Nothing is written until you explicitly approve the
              proposal.
            </p>

            {mode === "single" && examination && (
              <p className="mt-2 text-xs font-medium text-gray-500">
                Target examination:{" "}
                <span className="font-semibold text-gray-700">
                  #{examination.id} — {examination.name}
                </span>{" "}
                <span className="ml-1 rounded-full bg-gray-200 px-2 py-0.5 text-[10px] font-semibold text-gray-700">
                  {examination.status || "DRAFT"}
                </span>
              </p>
            )}

            {mode === "bulk" && hasBulk && (
              <p className="mt-2 text-xs font-medium text-gray-500">
                Bulk mode — {bulkIds.length} examination(s)
                selected in the bulk selector.
              </p>
            )}
            {mode === "single" && (
              <p className="mt-2 text-xs text-gray-500">
                Single-examination workflow. Uses the examination
                selected in the dropdown above.
              </p>
            )}
            {mode === "bulk" && (
              <p className="mt-2 text-xs text-gray-500">
                Bulk workflow. Uses the examinations selected in
                the bulk selector below.
              </p>
            )}
          </div>
        </div>
      </div>

      {/* CONTENT */}
      <div className="p-6">
        <div className="space-y-4">
          {/* MODE TOGGLE */}
          <div className="flex flex-wrap items-center gap-2 rounded-xl border border-gray-200 bg-gray-50 p-1 text-xs font-semibold">
            <button
              type="button"
              onClick={() => {
                setMode("single");
                setProposal(null);
                setApplied(null);
                setError("");
              }}
              className={`rounded-lg px-3 py-1.5 transition ${
                mode === "single"
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-500 hover:text-gray-800"
              }`}
            >
              Single examination
            </button>

            <button
              type="button"
              disabled={!hasBulk}
              onClick={() => {
                setMode("bulk");
                setProposal(null);
                setApplied(null);
                setError("");
              }}
              className={`rounded-lg px-3 py-1.5 transition ${
                mode === "bulk"
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-500 hover:text-gray-800"
              } disabled:cursor-not-allowed disabled:opacity-50`}
              title={
                !hasBulk
                  ? "Select examinations in the bulk selector below first."
                  : undefined
              }
            >
              Bulk ({bulkIds.length || 0})
            </button>
          </div>

          {/* VISIBLE MODE HINT */}
          {!hasBulk && (
            <p className="text-xs text-gray-500">
              Select examinations in the bulk selector below to
              enable bulk mode.
            </p>
          )}

          {hasBulk && mode === "bulk" && (
            <p className="text-xs text-amber-700">
              Bulk mode active — {bulkIds.length} examination(s)
              will be targeted when you click Preview or Apply.
            </p>
          )}
          
          {/* INPUT */}
          <div>
            <label
              htmlFor="examination-requirement"
              className="mb-2 block text-sm font-medium text-gray-800"
            >
              Examination Requirement
            </label>
            <textarea
              id="examination-requirement"
              value={requirement}
              onChange={(event) =>
                setRequirement(event.target.value)
              }
              placeholder="Example: Allocate students for the End Semester Examination using the minimum number of suitable halls. Keep students requiring accessibility support in accessible halls and avoid halls with reported incidents."
              rows={4}
              className="w-full resize-y rounded-xl border border-gray-300 bg-white px-4 py-3 text-sm text-gray-900 outline-none transition placeholder:text-gray-400 focus:border-primary focus:ring-2 focus:ring-primary/20"
            />
          </div>
          {/* ACTIONS */}
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={handleUnderstand}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Sparkles size={17} />
              {loading ? "Understanding..." : "Understand Requirements"}
            </button>

            <button
              type="button"
              onClick={handlePreview}
              disabled={
                previewLoading ||
                loading ||
                !result?.success ||
                !hasTargetForPreview ||
                (hasUnsupported && !acknowledgeUnsupported)
              }
              title={
                !hasTargetForPreview
                  ? mode === "bulk"
                    ? "Select at least one examination in the bulk selector below first."
                    : "Select an examination above first."
                  : hasUnsupported && !acknowledgeUnsupported
                    ? "Acknowledge the unsupported requirements below to continue."
                    : undefined
              }         
              className="inline-flex items-center gap-2 rounded-xl border border-gray-300 bg-white px-5 py-2.5 text-sm font-semibold text-gray-800 shadow-sm transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <ShieldCheck size={17} />
              {previewLoading ? "Preparing preview..." : "Preview Proposal"}
            </button>
          </div>
          {/* VISIBLE DISABLED REASON */}
          {!previewLoading && !loading && (
            <>
              {!hasTargetForPreview && mode === "single" && (
                <p className="text-xs text-gray-500">
                  Select an examination above to enable the preview.
                </p>
              )}

              {!hasTargetForPreview && mode === "bulk" && (
                <p className="text-xs text-gray-500">
                  Select at least one examination in the bulk
                  selector below to enable the preview.
                </p>
              )}

              {hasTargetForPreview && !result?.success && (
                <p className="text-xs text-gray-500">
                  Interpret the requirement first — then you can
                  preview a proposal.
                </p>
              )}

              {hasTargetForPreview &&
                result?.success &&
                hasUnsupported &&
                !acknowledgeUnsupported && (
                  <p className="text-xs text-amber-700">
                    Acknowledge the unsupported requirements below
                    to enable the preview.
                  </p>
                )}
            </>
          )}
          {/* HARD-BLOCKING (LIFECYCLE INSTRUCTIONS) */}
          {hasBlocking && (
            <div className="rounded-xl border border-red-300 bg-red-50 p-4 text-sm text-red-800">
              <div className="flex items-start gap-3">
                <AlertCircle size={18} className="mt-0.5 shrink-0" />
                <div>
                  <p className="font-semibold">
                    This requirement contains administrator-only
                    instructions.
                  </p>
                  <p className="mt-1">
                    Validation, review, approval and publication
                    are actions the administrator performs in the
                    Review &amp; Approve tab. They cannot be
                    triggered from the natural-language workflow.
                    Remove these from the requirement and try
                    again.
                  </p>
                  <ul className="mt-2 list-disc space-y-1 pl-5">
                    {blockingRequirements.map((item, idx) => (
                      <li key={idx}>
                        <span className="font-semibold">
                          {item.requirement}
                        </span>{" "}
                        — {item.reason}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* ERROR */}
          {error && (
            <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              <AlertCircle size={18} className="mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* INTERPRETED REQUIREMENTS */}
          {result && (
            <div className="overflow-hidden rounded-xl border border-gray-200 bg-gray-50">

              <div className="border-b border-gray-200 px-5 py-4">
                <div className="flex items-center gap-2">
                  <CheckCircle2 size={18} className="text-primary" />
                  <h3 className="text-sm font-semibold text-gray-900">
                    Interpreted Requirements
                  </h3>
                </div>
              </div>

              <div className="space-y-5 p-5">

                {recognizedRequirements.length === 0 ? (
                  <p className="text-sm text-gray-600">
                    No supported requirements were identified.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {recognizedRequirements.map(([key]) => (
                      <div
                        key={key}
                        className="flex items-center gap-3 rounded-lg border border-gray-200 bg-white px-4 py-3"
                      >
                        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent/10 text-accent">
                          <CheckCircle2 size={16} />
                        </div>
                        <span className="text-sm font-medium text-gray-800">
                          {REQUIREMENT_LABELS[key] || key}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {hasUnsupported && (
                  <div>
                    <div className="mb-3 flex items-center gap-2">
                      <AlertCircle size={17} className="text-accent" />
                      <h3 className="text-sm font-semibold text-gray-900">
                        Unsupported Requirements
                      </h3>
                    </div>

                    <div className="space-y-2">
                      {unsupportedRequirements.map((item, index) => (
                        <div
                          key={`${item.requirement}-${index}`}
                          className="rounded-lg border border-gray-200 bg-white p-4"
                        >
                          <p className="text-sm font-medium text-gray-900">
                            {item.requirement}
                          </p>
                          <p className="mt-1 text-sm leading-5 text-gray-600">
                            {item.reason}
                          </p>
                        </div>
                      ))}
                    </div>

                    <label className="mt-4 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                      <input
                        type="checkbox"
                        checked={acknowledgeUnsupported}
                        onChange={(event) =>
                          setAcknowledgeUnsupported(
                            event.target.checked,
                          )
                        }
                        className="mt-0.5 h-4 w-4 rounded border-amber-400"
                      />
                      <span>
                        I acknowledge these unsupported
                        requirements. The proposal will apply
                        only the supported requirements.
                      </span>
                    </label>
                  </div>
                )}

                <div className="border-t border-gray-200 pt-4">
                  <div className="rounded-lg border border-gray-200 bg-white px-4 py-3">
                    <p className="text-xs leading-5 text-gray-500">
                      These interpreted requirements do not
                      directly modify examinations, halls,
                      seats, invigilators, approvals, or
                      published data. Existing deterministic
                      allocation, validation and lifecycle
                      remain the source of truth.
                    </p>
                  </div>
                </div>

              </div>
            </div>
          )}

          {/* PROPOSAL (preview) — SINGLE */}
          {proposal && proposal.mode === "preview" && !proposal.__bulk && (
            <ProposalPanel
              proposal={proposal}
              examination={examination}
              onApply={handleApply}
              onDiscard={handleDiscardProposal}
              applying={applying}
              ready={proposalReady}
              blocked={proposalBlocked}
            />
          )}

          {/* PROPOSAL (preview) — BULK */}
          {proposal && proposal.mode === "preview" && proposal.__bulk && (
            <BulkProposalPanel
              proposal={proposal}
              onApply={handleApply}
              onDiscard={handleDiscardProposal}
              applying={applying}
            />
          )}

          {/* PROPOSAL REFUSED */}
          {proposal && proposal.mode === "refused" && (
            <RefusedPanel proposal={proposal} />
          )}

          {/* APPLIED — SINGLE */}
          {applied && !applied.__bulk && (
            <AppliedPanel result={applied} />
          )}

          {/* APPLIED — BULK */}
          {applied && applied.__bulk && (
            <BulkAppliedPanel result={applied} />
          )}

        </div>
      </div>
    </div>
  );
}


/* ========================================================= */
/* PROPOSAL PANEL                                            */
/* ========================================================= */

function ProposalPanel({
  proposal,
  examination,
  onApply,
  onDiscard,
  applying,
  ready,
  blocked,
}) {

  const proposed = proposal.proposed_allocations || [];
  const counts = proposal.proposed_counts || {};
  const validation = proposal.validation || {};
  const readiness = proposal.readiness || {};

  return (
    <div className="overflow-hidden rounded-xl border border-amber-200 bg-amber-50">

      <div className="flex items-center justify-between border-b border-amber-200 px-5 py-4">
        <div className="flex items-center gap-2">
          <AlertCircle size={18} className="text-amber-700" />
          <h3 className="text-sm font-semibold text-amber-900">
            Proposal — not yet applied
          </h3>
        </div>
        <button
          type="button"
          onClick={onDiscard}
          disabled={applying}
          className="rounded-lg p-1.5 text-amber-800 transition hover:bg-amber-100 disabled:opacity-50"
          aria-label="Discard proposal"
        >
          <X size={18} />
        </button>
      </div>

      <div className="space-y-5 bg-white p-5">

        {/* EXAM CONTEXT */}
        {proposal.examination && (
          <div className="rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-700">
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
              <span>
                <span className="font-semibold">
                  #{proposal.examination.id}
                </span>{" "}
                — {proposal.examination.name}
              </span>
              <span className="rounded-full bg-gray-200 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-gray-700">
                {proposal.examination.status || "DRAFT"}
              </span>
            </div>
          </div>
        )}

        {/* READINESS */}
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-gray-800">
              Readiness
            </p>
            <span
              className={`rounded-full px-3 py-1 text-xs font-semibold ${readiness.ready_for_allocation
                  ? "bg-green-50 text-green-700"
                  : "bg-red-50 text-red-700"
                }`}
            >
              {readiness.ready_for_allocation ? "READY" : "NOT READY"}
            </span>
          </div>

          <div className="mt-3 grid gap-3 sm:grid-cols-3">
            <MiniStat
              label="Eligible students"
              value={
                readiness.student_eligibility
                  ?.eligible_student_count ?? 0
              }
            />
            <MiniStat
              label="Timetable entries"
              value={readiness.timetable_entry_count ?? 0}
            />
            <MiniStat
              label="Worst shortage"
              value={readiness.capacity_check?.shortage ?? 0}
            />
          </div>

          {readiness.capacity_check?.per_timetable?.length > 0 && (
            <ul className="mt-3 space-y-1 text-xs text-gray-600">
              {readiness.capacity_check.per_timetable.map((row) => (
                <li key={row.timetable_id}>
                  {row.exam_date} · {row.session}:{" "}
                  {row.available_capacity}/{row.required_capacity}
                  {row.sufficient ? " ✓" : ` (short ${row.shortage})`}
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* COUNTS */}
        <div className="grid gap-3 sm:grid-cols-4">
          <MiniStat label="Students" value={counts.students ?? 0} icon={Users} />
          <MiniStat label="Halls used" value={counts.halls ?? 0} icon={Building2} />
          <MiniStat label="Capacity" value={counts.allocated_capacity ?? 0} icon={Armchair} />
          <MiniStat
            label="Accessibility"
            value={counts.accessibility_students ?? 0}
          />
        </div>

        {/* PROPOSED HALLS */}
        <div className="rounded-lg border border-gray-200">
          <div className="border-b border-gray-200 bg-gray-50 px-4 py-3">
            <p className="text-sm font-semibold text-gray-800">
              Proposed halls
            </p>
          </div>
          {proposed.length === 0 ? (
            <p className="px-4 py-4 text-sm text-gray-500">
              No halls in this proposal.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[520px]">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                    <th className="px-4 py-2">Timetable</th>
                    <th className="px-4 py-2">Hall ID</th>
                    <th className="px-4 py-2">Capacity</th>
                    <th className="px-4 py-2">Purpose</th>
                  </tr>
                </thead>
                <tbody>
                  {proposed.map((row, index) => (
                    <tr
                      key={`${row.timetable_id}-${row.hall_id}-${index}`}
                      className="border-b border-gray-100 last:border-0 text-sm text-gray-700"
                    >
                      <td className="px-4 py-2">
                        #{row.timetable_id}
                      </td>
                      <td className="px-4 py-2">
                        #{row.hall_id}
                      </td>
                      <td className="px-4 py-2">
                        {row.allocated_capacity}
                      </td>
                      <td className="px-4 py-2">
                        {row.purpose || "NORMAL"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* VALIDATION */}
        <div
          className={`rounded-lg border px-4 py-3 text-sm ${validation.status === "VALID"
              ? "border-green-200 bg-green-50 text-green-700"
              : "border-red-200 bg-red-50 text-red-700"
            }`}
        >
          <p className="font-semibold">
            Proposed-plan validation: {validation.status || "UNKNOWN"}
          </p>
          {validation.errors?.length > 0 && (
            <ul className="mt-2 list-disc space-y-1 pl-5">
              {validation.errors.map((line, idx) => (
                <li key={idx}>{line}</li>
              ))}
            </ul>
          )}
        </div>

        {/* ACTIONS */}
        <div className="flex flex-col-reverse gap-3 border-t border-gray-200 pt-4 sm:flex-row sm:justify-end">
          <button
            type="button"
            onClick={onDiscard}
            disabled={applying}
            className="rounded-xl border border-gray-300 bg-white px-5 py-2.5 text-sm font-semibold text-gray-800 transition hover:bg-gray-50 disabled:opacity-50"
          >
            Discard Proposal
          </button>

          <button
            type="button"
            onClick={onApply}
            disabled={applying || !ready}
            title={
              blocked
                ? "Resolve the blockers above before applying."
                : undefined
            }
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-sidebar px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-primary disabled:cursor-not-allowed disabled:opacity-50"
          >
            {applying ? "Applying..." : "Apply Proposal"}
          </button>
        </div>
      </div>
    </div>
  );
}


/* ========================================================= */
/* REFUSED PANEL                                             */
/* ========================================================= */

function RefusedPanel({ proposal }) {
  return (
    <div className="overflow-hidden rounded-xl border border-red-200 bg-red-50">
      <div className="flex items-center gap-2 border-b border-red-200 px-5 py-4">
        <AlertCircle size={18} className="text-red-700" />
        <h3 className="text-sm font-semibold text-red-900">
          No proposal could be generated
        </h3>
      </div>
      <div className="bg-white p-5 text-sm text-gray-700">
        <p>{proposal.message || "The plan could not be produced."}</p>

        {proposal.readiness && (
          <div className="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">
              Readiness
            </p>
            <p className="mt-1 text-sm text-gray-700">
              Ready:{" "}
              {proposal.readiness.ready_for_allocation
                ? "YES"
                : "NO"}
            </p>
            {proposal.readiness.capacity_check
              ?.per_timetable?.length > 0 && (
                <ul className="mt-2 space-y-1 text-xs text-gray-600">
                  {proposal.readiness.capacity_check.per_timetable.map(
                    (row) => (
                      <li key={row.timetable_id}>
                        {row.exam_date} · {row.session}:{" "}
                        {row.available_capacity}/{row.required_capacity}
                        {row.sufficient
                          ? " ✓"
                          : ` (short ${row.shortage})`}
                      </li>
                    ),
                  )}
                </ul>
              )}
          </div>
        )}
      </div>
    </div>
  );
}


/* ========================================================= */
/* APPLIED PANEL                                             */
/* ========================================================= */

function AppliedPanel({ result }) {
  const validation = result?.validation || {};

  return (
    <div className="overflow-hidden rounded-xl border border-green-200 bg-green-50">
      <div className="flex items-center gap-2 border-b border-green-200 px-5 py-4">
        <CheckCircle2 size={18} className="text-green-700" />
        <h3 className="text-sm font-semibold text-green-900">
          Proposal applied
        </h3>
      </div>
      <div className="space-y-3 bg-white p-5 text-sm text-gray-700">
        <p>
          {result?.message ||
            "Allocation was applied. The examination lifecycle is unchanged."}
        </p>

        <div className="rounded-lg border border-gray-200 bg-gray-50 px-4 py-3">
          <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">
            Post-apply validation
          </p>
          <p className="mt-1 font-semibold text-gray-800">
            {validation.status || "UNKNOWN"}
          </p>
          {validation.errors?.length > 0 && (
            <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-red-700">
              {validation.errors.map((line, idx) => (
                <li key={idx}>{line}</li>
              ))}
            </ul>
          )}
        </div>

        <p className="text-xs text-gray-500">
          The examination lifecycle has not been advanced. Use the
          Review &amp; Approve tab to move this examination through
          GENERATED → VALIDATED → REVIEW → APPROVED → PUBLISHED.
        </p>
      </div>
    </div>
  );
}


/* ========================================================= */
/* MINI STAT                                                 */
/* ========================================================= */

function MiniStat({ label, value, icon: Icon }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white px-3 py-2">
      <div className="flex items-center justify-between">
        <p className="text-xs text-gray-500">{label}</p>
        {Icon ? <Icon size={14} className="text-gray-400" /> : null}
      </div>
      <p className="mt-1 text-lg font-bold text-gray-900">{value}</p>
    </div>
  );
}

/* ========================================================= */
/* BULK PROPOSAL PANEL                                       */
/* ========================================================= */

function BulkProposalPanel({ proposal, onApply, onDiscard, applying }) {

  const rows = proposal.results || [];
  const anyPreviewOk = rows.some(
    (r) => r.status === "PREVIEW" && r.validation?.status === "VALID",
  );

  return (
    <div className="overflow-hidden rounded-xl border border-amber-200 bg-amber-50">

      <div className="flex items-center justify-between border-b border-amber-200 px-5 py-4">
        <div className="flex items-center gap-2">
          <AlertCircle size={18} className="text-amber-700" />
          <h3 className="text-sm font-semibold text-amber-900">
            Bulk proposal — not yet applied
          </h3>
        </div>
        <button
          type="button"
          onClick={onDiscard}
          disabled={applying}
          className="rounded-lg p-1.5 text-amber-800 transition hover:bg-amber-100 disabled:opacity-50"
          aria-label="Discard proposal"
        >
          <X size={18} />
        </button>
      </div>

      <div className="space-y-4 bg-white p-5">

        <p className="text-xs text-gray-500">
          Interpreted options:{" "}
          {(proposal.applied_options || []).join(", ") || "—"}
        </p>

        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="w-full min-w-[720px]">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                <th className="px-4 py-2">Examination</th>
                <th className="px-4 py-2">Status</th>
                <th className="px-4 py-2">Halls</th>
                <th className="px-4 py-2">Students</th>
                <th className="px-4 py-2">Validation</th>
                <th className="px-4 py-2">Notes</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr
                  key={row.examination_id}
                  className="border-b border-gray-100 last:border-0 text-sm text-gray-700"
                >
                  <td className="px-4 py-2">
                    #{row.examination_id}
                    {row.examination?.name
                      ? ` — ${row.examination.name}`
                      : ""}
                  </td>
                  <td className="px-4 py-2">{row.status}</td>
                  <td className="px-4 py-2">
                    {row.proposed_counts?.halls ?? "—"}
                  </td>
                  <td className="px-4 py-2">
                    {row.proposed_counts?.students ?? "—"}
                  </td>
                  <td className="px-4 py-2">
                    {row.validation?.status ?? "—"}
                  </td>
                  <td className="px-4 py-2 text-xs text-gray-500">
                    {row.message || ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="flex flex-col-reverse gap-3 border-t border-gray-200 pt-4 sm:flex-row sm:justify-end">
          <button
            type="button"
            onClick={onDiscard}
            disabled={applying}
            className="rounded-xl border border-gray-300 bg-white px-5 py-2.5 text-sm font-semibold text-gray-800 transition hover:bg-gray-50 disabled:opacity-50"
          >
            Discard Proposal
          </button>
          <button
            type="button"
            onClick={onApply}
            disabled={applying || !anyPreviewOk}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-sidebar px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-primary disabled:cursor-not-allowed disabled:opacity-50"
          >
            {applying ? "Applying..." : "Apply Proposal"}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ========================================================= */
/* BULK APPLIED PANEL                                        */
/* ========================================================= */

function BulkAppliedPanel({ result }) {
  const rows = result.results || [];

  return (
    <div className="overflow-hidden rounded-xl border border-green-200 bg-green-50">
      <div className="flex items-center gap-2 border-b border-green-200 px-5 py-4">
        <CheckCircle2 size={18} className="text-green-700" />
        <h3 className="text-sm font-semibold text-green-900">
          Bulk proposal applied
        </h3>
      </div>
      <div className="space-y-3 bg-white p-5 text-sm text-gray-700">
        <p className="text-xs text-gray-500">
          Applied options:{" "}
          {(result.applied_options || []).join(", ") || "—"}
        </p>

        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="w-full min-w-[720px]">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                <th className="px-4 py-2">Examination</th>
                <th className="px-4 py-2">Status</th>
                <th className="px-4 py-2">Hall validation</th>
                <th className="px-4 py-2">Invigilator validation</th>
                <th className="px-4 py-2">Notes</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr
                  key={row.examination_id}
                  className="border-b border-gray-100 last:border-0 text-sm text-gray-700"
                >
                  <td className="px-4 py-2">
                    #{row.examination_id}
                  </td>
                  <td className="px-4 py-2">{row.status}</td>
                  <td className="px-4 py-2">
                    {row.validation?.status || "—"}
                  </td>
                  <td className="px-4 py-2">
                    {row.invigilator_validation?.status || "—"}
                  </td>
                  <td className="px-4 py-2 text-xs text-gray-500">
                    {row.partial_failure?.message ||
                      row.message ||
                      ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="text-xs text-gray-500">
          The examination lifecycle has not been advanced. Use
          the Review &amp; Approve tab to move each examination
          through GENERATED → VALIDATED → REVIEW → APPROVED →
          PUBLISHED.
        </p>
      </div>
    </div>
  );
}

export default RequirementUnderstanding;