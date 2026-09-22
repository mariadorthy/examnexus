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
} from "lucide-react";

import AllocationDetails from "./AllocationDetails";
import {
  get,
  post,
} from "../../../services/api";
import AdminSidebar from "../../../components/AdminSidebar";
import AdminTopbar from "../../../components/AdminTopbar";
function Allocations({
  user,
  onLogout,
  onNavigate,
}) {
  const [sidebarOpen, setSidebarOpen] =
    useState(false);
  const [examinations, setExaminations] = useState([]);
  const [selectedExamination, setSelectedExamination] = useState("");

  const [summary, setSummary] = useState(null);
  const [allocations, setAllocations] = useState([]);

  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [loadingAllocations, setLoadingAllocations] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [showDetails, setShowDetails] = useState(false);

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
      "Generate examination hall allocation for this examination?"
    );

    if (!confirmed) {
      return;
    }

    try {
      setGenerating(true);
      setError("");
      setSuccess("");

      const data = await post(
        `/allocations/generate/${selectedExamination}`,
        {}
      );

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

      await loadAllocationData(selectedExamination);
    } catch (err) {
      console.error("Generate allocation error:", err);

      setError(
        err.message ||
        "Unable to generate allocation."
      );
    } finally {
      setGenerating(false);
    }
  };

  const handleRefresh = async () => {
    if (!selectedExamination) {
      await loadExaminations();
      return;
    }

    await loadAllocationData(selectedExamination);
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
                  Generate, validate and review student
                  hall and seat allocations for scheduled
                  examinations.
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
                        {examination.subject_id
                          ? `Subject #${examination.subject_id}`
                          : `Examination #${examination.id}`}{" "}
                        — {examination.exam_date} —{" "}
                        {examination.session}
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
                  label="Date"
                  value={selectedExam.exam_date}
                />

                <InfoItem
                  label="Session"
                  value={selectedExam.session}
                />

                <InfoItem
                  label="Time"
                  value={`${selectedExam.start_time} - ${selectedExam.end_time}`}
                />

              </div>
            )}

          </section>

          {/* ================================================= */}
          {/* SUMMARY */}
          {/* ================================================= */}

          {selectedExamination && (
            <section className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">

              <SummaryCard
                title="Allocated Students"
                value={
                  loadingAllocations
                    ? "..."
                    : summary?.allocated_students ?? 0
                }
                description="Students with assigned seats"
                icon={Users}
              />

              <SummaryCard
                title="Halls Used"
                value={
                  loadingAllocations
                    ? "..."
                    : summary?.halls_used ?? 0
                }
                description="Examination halls in use"
                icon={Building2}
              />

              <SummaryCard
                title="Unallocated"
                value={
                  loadingAllocations
                    ? "..."
                    : summary?.unallocated_students ?? 0
                }
                description="Students without allocation"
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
                    Allocation Records
                  </h2>

                  <p className="mt-1 text-sm text-text-muted">
                    Student hall and seat assignments.
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

                  <table className="w-full min-w-[700px]">

                    <thead>
                      <tr className="border-b border-border bg-surface-muted">

                        <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                          Student ID
                        </th>

                        <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                          Student Name
                        </th>

                        <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                          Hall
                        </th>

                        <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                          Seat
                        </th>

                        <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                          Status
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

                            <td className="px-5 py-4 text-sm font-semibold text-sidebar">
                              {allocation.student_id}
                            </td>

                            <td className="px-5 py-4 text-sm text-text">
                              {allocation.student_name}
                            </td>

                            <td className="px-5 py-4 text-sm text-text">
                              {allocation.hall}
                            </td>

                            <td className="px-5 py-4 text-sm font-semibold text-primary">
                              {allocation.seat_number || "—"}
                            </td>

                            <td className="px-5 py-4">

                              <span className="inline-flex rounded-full bg-green-50 px-3 py-1 text-xs font-semibold text-success">
                                {allocation.status}
                              </span>

                            </td>

                          </tr>
                        ))}

                    </tbody>

                  </table>

                  {allocations.length > 10 && (
                    <div className="border-t border-border px-5 py-4 text-center text-sm text-text-muted">
                      Showing first 10 of{" "}
                      {allocations.length} allocations.
                      Use View Details to see all records.
                    </div>
                  )}

                </div>
              )}

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
                existing allocations or generate a new
                hall and seat allocation.
              </p>

            </div>
          )}

        </main>

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
        No allocations found
      </h3>

      <p className="mx-auto mt-2 max-w-md text-sm text-text-muted">
        No student allocations have been generated
        for this examination yet.
      </p>

    </div>
  );
}

export default Allocations;
