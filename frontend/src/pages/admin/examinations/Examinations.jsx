import { useEffect, useState } from "react";
import {
  CalendarDays,
  Clock3,
  Plus,
  RefreshCw,
  Search,
  Edit3,
  Trash2,
  X,
} from "lucide-react";

import ExaminationForm from "./ExaminationForm";
import { get } from "../../services/api";

function Examinations() {
  const [examinations, setExaminations] = useState([]);
  const [subjects, setSubjects] = useState([]);

  const [loading, setLoading] = useState(true);
  const [subjectsLoading, setSubjectsLoading] = useState(true);

  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [editingExamination, setEditingExamination] = useState(null);

  useEffect(() => {
    loadExaminations();
    loadSubjects();
  }, []);

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

  const loadSubjects = async () => {
    try {
      setSubjectsLoading(true);

      const data = await get("/subjects/");

setSubjects(data);
    } catch (err) {
      console.error("Subjects error:", err);
    } finally {
      setSubjectsLoading(false);
    }
  };

  const getSubjectName = (subjectId) => {
    const subject = subjects.find(
      (item) => item.id === subjectId
    );

    if (!subject) {
      return `Subject #${subjectId}`;
    }

    return `${subject.subject_code} — ${subject.subject_name}`;
  };

  const handleCreate = () => {
    setEditingExamination(null);
    setShowForm(true);
  };

  const handleEdit = (examination) => {
    setEditingExamination(examination);
    setShowForm(true);
  };

  const handleFormSuccess = () => {
    setShowForm(false);
    setEditingExamination(null);
    loadExaminations();
  };

  const handleCloseForm = () => {
    setShowForm(false);
    setEditingExamination(null);
  };

  const handleDelete = async (id) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this examination?"
    );

    if (!confirmed) {
      return;
    }

    /*
     * NOTE:
     * Your current backend does not yet have
     * a DELETE /api/examinations/<id> route.
     *
     * This is intentionally left disabled until
     * the backend DELETE route is added.
     */

    alert(
      "Delete functionality will be enabled after the backend DELETE route is added."
    );
  };

  const filteredExaminations = examinations.filter(
    (examination) => {
      const subjectName = getSubjectName(
        examination.subject_id
      );

      const searchableText = `
        ${subjectName}
        ${examination.session}
        ${examination.exam_type}
        ${examination.status}
        ${examination.exam_date}
      `.toLowerCase();

      return searchableText.includes(
        search.toLowerCase()
      );
    }
  );

  const formatDate = (date) => {
    if (!date) {
      return "—";
    }

    return new Date(`${date}T00:00:00`).toLocaleDateString(
      "en-IN",
      {
        day: "2-digit",
        month: "short",
        year: "numeric",
      }
    );
  };

  const getStatusClasses = (status) => {
    switch (status) {
      case "SCHEDULED":
        return "bg-accent-light text-primary";

      case "COMPLETED":
        return "bg-green-100 text-green-700";

      case "CANCELLED":
        return "bg-red-100 text-red-700";

      case "ONGOING":
        return "bg-yellow-100 text-yellow-700";

      default:
        return "bg-gray-100 text-gray-600";
    }
  };

  return (
    <div className="min-h-screen bg-background">

      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <div className="mb-8 flex flex-col gap-5 md:flex-row md:items-center md:justify-between">

        <div>
          <p className="text-sm font-medium text-accent">
            Examination Management
          </p>

          <h1 className="mt-1 text-2xl font-bold text-text md:text-3xl">
            Examinations
          </h1>

          <p className="mt-2 text-sm text-text-muted">
            Create and manage examination schedules.
          </p>
        </div>

        <div className="flex gap-3">

          <button
            type="button"
            onClick={loadExaminations}
            disabled={loading}
            className="flex items-center justify-center gap-2 rounded-xl border border-border bg-surface px-4 py-3 text-sm font-semibold text-sidebar transition hover:border-accent hover:bg-surface-muted disabled:opacity-50"
          >
            <RefreshCw
              size={17}
              className={loading ? "animate-spin" : ""}
            />

            Refresh
          </button>

          <button
            type="button"
            onClick={handleCreate}
            className="flex items-center justify-center gap-2 rounded-xl bg-sidebar px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-sidebar/10 transition hover:bg-primary"
          >
            <Plus size={18} />

            Create Examination
          </button>

        </div>

      </div>

      {/* ================================================= */}
      {/* ERROR */}
      {/* ================================================= */}

      {error && (
        <div className="mb-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* ================================================= */}
      {/* SEARCH */}
      {/* ================================================= */}

      <div className="mb-6 rounded-2xl border border-border bg-surface p-4 shadow-sm">

        <div className="relative max-w-xl">

          <Search
            size={18}
            className="absolute left-4 top-1/2 -translate-y-1/2 text-text-light"
          />

          <input
            type="text"
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
            placeholder="Search examinations..."
            className="w-full rounded-xl border border-border bg-background py-3 pl-11 pr-4 text-sm text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
          />

        </div>

      </div>

      {/* ================================================= */}
      {/* STATISTICS */}
      {/* ================================================= */}

      <div className="mb-6 grid gap-4 sm:grid-cols-3">

        <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">

          <div className="flex items-center gap-3">

            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-light text-primary">
              <CalendarDays size={21} />
            </div>

            <div>
              <p className="text-xs font-medium text-text-muted">
                Total Examinations
              </p>

              <p className="mt-1 text-2xl font-bold text-text">
                {loading ? "..." : examinations.length}
              </p>
            </div>

          </div>

        </div>

        <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">

          <div className="flex items-center gap-3">

            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-light text-primary">
              <Clock3 size={21} />
            </div>

            <div>
              <p className="text-xs font-medium text-text-muted">
                Scheduled
              </p>

              <p className="mt-1 text-2xl font-bold text-text">
                {loading
                  ? "..."
                  : examinations.filter(
                      (item) =>
                        item.status === "SCHEDULED"
                    ).length}
              </p>
            </div>

          </div>

        </div>

        <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">

          <div className="flex items-center gap-3">

            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-light text-primary">
              <CalendarDays size={21} />
            </div>

            <div>
              <p className="text-xs font-medium text-text-muted">
                Showing
              </p>

              <p className="mt-1 text-2xl font-bold text-text">
                {loading
                  ? "..."
                  : filteredExaminations.length}
              </p>
            </div>

          </div>

        </div>

      </div>

      {/* ================================================= */}
      {/* TABLE */}
      {/* ================================================= */}

      <div className="overflow-hidden rounded-2xl border border-border bg-surface shadow-sm">

        <div className="overflow-x-auto">

          <table className="w-full min-w-[950px]">

            <thead>
              <tr className="border-b border-border bg-surface-muted">

                <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                  Subject
                </th>

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
                  Duration
                </th>

                <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                  Type
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

              {loading ? (
                <tr>
                  <td
                    colSpan="8"
                    className="px-5 py-12 text-center text-sm text-text-muted"
                  >
                    Loading examinations...
                  </td>
                </tr>
              ) : filteredExaminations.length === 0 ? (
                <tr>
                  <td
                    colSpan="8"
                    className="px-5 py-12 text-center"
                  >
                    <CalendarDays
                      size={32}
                      className="mx-auto text-text-light"
                    />

                    <p className="mt-3 font-semibold text-text">
                      No examinations found
                    </p>

                    <p className="mt-1 text-sm text-text-muted">
                      Create an examination to get started.
                    </p>
                  </td>
                </tr>
              ) : (
                filteredExaminations.map(
                  (examination) => (
                    <tr
                      key={examination.id}
                      className="border-b border-border last:border-0 hover:bg-surface-muted"
                    >

                      <td className="px-5 py-4">

                        <p className="font-semibold text-text">
                          {getSubjectName(
                            examination.subject_id
                          )}
                        </p>

                        <p className="mt-1 text-xs text-text-muted">
                          Examination #{examination.id}
                        </p>

                      </td>

                      <td className="px-5 py-4 text-sm text-text">
                        {formatDate(
                          examination.exam_date
                        )}
                      </td>

                      <td className="px-5 py-4 text-sm text-text">
                        {examination.session}
                      </td>

                      <td className="px-5 py-4 text-sm text-text">
                        {examination.start_time} —{" "}
                        {examination.end_time}
                      </td>

                      <td className="px-5 py-4 text-sm text-text">
                        {examination.duration_minutes} min
                      </td>

                      <td className="px-5 py-4 text-sm text-text">
                        {examination.exam_type}
                      </td>

                      <td className="px-5 py-4">

                        <span
                          className={`rounded-full px-3 py-1 text-xs font-semibold ${getStatusClasses(
                            examination.status
                          )}`}
                        >
                          {examination.status}
                        </span>

                      </td>

                      <td className="px-5 py-4">

                        <div className="flex justify-end gap-2">

                          <button
                            type="button"
                            onClick={() =>
                              handleEdit(
                                examination
                              )
                            }
                            className="rounded-lg p-2 text-primary transition hover:bg-accent-light"
                            title="Edit examination"
                          >
                            <Edit3 size={17} />
                          </button>

                          <button
                            type="button"
                            onClick={() =>
                              handleDelete(
                                examination.id
                              )
                            }
                            className="rounded-lg p-2 text-danger transition hover:bg-red-50"
                            title="Delete examination"
                          >
                            <Trash2 size={17} />
                          </button>

                        </div>

                      </td>

                    </tr>
                  )
                )
              )}

            </tbody>

          </table>

        </div>

      </div>

      {/* ================================================= */}
      {/* FORM MODAL */}
      {/* ================================================= */}

      {showForm && (
        <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/40 px-4 py-8 backdrop-blur-sm">

          <div className="w-full max-w-2xl rounded-2xl bg-surface shadow-2xl">

            <div className="flex items-center justify-between border-b border-border px-6 py-5">

              <div>
                <h2 className="text-xl font-bold text-text">
                  {editingExamination
                    ? "Edit Examination"
                    : "Create Examination"}
                </h2>

                <p className="mt-1 text-sm text-text-muted">
                  {editingExamination
                    ? "Update examination details."
                    : "Schedule a new examination."}
                </p>
              </div>

              <button
                type="button"
                onClick={handleCloseForm}
                className="rounded-lg p-2 text-text-muted hover:bg-surface-muted hover:text-text"
              >
                <X size={20} />
              </button>

            </div>

            <div className="p-6">

              <ExaminationForm
                examination={editingExamination}
                subjects={subjects}
                subjectsLoading={subjectsLoading}
                onSuccess={handleFormSuccess}
                onCancel={handleCloseForm}
              />

            </div>

          </div>

        </div>
      )}

    </div>
  );
}

export default Examinations;
