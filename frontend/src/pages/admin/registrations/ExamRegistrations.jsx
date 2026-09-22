import { useEffect, useState } from "react";
import {
  ClipboardList,
  RefreshCw,
  Search,
  Users,
} from "lucide-react";


import { get } from "../../../services/api";
import AdminSidebar from "../../../components/AdminSidebar";
import AdminTopbar from "../../../components/AdminTopbar";

function ExamRegistrations({
  user,
  onLogout,
  onNavigate,
}) {
  const [sidebarOpen, setSidebarOpen] =
    useState(false);
  const [registrations, setRegistrations] =
    useState([]);

  const [students, setStudents] = useState([]);
  const [examinations, setExaminations] =
    useState([]);

  const [loading, setLoading] = useState(true);
  const [supportDataLoading, setSupportDataLoading] =
    useState(true);

  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    await Promise.all([
      loadRegistrations(),
      loadStudents(),
      loadExaminations(),
    ]);
  };

  const loadRegistrations = async () => {
    try {
      setLoading(true);
      setError("");

     const data = await get(
  "/exam-registrations/"
);

setRegistrations(data);
    } catch (err) {
      console.error(
        "Exam registrations error:",
        err
      );

      setError(
        "Unable to load exam registrations. Please make sure the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  const loadStudents = async () => {
    try {
      const data = await get("/students/");

setStudents(data);
    } catch (err) {
      console.error("Students error:", err);
    } finally {
      setSupportDataLoading(false);
    }
  };

  const loadExaminations = async () => {
    try {
      const data = await get(
  "/examinations/"
);

setExaminations(data);
    } catch (err) {
      console.error("Examinations error:", err);
    } finally {
      setSupportDataLoading(false);
    }
  };

  const getStudent = (studentId) => {
    return students.find(
      (student) => student.id === studentId
    );
  };

  const getExamination = (examinationId) => {
    return examinations.find(
      (examination) =>
        examination.id === examinationId
    );
  };

  const getStudentName = (studentId) => {
    const student = getStudent(studentId);

    return student
      ? `${student.student_id} — ${student.name}`
      : `Student #${studentId}`;
  };

  const getExaminationName = (
    examinationId
  ) => {
    const examination =
      getExamination(examinationId);

    if (!examination) {
      return `Examination #${examinationId}`;
    }

    return `Examination #${examination.id}`;
  };

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

  const formatRegisteredAt = (date) => {
    if (!date) {
      return "—";
    }

    return new Date(date).toLocaleString(
      "en-IN",
      {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }
    );
  };

  const getStatusClasses = (status) => {
    switch (status) {
      case "REGISTERED":
        return "bg-accent-light text-primary";

      case "CANCELLED":
        return "bg-red-100 text-red-700";

      case "COMPLETED":
        return "bg-green-100 text-green-700";

      default:
        return "bg-gray-100 text-gray-600";
    }
  };

  const filteredRegistrations =
    registrations.filter((registration) => {
      const student = getStudent(
        registration.student_id
      );

      const examination =
        getExamination(
          registration.examination_id
        );

      const searchableText = `
        ${student?.student_id || ""}
        ${student?.name || ""}
        ${student?.email || ""}
        ${examination?.exam_date || ""}
        ${examination?.session || ""}
        ${examination?.exam_type || ""}
        ${registration.status}
        ${registration.id}
      `.toLowerCase();

      return searchableText.includes(
        search.toLowerCase()
      );
    });

  const registeredCount =
    registrations.filter(
      (item) => item.status === "REGISTERED"
    ).length;

  const uniqueExaminations = new Set(
    registrations.map(
      (item) => item.examination_id
    )
  ).size;

  return (
    <div className="min-h-screen bg-background">

    <AdminSidebar
      user={user}
      onLogout={onLogout}
      sidebarOpen={sidebarOpen}
      setSidebarOpen={setSidebarOpen}
      activePage="Registrations"
      onNavigate={onNavigate}
    />

    <main className="lg:ml-72">

      <AdminTopbar
        user={user}
        title="Exam Registrations"
        section="Administration"
        onOpenSidebar={() =>
          setSidebarOpen(true)
        }
      />

      <div className="p-5 md:p-8">
      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <div className="mb-8 flex flex-col gap-5 md:flex-row md:items-center md:justify-between">

        <div>
          <p className="text-sm font-medium text-accent">
            Examination Management
          </p>

          <h1 className="mt-1 text-2xl font-bold text-text md:text-3xl">
            Exam Registrations
          </h1>

          <p className="mt-2 text-sm text-text-muted">
            View students registered for examinations.
          </p>
        </div>

        <button
          type="button"
          onClick={loadData}
          disabled={loading}
          className="flex items-center justify-center gap-2 rounded-xl border border-border bg-surface px-4 py-3 text-sm font-semibold text-sidebar transition hover:border-accent hover:bg-surface-muted disabled:opacity-50"
        >
          <RefreshCw
            size={17}
            className={
              loading ? "animate-spin" : ""
            }
          />

          Refresh
        </button>

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
      {/* STATISTICS */}
      {/* ================================================= */}

      <div className="mb-6 grid gap-4 sm:grid-cols-3">

        <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">

          <div className="flex items-center gap-3">

            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-light text-primary">
              <ClipboardList size={21} />
            </div>

            <div>
              <p className="text-xs font-medium text-text-muted">
                Total Registrations
              </p>

              <p className="mt-1 text-2xl font-bold text-text">
                {loading
                  ? "..."
                  : registrations.length}
              </p>
            </div>

          </div>

        </div>

        <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">

          <div className="flex items-center gap-3">

            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-light text-primary">
              <Users size={21} />
            </div>

            <div>
              <p className="text-xs font-medium text-text-muted">
                Active Registrations
              </p>

              <p className="mt-1 text-2xl font-bold text-text">
                {loading
                  ? "..."
                  : registeredCount}
              </p>
            </div>

          </div>

        </div>

        <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">

          <div className="flex items-center gap-3">

            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-light text-primary">
              <ClipboardList size={21} />
            </div>

            <div>
              <p className="text-xs font-medium text-text-muted">
                Examinations
              </p>

              <p className="mt-1 text-2xl font-bold text-text">
                {loading
                  ? "..."
                  : uniqueExaminations}
              </p>
            </div>

          </div>

        </div>

      </div>

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
            placeholder="Search by student, examination or status..."
            className="w-full rounded-xl border border-border bg-background py-3 pl-11 pr-4 text-sm text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
          />

        </div>

      </div>

      {/* ================================================= */}
      {/* TABLE */}
      {/* ================================================= */}

      <div className="overflow-hidden rounded-2xl border border-border bg-surface shadow-sm">

        <div className="overflow-x-auto">

          <table className="w-full min-w-[850px]">

            <thead>
              <tr className="border-b border-border bg-surface-muted">

                <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                  Student
                </th>

                <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                  Examination
                </th>

                <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                  Exam Date
                </th>

                <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                  Session
                </th>

                <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                  Status
                </th>

                <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                  Registered At
                </th>

              </tr>
            </thead>

            <tbody>

              {loading ? (
                <tr>
                  <td
                    colSpan="6"
                    className="px-5 py-12 text-center text-sm text-text-muted"
                  >
                    Loading registrations...
                  </td>
                </tr>
              ) : filteredRegistrations.length ===
                0 ? (
                <tr>
                  <td
                    colSpan="6"
                    className="px-5 py-12 text-center"
                  >
                    <ClipboardList
                      size={32}
                      className="mx-auto text-text-light"
                    />

                    <p className="mt-3 font-semibold text-text">
                      No registrations found
                    </p>

                    <p className="mt-1 text-sm text-text-muted">
                      Registered students will appear here.
                    </p>
                  </td>
                </tr>
              ) : (
                filteredRegistrations.map(
                  (registration) => {
                    const examination =
                      getExamination(
                        registration.examination_id
                      );

                    return (
                      <tr
                        key={registration.id}
                        className="border-b border-border last:border-0 hover:bg-surface-muted"
                      >

                        {/* Student */}

                        <td className="px-5 py-4">

                          <p className="font-semibold text-text">
                            {getStudentName(
                              registration.student_id
                            )}
                          </p>

                          {getStudent(
                            registration.student_id
                          )?.email && (
                            <p className="mt-1 text-xs text-text-muted">
                              {
                                getStudent(
                                  registration.student_id
                                ).email
                              }
                            </p>
                          )}

                        </td>

                        {/* Examination */}

                        <td className="px-5 py-4">

                          <p className="font-medium text-text">
                            {getExaminationName(
                              registration.examination_id
                            )}
                          </p>

                          {examination && (
                            <p className="mt-1 text-xs text-text-muted">
                              {examination.exam_type}
                            </p>
                          )}

                        </td>

                        {/* Date */}

                        <td className="px-5 py-4 text-sm text-text">
                          {formatDate(
                            examination?.exam_date
                          )}
                        </td>

                        {/* Session */}

                        <td className="px-5 py-4 text-sm text-text">
                          {examination?.session || "—"}
                        </td>

                        {/* Status */}

                        <td className="px-5 py-4">

                          <span
                            className={`rounded-full px-3 py-1 text-xs font-semibold ${getStatusClasses(
                              registration.status
                            )}`}
                          >
                            {registration.status}
                          </span>

                        </td>

                        {/* Registered */}

                        <td className="px-5 py-4 text-sm text-text-muted">
                          {formatRegisteredAt(
                            registration.registered_at
                          )}
                        </td>

                      </tr>
                    );
                  }
                )
              )}

            </tbody>

          </table>

        </div>

      </div>

      {supportDataLoading && (
        <p className="mt-4 text-xs text-text-light">
          Loading student and examination details...
        </p>
      )}
      </div>
    </main>
    </div>
  );
}

export default ExamRegistrations;
