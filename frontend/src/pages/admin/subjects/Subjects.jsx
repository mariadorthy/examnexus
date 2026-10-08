import { useEffect, useState } from "react";
import {
  Plus,
  Search,
  Pencil,
  BookOpen,
  RefreshCw,
  Power,
  Eye,
  X,
  Loader2,
} from "lucide-react";

import SubjectForm from "./SubjectForm";
import { get, patch } from "../../../services/api";
import AdminSidebar from "../../../components/AdminSidebar";
import AdminTopbar from "../../../components/AdminTopbar";
import {
  validateCsv,
  importCsv,
} from "../../../services/api";
import CsvImport from "../../../components/admin/CsvImport/CsvImport";
function Subjects({
  user,
  onLogout,
  onNavigate,
}) {
  const [sidebarOpen, setSidebarOpen] =
    useState(false);
  const [subjects, setSubjects] = useState([]);
  const [courses, setCourses] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [editingSubject, setEditingSubject] = useState(null);
  const [showCsvImport, setShowCsvImport] = useState(false);
  const [viewingSubject, setViewingSubject] =
  useState(null);

const [detailsLoading, setDetailsLoading] =
  useState(false);

const [statusLoading, setStatusLoading] = useState(null);
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError("");

      const [
        subjectsData,
        coursesData,
      ] = await Promise.all([
        get("/subjects/"),
        get("/courses/"),
      ]);

      console.log(
  "SUBJECTS GET response:",
  subjectsData
);

console.log(
  "SUBJECT STATUS VALUES:",
  subjectsData.map((subject) => ({
    id: subject.id,
    subject_code: subject.subject_code,
    is_active: subject.is_active,
  }))
);

      setSubjects(subjectsData);
      setCourses(coursesData);
    } catch (err) {
      console.error("Subjects error:", err);

      setError(
        "Unable to load subjects. Please make sure the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  const getCourseName = (courseId) => {
    const course = courses.find(
      (item) => item.id === courseId
    );

    if (!course) {
      return "—";
    }

    return `${course.course_code} - ${course.course_name}`;
  };

  const handleAdd = () => {
    setEditingSubject(null);
    setShowForm(true);
  };

  const handleEdit = (subject) => {
    setEditingSubject(subject);
    setShowForm(true);
  };

  const handleViewDetails = async (subject) => {
  try {
    setDetailsLoading(true);

    const data = await get(
      `/subjects/${subject.id}`
    );

    setViewingSubject(data);
  } catch (err) {
    console.error(
      "Subject details error:",
      err
    );

    setError(
      err.message ||
      "Unable to load subject details."
    );
  } finally {
    setDetailsLoading(false);
  }
};

  const handleStatusChange = async (subject) => {
  try {
    setStatusLoading(subject.id);

    const newStatus = !subject.is_active;

    console.log("SUBJECT CLICKED:", {
      id: subject.id,
      code: subject.subject_code,
      current: subject.is_active,
      sending: newStatus,
    });

   const response = await patch(
  `/subjects/${subject.id}/status`,
  {
    is_active: newStatus,
  }
);

console.log("SUBJECT PATCH RESPONSE:", response);

setSubjects((currentSubjects) =>
  currentSubjects.map((item) =>
    item.id === subject.id
      ? {
          ...item,
          is_active: response.is_active,
        }
      : item
  )
);
  } catch (err) {
    console.error(
      "Subject status error:",
      err
    );

    setError(
      err.message ||
        "Unable to update subject status."
    );
  } finally {
    setStatusLoading(null);
  }
};

  const handleFormSuccess = () => {
    setShowForm(false);
    setEditingSubject(null);
    loadData();
  };

  const filteredSubjects = subjects.filter(
    (subject) => {
      const searchText =
        search.trim().toLowerCase();

      if (!searchText) {
        return true;
      }

      return (
        subject.subject_code
          ?.toLowerCase()
          .includes(searchText) ||
        subject.subject_name
          ?.toLowerCase()
          .includes(searchText) ||
        subject.subject_type
          ?.toLowerCase()
          .includes(searchText) ||
        getCourseName(subject.course_id)
          .toLowerCase()
          .includes(searchText)
      );
    }
  );

  return (
    <div className="min-h-screen bg-background">

    <AdminSidebar
      user={user}
      onLogout={onLogout}
      sidebarOpen={sidebarOpen}
      setSidebarOpen={setSidebarOpen}
      activePage="Subjects"
      onNavigate={onNavigate}
    />

    <main className="lg:ml-72">

      <AdminTopbar
        user={user}
        title="Subjects"
        section="Administration"
        onOpenSidebar={() =>
          setSidebarOpen(true)
        }
      />

      <div className="p-5 md:p-8">

      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">

        <div>
          <p className="text-sm font-medium text-accent">
            Academic Management
          </p>

          <h1 className="mt-1 text-2xl font-bold text-text md:text-3xl">
            Subjects
          </h1>

          <p className="mt-2 text-sm text-text-muted">
            Manage subjects offered under each course.
          </p>
        </div>

<div className="flex flex-wrap gap-3">

  <button 
    type="button" 
    onClick={loadData} 
    disabled={loading} 
    className="flex items-center gap-2 rounded-xl border border-border bg-surface px-4 py-3 text-sm font-semibold text-sidebar transition hover:bg-surface-muted disabled:opacity-60"
  > 
    <RefreshCw 
      size={17} 
      className={loading ? "animate-spin" : ""} 
    /> 
    Refresh 
  </button>

  <button
    type="button"
    onClick={() => setShowCsvImport(true)}
    className="flex items-center gap-2 rounded-xl border border-border bg-surface px-4 py-3 text-sm font-semibold text-sidebar transition hover:bg-surface-muted"
  >
    Import CSV
  </button>

  <button 
    type="button" 
    onClick={handleAdd} 
    className="flex items-center gap-2 rounded-xl bg-sidebar px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-sidebar/10 transition hover:bg-primary"
  > 
    <Plus size={18} /> 
    Add Subject 
  </button>

</div>
      
      </div>

      {/* ================================================= */}
      {/* ERROR */}
      {/* ================================================= */}

      {error && (
        <div className="mb-6 flex items-center justify-between rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <span>{error}</span>

          <button
            type="button"
            onClick={() => setError("")}
            className="font-semibold"
          >
            ×
          </button>
        </div>
      )}

      {/* ================================================= */}
      {/* SEARCH */}
      {/* ================================================= */}

      <div className="mb-5 rounded-2xl border border-border bg-surface p-4 shadow-sm">

        <div className="relative max-w-lg">

          <Search
            size={19}
            className="absolute left-4 top-1/2 -translate-y-1/2 text-text-light"
          />

          <input
            type="text"
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
            placeholder="Search by subject code, name, course..."
            className="w-full rounded-xl border border-border bg-surface-muted py-3 pl-11 pr-4 text-sm text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
          />

        </div>

      </div>

      {/* ================================================= */}
      {/* TABLE */}
      {/* ================================================= */}

      <div className="overflow-hidden rounded-2xl border border-border bg-surface shadow-sm">

        <div className="overflow-x-auto">

          <table className="w-full min-w-[850px]">

            <thead className="border-b border-border bg-surface-muted">

              <tr>

                <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-text-muted">
                  Subject
                </th>

                <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-text-muted">
                  Course
                </th>

                <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-text-muted">
                  Semester
                </th>

                <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-text-muted">
                  Type
                </th>

                <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-text-muted">
                  Status
                </th>

                <th className="px-6 py-4 text-right text-xs font-bold uppercase tracking-wider text-text-muted">
                  Actions
                </th>

              </tr>

            </thead>

            <tbody className="divide-y divide-border">

              {loading ? (

                <tr>
                  <td
                    colSpan="6"
                    className="px-6 py-12 text-center text-sm text-text-muted"
                  >
                    Loading subjects...
                  </td>
                </tr>

              ) : filteredSubjects.length === 0 ? (

                <tr>
                  <td
                    colSpan="6"
                    className="px-6 py-14 text-center"
                  >

                    <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-accent-light text-primary">
                      <BookOpen size={22} />
                    </div>

                    <p className="mt-4 font-semibold text-text">
                      No subjects found
                    </p>

                    <p className="mt-1 text-sm text-text-muted">
                      {search
                        ? "Try changing your search."
                        : "Create your first subject to get started."}
                    </p>

                  </td>
                </tr>

              ) : (

                filteredSubjects.map(
                  (subject) => (
                    <tr
                      key={subject.id}
                      className="transition hover:bg-surface-muted"
                    >

                      <td className="px-6 py-4">

                        <div>
                          <p className="font-semibold text-text">
                            {subject.subject_name}
                          </p>

                          <p className="mt-1 text-xs font-medium text-text-muted">
                            {subject.subject_code}
                          </p>
                        </div>

                      </td>

                      <td className="px-6 py-4 text-sm text-text-muted">
                        {getCourseName(
                          subject.course_id
                        )}
                      </td>

                      <td className="px-6 py-4 text-sm font-medium text-text">
                        Semester{" "}
                        {subject.semester}
                      </td>

                      <td className="px-6 py-4">

                        <span className="rounded-full bg-accent-light px-3 py-1 text-xs font-semibold text-primary">
                          {subject.subject_type}
                        </span>

                      </td>

                      <td className="px-6 py-4">

                        <span
                          className={`rounded-full px-3 py-1 text-xs font-semibold ${subject.is_active
                              ? "bg-green-50 text-success"
                              : "bg-red-50 text-danger"
                            }`}
                        >
                          {subject.is_active
                            ? "Active"
                            : "Inactive"}
                        </span>

                      </td>

                      <td className="px-6 py-4">

                        <div className="flex justify-end gap-2">

<button
  type="button"
  onClick={() =>
    handleViewDetails(subject)
  }
  disabled={detailsLoading}
  className="rounded-lg p-2 text-text-muted transition hover:bg-accent-light hover:text-primary"
  title="View details"
>
  <Eye size={17} />
</button>
                          <button
                            type="button"
                            onClick={() =>
                              handleEdit(
                                subject
                              )
                            }
                            className="rounded-lg p-2 text-primary transition hover:bg-accent-light"
                            title="Edit subject"
                          >
                            <Pencil size={17} />
                          </button>

               <button
  type="button"
  onClick={() =>
    handleStatusChange(subject)
  }
  disabled={
    statusLoading === subject.id
  }
  className={`rounded-lg p-2 transition ${
    subject.is_active
      ? "text-danger hover:bg-danger/10"
      : "text-success hover:bg-accent-light"
  }`}
  title={
    subject.is_active
      ? "Deactivate subject"
      : "Activate subject"
  }
>
  {statusLoading === subject.id ? (
    <Loader2
      size={17}
      className="animate-spin"
    />
  ) : (
    <Power size={17} />
  )}
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
      {/* FORM */}
      {/* ================================================= */}
<CsvImport
  entity="subjects"
  isOpen={showCsvImport}
  onClose={() => setShowCsvImport(false)}
  onValidate={validateCsv}
  onImport={importCsv}
/>
      {showForm && (
        <SubjectForm
          subject={editingSubject}
          courses={courses}
          onClose={() => {
            setShowForm(false);
            setEditingSubject(null);
          }}
          onSuccess={handleFormSuccess}
        />
      )}
{viewingSubject && (
  <div
    className="
      fixed inset-0 z-[60]
      flex items-center justify-center
      bg-black/40 p-4
      backdrop-blur-sm
    "
    onMouseDown={(event) => {
      if (
        event.target === event.currentTarget
      ) {
        setViewingSubject(null);
      }
    }}
  >
    <div
      className="
        w-full max-w-2xl
        overflow-hidden
        rounded-2xl bg-surface
        shadow-2xl
      "
    >

      <div className="
        flex items-center justify-between
        border-b border-border
        px-6 py-5
      ">
        <div className="flex items-center gap-3">

          <div className="
            flex h-11 w-11
            items-center justify-center
            rounded-xl
            bg-accent-light text-primary
          ">
            <BookOpen size={21} />
          </div>

          <div>
            <h2 className="text-lg font-bold text-text">
              Subject Details
            </h2>

            <p className="text-sm text-text-muted">
              Subject and academic information.
            </p>
          </div>

        </div>

        <button
          type="button"
          onClick={() =>
            setViewingSubject(null)
          }
          className="
            rounded-lg p-2
            text-text-muted
            transition
            hover:bg-surface-muted
            hover:text-text
          "
        >
          <X size={20} />
        </button>

      </div>

      <div className="p-6">

        <div className="grid gap-4 sm:grid-cols-2">

          <div className="
            rounded-xl border border-border
            bg-surface-muted p-4
          ">
            <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">
              Subject Code
            </p>

            <p className="mt-2 text-lg font-bold text-primary">
              {viewingSubject.subject_code}
            </p>
          </div>

          <div className="
            rounded-xl border border-border
            bg-surface-muted p-4
          ">
            <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">
              Status
            </p>

            <p className="mt-2 text-lg font-bold text-text">
              {viewingSubject.is_active
                ? "Active"
                : "Inactive"}
            </p>
          </div>

        </div>

        <div className="
          mt-4 rounded-xl
          border border-border
          bg-surface-muted p-4
        ">
          <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">
            Subject Name
          </p>

          <p className="mt-2 text-lg font-bold text-text">
            {viewingSubject.subject_name}
          </p>
        </div>

        <div className="
          mt-4 grid gap-4
          sm:grid-cols-2
        ">

          <div className="
            rounded-xl border border-border
            bg-surface-muted p-4
          ">
            <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">
              Course
            </p>

            <p className="mt-2 text-sm font-bold text-text">
              {getCourseName(
                viewingSubject.course_id
              )}
            </p>
          </div>

          <div className="
            rounded-xl border border-border
            bg-surface-muted p-4
          ">
            <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">
              Semester
            </p>

            <p className="mt-2 text-sm font-bold text-text">
              Semester {viewingSubject.semester}
            </p>
          </div>

          <div className="
            rounded-xl border border-border
            bg-surface-muted p-4
            sm:col-span-2
          ">
            <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">
              Subject Type
            </p>

            <p className="mt-2 text-sm font-bold text-text">
              {viewingSubject.subject_type}
            </p>
          </div>

        </div>

      </div>

      <div className="
        flex justify-end
        border-t border-border
        px-6 py-4
      ">
        <button
          type="button"
          onClick={() =>
            setViewingSubject(null)
          }
          className="
            rounded-xl bg-sidebar
            px-5 py-2.5
            text-sm font-semibold
            text-white
            transition hover:bg-primary
          "
        >
          Close
        </button>
      </div>

    </div>
  </div>
)}
</div>
</main>
    </div>
  );
}

export default Subjects;
