import { useEffect, useState } from "react";
import {
  ClipboardList,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Users,
  Building2,
  Armchair,
  Eye,
  Sparkles,
  Lock,
  Pencil,
} from "lucide-react";

import AllocationDetails from "./AllocationDetails";
import AllocationForm from "./AllocationForm";
import SeatAllocationPanel from "./SeatAllocationPanel";
import InvigilatorPanel from "./InvigilatorPanel";
import ApprovalPanel from "./ApprovalPanel";
import WhatIfReallocation from "./WhatIfReallocation";

import {
  get,
  post,
} from "../../../services/api";
import {
  generateBulkSeatAllocation,
  bulkValidateExaminations,
} from "../../../services/allocationService";
import {
  generateBulkInvigilators,
} from "../../../services/invigilatorService";
import AdminSidebar from "../../../components/AdminSidebar";
import AdminTopbar from "../../../components/AdminTopbar";
import RequirementUnderstanding from "../../../components/admin/RequirementUnderstanding";

function Allocations({
  user,
  onLogout,
  onNavigate,
}) {
  const [sidebarOpen, setSidebarOpen] =
    useState(false);

const [activeAllocationTab, setActiveAllocationTab] =
  useState("hall");

  const [examinations, setExaminations] = useState([]);
  const [selectedExamination, setSelectedExamination] = useState("");

  const [summary, setSummary] = useState(null);
  const [allocations, setAllocations] = useState([]);

  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [loadingAllocations, setLoadingAllocations] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

    const [showDetails, setShowDetails] =
    useState(false);
    
        const [editingAllocation, setEditingAllocation] =
    useState(null);

    const [selectedBulkExaminations, setSelectedBulkExaminations] =
    useState([]);

  const [bulkGenerating, setBulkGenerating] =
    useState(false);

    const [bulkResult, setBulkResult] =
    useState(null);

  const [bulkSeatGenerating, setBulkSeatGenerating] =
    useState(false);
  const [bulkSeatResult, setBulkSeatResult] =
    useState(null);

  const [bulkInvigGenerating, setBulkInvigGenerating] =
    useState(false);
  const [bulkInvigResult, setBulkInvigResult] =
    useState(null);

  const [bulkValidating, setBulkValidating] =
    useState(false);
  const [bulkValidationResult, setBulkValidationResult] =
    useState(null);

  useEffect(() => {
    loadExaminations();
  }, []);

  useEffect(() => {
    if (selectedExamination) {
      loadAllocationData(selectedExamination);
    } else {
      setSummary(null);
      setAllocations([]);
    }
  }, [selectedExamination]);

  const loadExaminations = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await get("/examinations/");

      setExaminations(data);
    } catch (err) {
      console.error("Examinations error:", err);

      setError(
        "Unable to load examinations. Please make sure the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  const loadAllocationData = async (examinationId) => {
    try {
      setLoadingAllocations(true);
      setError("");
      setSuccess("");

      const [summaryData, allocationsData] =
        await Promise.all([
          get(
            `/allocations/summary/${examinationId}`
          ),
          get(
            `/allocations/${examinationId}`
          ),
        ]);

      setSummary(summaryData);
      setAllocations(allocationsData);
    } catch (err) {
      console.error("Allocation data error:", err);

      setError(
        "Unable to load allocation information."
      );

      setSummary(null);
      setAllocations([]);
    } finally {
      setLoadingAllocations(false);
    }
  };

const handleGenerateAllocation = async () => {
  if (!selectedExamination) {
    setError("Please select an examination first.");
    return;
  }

  const confirmed = window.confirm(
    `Generate hall allocation for Examination #${selectedExamination}?`
  );

  if (!confirmed) {
    return;
  }

  try {
    setGenerating(true);
    setError("");
    setSuccess("");

    let data;

    try {
      // First attempt: normal generation.
      data = await post(
        `/allocations/generate/${selectedExamination}`,
        {}
      );
    } catch (err) {
      // Existing allocation detected.
      if (
        err.message?.includes(
          "Use force=true to regenerate"
        )
      ) {
        const regenerate = window.confirm(
          `An allocation already exists for Examination #${selectedExamination}.\n\n` +
          `Do you want to regenerate it?\n\n` +
          `The existing hall, seat and invigilator allocation state will be replaced.`
        );

        if (!regenerate) {
          return;
        }

        data = await post(
          `/allocations/generate/${selectedExamination}`,
          {
            force: true,
          }
        );
      } else {
        throw err;
      }
    }

    if (!data.success) {
      throw new Error(
        data.message ||
          "Failed to generate allocation."
      );
    }

    setSuccess(
      data.message ||
        "Allocation generated successfully."
    );

    await loadAllocationData(
      selectedExamination
    );
  } catch (err) {
    console.error(
      "Generate allocation error:",
      err
    );

    setError(
      err.message ||
        "Unable to generate allocation."
    );
  } finally {
    setGenerating(false);
  }
};

    const handleGenerateBulkAllocation = async () => {
    if (selectedBulkExaminations.length === 0) {
      setError(
        "Please select at least one examination."
      );
      return;
    }

  const selectedExamLabels =
  selectedBulkExaminations
    .map((id) => `Examination #${id}`)
    .join(", ");

const confirmed = window.confirm(
  `${selectedExamLabels} ${selectedBulkExaminations.length === 1 ? "is" : "are"} selected.\n\n` +
  `Existing hall, seat and invigilator allocations for these examinations will be replaced if they already exist.\n\n` +
  `Do you want to continue?`
);

    if (!confirmed) {
      return;
    }

    try {
      setBulkGenerating(true);
      setError("");
      setSuccess("");
      setBulkResult(null);

      const data = await post(
  "/allocations/bulk-generate",
  {
    examination_ids: selectedBulkExaminations,
    force: true,
  }
);

      if (!data.success) {
        throw new Error(
          data.message ||
          "Failed to generate bulk allocation."
        );
      }

      setBulkResult(data);

      setSuccess(
        data.message ||
        "Bulk hall allocation generated successfully."
      );

      // Refresh the examination currently selected
      // in the single-examination section if applicable.
      if (selectedExamination) {
        await loadAllocationData(
          selectedExamination
        );
      }
    } catch (err) {
      console.error(
        "Bulk allocation error:",
        err
      );

      setError(
        err.message ||
        "Unable to generate bulk allocation."
      );
    } finally {
      setBulkGenerating(false);
    }
  };

    const handleBulkExaminationChange = (
    examinationId
  ) => {
    setSelectedBulkExaminations(
      (current) => {
        if (
          current.includes(examinationId)
        ) {
          return current.filter(
            (id) => id !== examinationId
          );
        }

        return [
          ...current,
          examinationId,
        ];
      }
    );
  };

  const handleBulkSeatGeneration = async () => {
    if (selectedBulkExaminations.length === 0) {
      setError("Please select at least one examination.");
      return;
    }

    const confirmed = window.confirm(
      `Generate seat allocation for ${selectedBulkExaminations.length} examination(s)?`
    );
    if (!confirmed) return;

    try {
      setBulkSeatGenerating(true);
      setError("");
      setSuccess("");
      setBulkSeatResult(null);

      const result = await generateBulkSeatAllocation(
        selectedBulkExaminations,
        false
      );

      setBulkSeatResult(result);

      if (result.success) {
        setSuccess(
          "Bulk seat allocation completed."
        );
      } else {
        setError(
          "Bulk seat allocation completed with failures."
        );
      }
    } catch (err) {
      console.error(err);
      setError(
        err.message ||
          "Bulk seat allocation failed."
      );
    } finally {
      setBulkSeatGenerating(false);
    }
  };

  const handleBulkInvigilatorGeneration = async () => {
    if (selectedBulkExaminations.length === 0) {
      setError("Please select at least one examination.");
      return;
    }

    const confirmed = window.confirm(
      `Generate invigilator allocation for ${selectedBulkExaminations.length} examination(s)?`
    );
    if (!confirmed) return;

    try {
      setBulkInvigGenerating(true);
      setError("");
      setSuccess("");
      setBulkInvigResult(null);

      const result = await generateBulkInvigilators(
        selectedBulkExaminations,
        false
      );

      setBulkInvigResult(result);

      if (result.success) {
        setSuccess(
          "Bulk invigilator allocation completed."
        );
      } else {
        setError(
          "Bulk invigilator allocation completed with failures."
        );
      }
    } catch (err) {
      console.error(err);
      setError(
        err.message ||
          "Bulk invigilator allocation failed."
      );
    } finally {
      setBulkInvigGenerating(false);
    }
  };

  const handleBulkValidation = async () => {
    if (selectedBulkExaminations.length === 0) {
      setError("Please select at least one examination.");
      return;
    }

    try {
      setBulkValidating(true);
      setError("");
      setSuccess("");
      setBulkValidationResult(null);

      const result = await bulkValidateExaminations(
        selectedBulkExaminations
      );

      setBulkValidationResult(result);

      setSuccess(
        "Bulk validation completed. See per-examination results below."
      );
    } catch (err) {
      console.error(err);
      setError(
        err.message ||
          "Bulk validation failed."
      );
    } finally {
      setBulkValidating(false);
    }
  };

  const handleSelectAllBulkExaminations = () => {
    if (
      selectedBulkExaminations.length ===
      examinations.length
    ) {
      setSelectedBulkExaminations([]);
      return;
    }

    setSelectedBulkExaminations(
      examinations.map(
        (examination) =>
          String(examination.id)
      )
    );
  };

   const handleRefresh = async () => {
      if (!selectedExamination) {
      await loadExaminations();
      return;
    }

    await loadAllocationData(selectedExamination);
  };

  const handleEditSuccess = async () => {

    setEditingAllocation(null);

    setSuccess("Hall allocation updated successfully.");

    if (selectedExamination) {
      await loadAllocationData(selectedExamination);
    }
  };

  const selectedExam = examinations.find(
    (examination) =>
      String(examination.id) ===
      String(selectedExamination)
  );

  const allocationStatus =
    summary?.status || "NOT GENERATED";

  const isValid = allocationStatus === "VALID";

  return (
    <div className="min-h-screen bg-background">

      <AdminSidebar
        user={user}
        onLogout={onLogout}
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        activePage="Allocations"
        onNavigate={onNavigate}
      />

      <main className="lg:ml-72">

        <AdminTopbar
          user={user}
          title="Allocations"
          section="Administration"
          onOpenSidebar={() =>
            setSidebarOpen(true)
          }
        />

        <main className="p-5 md:p-8">

          {/* ================================================= */}
          {/* HEADER */}
          {/* ================================================= */}

          <section className="mb-8">

            <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">

              <div>
                <p className="text-sm font-semibold uppercase tracking-widest text-accent">
                  Examination Management
                </p>

                <h1 className="mt-1 text-2xl font-bold text-text md:text-3xl">
                  Examination Allocation
                </h1>

                <p className="mt-2 max-w-2xl text-sm leading-6 text-text-muted">
  Manage examination hall, invigilator and
  student seat allocations from one place.
</p>
              </div>

              <button
                type="button"
                onClick={handleRefresh}
                disabled={loading || loadingAllocations}
                className="flex w-fit items-center gap-2 rounded-xl border border-border bg-surface px-4 py-2.5 text-sm font-semibold text-sidebar shadow-sm transition hover:border-accent hover:bg-surface-muted disabled:cursor-not-allowed disabled:opacity-60"
              >
                <RefreshCw
                  size={17}
                  className={
                    loading || loadingAllocations
                      ? "animate-spin"
                      : ""
                  }
                />

                Refresh
              </button>

            </div>

          </section>

{/* ================================================= */}
{/* ALLOCATION MODULES */}
{/* ================================================= */}

<section className="mb-6 rounded-2xl border border-border bg-surface p-2 shadow-sm">

    <div className="grid gap-2 md:grid-cols-4">

    {/* Hall Allocation */}

    <button
      type="button"
      onClick={() =>
        setActiveAllocationTab("hall")
      }
      className={`flex items-center gap-3 rounded-xl px-4 py-4 text-left transition ${
        activeAllocationTab === "hall"
          ? "bg-sidebar text-white shadow-md"
          : "text-text hover:bg-surface-muted"
      }`}
    >

      <div
        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${
          activeAllocationTab === "hall"
            ? "bg-white/10"
            : "bg-accent-light text-primary"
        }`}
      >
        <Building2 size={20} />
      </div>

      <div className="min-w-0">

        <p className="text-sm font-bold">
          Hall Allocation
        </p>

        <p
          className={`mt-0.5 text-xs ${
            activeAllocationTab === "hall"
              ? "text-white/70"
              : "text-text-muted"
          }`}
        >
          Examination → Hall
        </p>

      </div>

    </button>


    {/* Invigilator Allocation */}

    <button
  type="button"
  onClick={() =>
    setActiveAllocationTab("invigilator")
  }
  className={`flex items-center gap-3 rounded-xl px-4 py-4 text-left transition ${
    activeAllocationTab === "invigilator"
      ? "bg-sidebar text-white shadow-md"
      : "text-text opacity-60 hover:bg-surface-muted"
  }`}
>

      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-surface-muted text-text-muted">
        <Users size={20} />
      </div>

      <div className="min-w-0 flex-1">

        <div className="flex items-center gap-2">

          <p className="text-sm font-bold text-text">
            Invigilator Allocation
          </p>

          <Lock size={13} className="text-text-muted" />

        </div>

        <p className="mt-0.5 text-xs text-text-muted">
          Hall → Staff
        </p>

      </div>

      <span className="hidden rounded-full bg-surface-muted px-2.5 py-1 text-[10px] font-semibold text-text-muted sm:inline-flex">
        Coming Next
      </span>

    </button>


    {/* Student / Seat Allocation */}

    <button
  type="button"
  onClick={() =>
    setActiveAllocationTab("seat")
  }
  className={`flex items-center gap-3 rounded-xl px-4 py-4 text-left transition ${
    activeAllocationTab === "seat"
      ? "bg-sidebar text-white shadow-md"
      : "text-text opacity-60 hover:bg-surface-muted"
  }`}
>
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-surface-muted text-text-muted">
        <Armchair size={20} />
      </div>

      <div className="min-w-0 flex-1">

        <div className="flex items-center gap-2">

          <p className="text-sm font-bold text-text">
            Student / Seat Allocation
          </p>

          <Lock size={13} className="text-text-muted" />

        </div>

        <p className="mt-0.5 text-xs text-text-muted">
          Student → Hall → Seat
        </p>

      </div>

            <span className="hidden rounded-full bg-surface-muted px-2.5 py-1 text-[10px] font-semibold text-text-muted sm:inline-flex">
        Coming Later
      </span>

    </button>

    {/* Review / Approval */}

    <button
      type="button"
      onClick={() =>
        setActiveAllocationTab("approval")
      }
      className={`flex items-center gap-3 rounded-xl px-4 py-4 text-left transition ${
        activeAllocationTab === "approval"
          ? "bg-sidebar text-white shadow-md"
          : "text-text hover:bg-surface-muted"
      }`}
    >
      <div
        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${
          activeAllocationTab === "approval"
            ? "bg-white/10"
            : "bg-accent-light text-primary"
        }`}
      >
        <CheckCircle2 size={20} />
      </div>

      <div className="min-w-0">
        <p className="text-sm font-bold">
          Review & Approve
        </p>
        <p
          className={`mt-0.5 text-xs ${
            activeAllocationTab === "approval"
              ? "text-white/70"
              : "text-text-muted"
          }`}
        >
          Validate → Approve → Publish
        </p>
      </div>
    </button>

  </div>

</section>

          {/* ================================================= */}
          {/* ERROR */}
          {/* ================================================= */}

          {error && (
            <div className="mb-6 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">

              <AlertCircle
                size={19}
                className="mt-0.5 shrink-0"
              />

              <span>{error}</span>

            </div>
          )}

          {/* ================================================= */}
          {/* SUCCESS */}
          {/* ================================================= */}

          {success && (
            <div className="mb-6 flex items-start gap-3 rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">

              <CheckCircle2
                size={19}
                className="mt-0.5 shrink-0"
              />

              <span>{success}</span>

            </div>
          )}

{activeAllocationTab === "hall" && (
  <>
    {/* ================================================= */}
    {/* EXAMINATION SELECTOR */}
    {/* ================================================= */}

    <section className="mb-6 rounded-2xl border border-border bg-surface p-5 shadow-sm md:p-6">

            <div className="grid gap-5 lg:grid-cols-[1fr_auto] lg:items-end">

              <div>
                <label
                  htmlFor="examination"
                  className="mb-2 block text-sm font-semibold text-sidebar"
                >
                  Select Examination
                </label>

                <select
                  id="examination"
                  value={selectedExamination}
                  onChange={(event) =>
                    setSelectedExamination(
                      event.target.value
                    )
                  }
                  disabled={loading}
                  className="w-full rounded-xl border border-border bg-surface px-4 py-3.5 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
                >
                  <option value="">
                    {loading
                      ? "Loading examinations..."
                      : "Select an examination"}
                  </option>

                  {examinations.map(
                    (examination) => (
                      <option
                        key={examination.id}
                        value={examination.id}
                      >
                        {`Examination #${examination.id}`}{" "}
— {examination.name}
                      </option>
                    )
                  )}
                </select>
              </div>

              <button
                type="button"
                onClick={handleGenerateAllocation}
                disabled={
                  !selectedExamination ||
                  generating ||
                  loadingAllocations
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

                    Generate Allocation
                  </>
                )}
              </button>

            </div>

            {/* Selected examination information */}

            {selectedExam && (
              <div className="mt-5 grid gap-3 border-t border-border pt-5 sm:grid-cols-2 lg:grid-cols-4">

                <InfoItem
                  label="Exam ID"
                  value={`#${selectedExam.id}`}
                />

              <InfoItem
  label="Examination"
  value={selectedExam.name}
/>

<InfoItem
  label="Course"
  value={selectedExam.course_name || "—"}
/>

<InfoItem
  label="Semester"
  value={selectedExam.semester}
/>

              </div>
            )}

          </section>

          {/* ================================================= */}
          {/* NATURAL-LANGUAGE REQUIREMENT UNDERSTANDING */}
          {/* ================================================= */}

          <section className="mb-6">
            <RequirementUnderstanding />
          </section>

          {/* ================================================= */}
          {/* BULK HALL ALLOCATION */}
          {/* ================================================= */}

          <section className="mb-6 rounded-2xl border border-border bg-surface p-5 shadow-sm md:p-6">
            <div className="flex flex-col gap-4 border-b border-border pb-5 md:flex-row md:items-center md:justify-between">

              <div>
                <p className="text-sm font-semibold uppercase tracking-wider text-accent">
                  Bulk Allocation
                </p>

                <h2 className="mt-1 text-lg font-bold text-text">
                  Allocate Multiple Examinations
                </h2>

                <p className="mt-1 max-w-2xl text-sm leading-6 text-text-muted">
                  Select multiple examinations to generate
                  hall allocations together. Halls can be
                  reused when examination timetable slots
                  do not overlap.
                </p>
              </div>

              <button
                type="button"
                onClick={
                  handleSelectAllBulkExaminations
                }
                disabled={
                  loading ||
                  examinations.length === 0 ||
                  bulkGenerating
                }
                className="w-fit rounded-xl border border-border px-4 py-2.5 text-sm font-semibold text-sidebar transition hover:border-accent hover:bg-surface-muted disabled:cursor-not-allowed disabled:opacity-50"
              >
                {selectedBulkExaminations.length ===
                examinations.length
                  ? "Clear All"
                  : "Select All"}
              </button>

            </div>

            {loading ? (
              <div className="flex items-center justify-center py-10">

                <RefreshCw
                  size={24}
                  className="animate-spin text-accent"
                />

                <span className="ml-3 text-sm text-text-muted">
                  Loading examinations...
                </span>

              </div>
            ) : examinations.length === 0 ? (
              <div className="py-10 text-center">

                <ClipboardList
                  size={28}
                  className="mx-auto text-text-muted"
                />

                <p className="mt-3 text-sm font-semibold text-text">
                  No examinations available
                </p>

                <p className="mt-1 text-sm text-text-muted">
                  Create an examination before generating
                  bulk hall allocation.
                </p>

              </div>
            ) : (
              <>

                <div className="mt-5 grid gap-3 md:grid-cols-2">

                  {examinations.map(
                    (examination) => {
                      const examinationId =
                        String(
                          examination.id
                        );

                      const isSelected =
                        selectedBulkExaminations.includes(
                          examinationId
                        );

                      return (
                        <label
                          key={examination.id}
                          className={`flex cursor-pointer items-start gap-3 rounded-xl border p-4 transition ${
                            isSelected
                              ? "border-primary bg-accent-light"
                              : "border-border hover:border-accent hover:bg-surface-muted"
                          }`}
                        >

                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() =>
                              handleBulkExaminationChange(
                                examinationId
                              )
                            }
                            disabled={
                              bulkGenerating
                            }
                            className="mt-1 h-4 w-4 accent-primary"
                          />

                          <div className="min-w-0">

                            <p className="text-sm font-semibold text-text">
                              {`Examination #${examination.id}`}
                            </p>

                            <p className="mt-1 truncate text-sm text-text-muted">
                              {examination.name}
                            </p>

                            <div className="mt-2 flex flex-wrap gap-2">

                              <span className="rounded-full bg-surface-muted px-2.5 py-1 text-xs font-medium text-text-muted">
                                {examination.course_name ||
                                  "Course —"}
                              </span>

                              <span className="rounded-full bg-surface-muted px-2.5 py-1 text-xs font-medium text-text-muted">
                                Semester{" "}
                                {examination.semester ??
                                  "—"}
                              </span>

                              <span className="rounded-full bg-surface-muted px-2.5 py-1 text-xs font-medium text-text-muted">
                                {examination.status ||
                                  "—"}
                              </span>

                            </div>

                          </div>

                        </label>
                      );
                    }
                  )}

                </div>

                <div className="mt-5 flex flex-col gap-4 rounded-xl bg-surface-muted p-4 sm:flex-row sm:items-center sm:justify-between">

                  <div>
                    <p className="text-sm font-semibold text-text">
                      {selectedBulkExaminations.length}{" "}
                      examination
                      {selectedBulkExaminations.length !==
                      1
                        ? "s"
                        : ""}{" "}
                      selected
                    </p>

                    <p className="mt-1 text-xs text-text-muted">
                      Only examinations with valid timetable
                      entries and eligible students can be
                      allocated.
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={
                      handleGenerateBulkAllocation
                    }
                    disabled={
                      selectedBulkExaminations.length ===
                        0 ||
                      bulkGenerating
                    }
                    className="flex items-center justify-center gap-2 rounded-xl bg-sidebar px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-sidebar/10 transition hover:bg-primary disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {bulkGenerating ? (
                      <>
                        <RefreshCw
                          size={18}
                          className="animate-spin"
                        />

                        Generating Bulk Allocation...
                      </>
                    ) : (
                      <>
                        <Sparkles size={18} />

                        Generate Bulk Allocation
                      </>
                    )}
                  </button>

                </div>

              </>
            )}

            {/* Bulk Result */}

            {bulkResult && (
              <div className="mt-5 rounded-xl border border-green-200 bg-green-50 p-4">

                <div className="flex items-start gap-3">

                  <CheckCircle2
                    size={20}
                    className="mt-0.5 shrink-0 text-success"
                  />

                  <div className="min-w-0">

                    <p className="text-sm font-bold text-green-800">
                      Bulk Allocation Completed
                    </p>

                    <p className="mt-1 text-sm text-green-700">
                      {bulkResult.message}
                    </p>

                    <div className="mt-4 grid gap-3 sm:grid-cols-3">

                      <div className="rounded-lg bg-white/70 px-3 py-2">
                        <p className="text-xs text-text-muted">
                          Examinations
                        </p>
                        <p className="mt-1 text-lg font-bold text-text">
                          {bulkResult.examinations_processed ??
                            0}
                        </p>
                      </div>

                      <div className="rounded-lg bg-white/70 px-3 py-2">
                        <p className="text-xs text-text-muted">
                          Halls Used
                        </p>
                        <p className="mt-1 text-lg font-bold text-text">
                          {bulkResult.halls_used ??
                            0}
                        </p>
                      </div>

                      <div className="rounded-lg bg-white/70 px-3 py-2">
                        <p className="text-xs text-text-muted">
                          Allocation Records
                        </p>
                        <p className="mt-1 text-lg font-bold text-text">
                          {bulkResult.allocation_records ??
                            0}
                        </p>
                      </div>

                    </div>

                  </div>

                </div>

              </div>
            )}

          </section>

                   {/* ================================================= */}
          {/* BULK SEAT / INVIGILATOR / VALIDATE */}
          {/* ================================================= */}

          <section className="mb-6 grid gap-5 lg:grid-cols-3">

            {/* BULK SEAT */}

            <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm md:p-6">

              <h3 className="text-sm font-bold text-text">
                Bulk Seat Allocation
              </h3>

              <p className="mt-1 text-xs text-text-muted">
                Generate seat allocation for the selected
                examinations using the existing seat engine.
              </p>

              <button
                type="button"
                onClick={handleBulkSeatGeneration}
                disabled={
                  selectedBulkExaminations.length === 0 ||
                  bulkSeatGenerating
                }
                className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-sidebar px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-primary disabled:cursor-not-allowed disabled:opacity-60"
              >
                {bulkSeatGenerating ? (
                  <>
                    <RefreshCw size={16} className="animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles size={16} />
                    Generate Seats
                  </>
                )}
              </button>

              {bulkSeatResult && (
                <BulkResultList result={bulkSeatResult} />
              )}

            </div>

            {/* BULK INVIGILATOR */}

            <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm md:p-6">

              <h3 className="text-sm font-bold text-text">
                Bulk Invigilator Allocation
              </h3>

              <p className="mt-1 text-xs text-text-muted">
                Deterministic invigilator allocation across
                selected examinations.
              </p>

              <button
                type="button"
                onClick={handleBulkInvigilatorGeneration}
                disabled={
                  selectedBulkExaminations.length === 0 ||
                  bulkInvigGenerating
                }
                className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-sidebar px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-primary disabled:cursor-not-allowed disabled:opacity-60"
              >
                {bulkInvigGenerating ? (
                  <>
                    <RefreshCw size={16} className="animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Users size={16} />
                    Generate Invigilators
                  </>
                )}
              </button>

              {bulkInvigResult && (
                <BulkResultList result={bulkInvigResult} />
              )}

            </div>

            {/* BULK VALIDATE */}

            <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm md:p-6">

              <h3 className="text-sm font-bold text-text">
                Bulk Validation
              </h3>

              <p className="mt-1 text-xs text-text-muted">
                Read-only validation of selected examinations.
              </p>

              <button
                type="button"
                onClick={handleBulkValidation}
                disabled={
                  selectedBulkExaminations.length === 0 ||
                  bulkValidating
                }
                className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl border border-border bg-surface px-4 py-2.5 text-sm font-semibold text-sidebar transition hover:border-accent hover:bg-surface-muted disabled:cursor-not-allowed disabled:opacity-60"
              >
                {bulkValidating ? (
                  <>
                    <RefreshCw size={16} className="animate-spin" />
                    Validating...
                  </>
                ) : (
                  <>
                    <CheckCircle2 size={16} />
                    Validate Selected
                  </>
                )}
              </button>

              {bulkValidationResult && (
                <BulkValidationList
                  result={bulkValidationResult}
                />
              )}

            </div>

          </section>

          {/* ================================================= */}
          {/* SUMMARY */}
          {/* ================================================= */}
          {selectedExamination && (
            <section className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">

             <SummaryCard
  title="Eligible Students"
  value={
    loadingAllocations
      ? "..."
      : summary?.eligible_students ?? 0
  }
  description="Students requiring examination capacity"
  icon={Users}
/>

<SummaryCard
  title="Halls Used"
  value={
    loadingAllocations
      ? "..."
      : summary?.halls_used ?? 0
  }
  description="Examination halls reserved"
  icon={Building2}
/>

<SummaryCard
  title="Allocated Capacity"
  value={
    loadingAllocations
      ? "..."
      : summary?.allocated_capacity ?? 0
  }
  description="Total hall capacity reserved"
  icon={Armchair}
/>

              <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">

                <div className="flex items-start justify-between">

                  <div>
                    <p className="text-sm font-medium text-text-muted">
                      Allocation Status
                    </p>

                    <p
                      className={`mt-2 text-2xl font-bold ${isValid
                          ? "text-success"
                          : "text-warning"
                        }`}
                    >
                      {allocationStatus}
                    </p>
                  </div>

                  <div
                    className={`flex h-11 w-11 items-center justify-center rounded-xl ${isValid
                        ? "bg-green-50 text-success"
                        : "bg-yellow-50 text-warning"
                      }`}
                  >
                    {isValid ? (
                      <CheckCircle2 size={21} />
                    ) : (
                      <AlertCircle size={21} />
                    )}
                  </div>

                </div>

                <p className="mt-4 text-xs text-text-muted">
                  Allocation validation result
                </p>

              </div>

            </section>
          )}

          {/* ================================================= */}
          {/* ALLOCATION TABLE */}
          {/* ================================================= */}

          {selectedExamination && (
            <section className="rounded-2xl border border-border bg-surface shadow-sm">

              <div className="flex flex-col gap-4 border-b border-border p-5 md:flex-row md:items-center md:justify-between md:p-6">

                <div>
                  <h2 className="font-bold text-text">
  Hall Allocation Records
</h2>

<p className="mt-1 text-sm text-text-muted">
  Examination halls reserved for each timetable slot.
</p>
                </div>

                <button
                  type="button"
                  onClick={() =>
                    setShowDetails(true)
                  }
                  disabled={!allocations.length}
                  className="flex w-fit items-center gap-2 rounded-xl border border-border px-4 py-2.5 text-sm font-semibold text-sidebar transition hover:border-accent hover:bg-surface-muted disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <Eye size={17} />

                  View Details
                </button>

              </div>

              {loadingAllocations ? (
                <div className="flex items-center justify-center px-5 py-16">

                  <div className="text-center">

                    <RefreshCw
                      size={28}
                      className="mx-auto animate-spin text-accent"
                    />

                    <p className="mt-3 text-sm text-text-muted">
                      Loading allocation records...
                    </p>

                  </div>

                </div>
              ) : allocations.length === 0 ? (
                <EmptyState />
              ) : (
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
        Hall
      </th>

      <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
        Building
      </th>

      <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
        Floor
      </th>

      <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
        Capacity
      </th>

      <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
        Purpose
      </th>

            <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
        Status
      </th>

      <th className="px-5 py-4 text-right text-xs font-semibold uppercase tracking-wider text-text-muted">
        Actions
      </th>

    </tr>
  </thead>

  <tbody>

    {allocations
      .slice(0, 10)
      .map((allocation) => (
        <tr
          key={allocation.id}
          className="border-b border-border last:border-0 hover:bg-surface-muted"
        >

          <td className="px-5 py-4 text-sm text-text">
            {allocation.exam_date || "—"}
          </td>

          <td className="px-5 py-4 text-sm font-semibold text-sidebar">
            {allocation.session || "—"}
          </td>

          <td className="px-5 py-4 text-sm font-semibold text-text">
            {allocation.hall || "—"}
          </td>

          <td className="px-5 py-4 text-sm text-text">
            {allocation.building_name || "—"}
          </td>

          <td className="px-5 py-4 text-sm text-text">
            {allocation.floor_no ?? "—"}
          </td>

          <td className="px-5 py-4 text-sm font-semibold text-primary">
            {allocation.allocated_capacity ?? 0}
          </td>

          <td className="px-5 py-4">
            <span className="inline-flex rounded-full bg-accent-light px-3 py-1 text-xs font-semibold text-primary">
              {allocation.purpose || "NORMAL"}
            </span>
          </td>

                   <td className="px-5 py-4">

            <span className="inline-flex rounded-full bg-green-50 px-3 py-1 text-xs font-semibold text-success">
              {allocation.status}
            </span>

          </td>

          <td className="px-5 py-4">

            <div className="flex items-center justify-end gap-2">

              <button
                type="button"
                onClick={() =>
                  setEditingAllocation(allocation)
                }
                className="
                  rounded-lg
                  p-2
                  text-text-muted
                  transition
                  hover:bg-accent-light
                  hover:text-primary
                "
                title="Edit allocation"
              >
                <Pencil size={17} />
              </button>

            </div>

          </td>

        </tr>
      ))}

  </tbody>
</table>
                  {allocations.length > 10 && (
                    <div className="border-t border-border px-5 py-4 text-center text-sm text-text-muted">
                      Showing first 10 of{" "}
{allocations.length} hall allocation records.
Use View Details to see all records.
                    </div>
                  )}

                </div>
              )}

            </section>
          )}

{/* ================================================= */}
{/* FEATURE 21 — WHAT-IF / DYNAMIC REALLOCATION */}
{/* ================================================= */}

{selectedExamination && (
  <section className="mb-6">
    <WhatIfReallocation
      examinationId={selectedExamination}
      onApplied={() =>
        loadAllocationData(selectedExamination)
      }
    />
  </section>
)}

          {!selectedExamination && (
            <div className="rounded-2xl border border-dashed border-border bg-surface p-12 text-center">

              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-accent-light text-primary">
                <ClipboardList size={27} />
              </div>

              <h3 className="mt-5 text-lg font-bold text-text">
                Select an examination
              </h3>

             <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-text-muted">
  Select an examination above to view
  existing hall allocations or generate a
  new examination hall allocation.
</p>

            </div>
          )}

  </>
)}
{activeAllocationTab === "invigilator" && (
  <InvigilatorPanel
    examinations={examinations}
    onMessage={(message, type) => {
      if (type === "error") {
        setError(message);
        setSuccess("");
      } else {
        setSuccess(message);
        setError("");
      }
    }}
  />
)}

{activeAllocationTab === "seat" && (
  <SeatAllocationPanel
    examinations={examinations}
    onMessage={(message, type) => {
      if (type === "error") {
        setError(message);
        setSuccess("");
      } else {
        setSuccess(message);
        setError("");
      }
    }}
  />
)}

{activeAllocationTab === "approval" && (
  <ApprovalPanel
    examinations={examinations}
    onMessage={(message, type) => {
      if (type === "error") {
        setError(message);
        setSuccess("");
      } else {
        setSuccess(message);
        setError("");
      }
    }}
  />
)}

{/* ================================================= */}
{/* DETAILS MODAL */}
{/* ================================================= */}
               {showDetails && (
          <AllocationDetails
            examination={selectedExam}
            allocations={allocations}
            onClose={() => setShowDetails(false)}
          />
        )}

        {editingAllocation && (
          <AllocationForm
            allocation={editingAllocation}
            onClose={() =>
              setEditingAllocation(null)
            }
            onSuccess={handleEditSuccess}
          />
        )}

      </main>
      </main>
    </div>
  );
}

/* ================================================= */
/* SUMMARY CARD */
/* ================================================= */

function SummaryCard({
  title,
  value,
  description,
  icon: Icon,
}) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">

      <div className="flex items-start justify-between">

        <div>
          <p className="text-sm font-medium text-text-muted">
            {title}
          </p>

          <p className="mt-2 text-3xl font-bold text-text">
            {value}
          </p>
        </div>

        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-light text-primary">
          <Icon size={21} />
        </div>

      </div>

      <p className="mt-4 text-xs text-text-muted">
        {description}
      </p>

    </div>
  );
}

/* ================================================= */
/* INFO ITEM */
/* ================================================= */

function InfoItem({ label, value }) {
  return (
    <div className="rounded-xl bg-surface-muted px-4 py-3">

      <p className="text-xs font-medium text-text-light">
        {label}
      </p>

      <p className="mt-1 text-sm font-semibold text-text">
        {value}
      </p>

    </div>
  );
}
{/* 
{activeAllocationTab === "invigilator" && (
  <ComingSoonPanel
    icon={Users}
    title="Invigilator Allocation"
    description="Assign invigilators to examination halls while managing staff availability and workload."
    label="Coming Next"
  />
)}

{activeAllocationTab === "seat" && (
  <ComingSoonPanel
    icon={Armchair}
    title="Student / Seat Allocation"
    description="Assign eligible students to examination halls and seats after hall allocation is completed."
    label="Coming Later"
  />
)} */}

/* ================================================= */
/* EMPTY STATE */
/* ================================================= */

function EmptyState() {
  return (
    <div className="px-5 py-14 text-center">

      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-accent-light text-primary">
        <ClipboardList size={27} />
      </div>

      <h3 className="mt-5 font-bold text-text">
  No hall allocations found
</h3>

<p className="mx-auto mt-2 max-w-md text-sm text-text-muted">
  No examination halls have been allocated
  for this examination yet.
</p>

    </div>
  );
}
function ComingSoonPanel({
  icon: Icon,
  title,
  description,
  label,
}) {
  return (
    <section className="rounded-2xl border border-dashed border-border bg-surface p-12 text-center">

      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-surface-muted text-text-muted">
        <Icon size={27} />
      </div>

      <span className="mt-5 inline-flex rounded-full bg-surface-muted px-3 py-1 text-xs font-semibold text-text-muted">
        {label}
      </span>

      <h3 className="mt-4 text-lg font-bold text-text">
        {title}
      </h3>

      <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-text-muted">
        {description}
      </p>

    </section>
  );
}

function BulkResultList({ result }) {
  return (
    <div className="mt-4 space-y-2">
      {result.results.map((row) => (
        <div
          key={row.examination_id}
          className={`rounded-lg border px-3 py-2 text-xs ${
            row.status === "GENERATED"
              ? "border-green-200 bg-green-50 text-green-700"
              : "border-red-200 bg-red-50 text-red-700"
          }`}
        >
          <p className="font-semibold">
            Examination #{row.examination_id} — {row.status}
          </p>
          {row.status === "GENERATED" ? (
            <p className="mt-0.5">
              {row.seat_records !== undefined
                ? `${row.seat_records} seats`
                : ""}
              {row.invigilator_assignments !== undefined
                ? `${row.invigilator_assignments} assignments / ${row.distinct_staff_used} staff`
                : ""}
            </p>
          ) : (
            <p className="mt-0.5">{row.message}</p>
          )}
        </div>
      ))}
    </div>
  );
}


function BulkValidationList({ result }) {
  return (
    <div className="mt-4 space-y-2">
      {result.results.map((row) => (
        <div
          key={row.examination_id}
          className={`rounded-lg border px-3 py-2 text-xs ${
            row.status === "VALID"
              ? "border-green-200 bg-green-50 text-green-700"
              : row.status === "NOT GENERATED"
              ? "border-yellow-200 bg-yellow-50 text-yellow-800"
              : "border-red-200 bg-red-50 text-red-700"
          }`}
        >
          <p className="font-semibold">
            Examination #{row.examination_id} — {row.status}
          </p>
          <p className="mt-0.5">
            Hall: {row.hall_status} • Invigilator: {row.invigilator_status}
          </p>
        </div>
      ))}
    </div>
  );
}

export default Allocations;