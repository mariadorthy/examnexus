import { useEffect, useState } from "react";
import {
  Plus,
  Search,
  Pencil,
  Trash2,
  GraduationCap,
  RefreshCw,
} from "lucide-react";

import StudentForm from "./StudentForm";
import { get } from "../../../services/api";
import AdminSidebar from "../../../components/AdminSidebar";
import AdminTopbar from "../../../components/AdminTopbar";

function Students({
  user,
  onLogout,
  onNavigate,
}) {
  const [sidebarOpen, setSidebarOpen] =
    useState(false);
  const [students, setStudents] = useState([]);
  const [courses, setCourses] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [editingStudent, setEditingStudent] =
    useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError("");

      const [
  studentsData,
  coursesData,
] = await Promise.all([
  get("/students/"),
  get("/courses/"),
]);

setStudents(studentsData);
setCourses(coursesData);
     
    } catch (err) {
      console.error("Students error:", err);

      setError(
        "Unable to load students. Please make sure the backend is running."
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
    setEditingStudent(null);
    setShowForm(true);
  };

  const handleEdit = (student) => {
    setEditingStudent(student);
    setShowForm(true);
  };

  const handleDelete = async (student) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete ${student.name}?`
    );

    if (!confirmed) {
      return;
    }

    /*
     * DELETE endpoint is not currently present
     * in the Flask backend.
     */

    try {
      const response = await fetch(
        `${API_URL}${student.id}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        throw new Error(
          "Delete operation failed."
        );
      }

      await loadData();
    } catch (err) {
      console.error("Delete student error:", err);

      setError(
        "Unable to delete student. The backend DELETE route may not be available yet."
      );
    }
  };

  const handleFormSuccess = () => {
    setShowForm(false);
    setEditingStudent(null);
    loadData();
  };

  const filteredStudents = students.filter(
    (student) => {
      const searchText =
        search.trim().toLowerCase();

      if (!searchText) {
        return true;
      }

      return (
        student.student_id
          ?.toLowerCase()
          .includes(searchText) ||
        student.name
          ?.toLowerCase()
          .includes(searchText) ||
        student.email
          ?.toLowerCase()
          .includes(searchText) ||
        student.batch
          ?.toLowerCase()
          .includes(searchText) ||
        getCourseName(student.course_id)
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
      activePage="Students"
      onNavigate={onNavigate}
    />

    <main className="lg:ml-72">

      <AdminTopbar
        user={user}
        title="Students"
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
            Students
          </h1>

          <p className="mt-2 text-sm text-text-muted">
            Manage student records and academic information.
          </p>

        </div>

        <div className="flex gap-3">

          <button
            type="button"
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-2 rounded-xl border border-border bg-surface px-4 py-3 text-sm font-semibold text-sidebar transition hover:bg-surface-muted disabled:opacity-60"
          >

            <RefreshCw
              size={17}
              className={
                loading
                  ? "animate-spin"
                  : ""
              }
            />

            Refresh

          </button>

          <button
            type="button"
            onClick={handleAdd}
            className="flex items-center gap-2 rounded-xl bg-sidebar px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-sidebar/10 transition hover:bg-primary"
          >

            <Plus size={18} />

            Add Student

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
            placeholder="Search by student ID, name, email, course..."
            className="w-full rounded-xl border border-border bg-surface-muted py-3 pl-11 pr-4 text-sm text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
          />

        </div>

      </div>

      {/* ================================================= */}
      {/* TABLE */}
      {/* ================================================= */}

      <div className="overflow-hidden rounded-2xl border border-border bg-surface shadow-sm">

        <div className="overflow-x-auto">

          <table className="w-full min-w-[1050px]">

            <thead className="border-b border-border bg-surface-muted">

              <tr>

                <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-text-muted">
                  Student
                </th>

                <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-text-muted">
                  Course
                </th>

                <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-text-muted">
                  Batch
                </th>

                <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-text-muted">
                  Semester
                </th>

                <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-text-muted">
                  Email
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
                    colSpan="7"
                    className="px-6 py-12 text-center text-sm text-text-muted"
                  >
                    Loading students...
                  </td>

                </tr>

              ) : filteredStudents.length === 0 ? (

                <tr>

                  <td
                    colSpan="7"
                    className="px-6 py-14 text-center"
                  >

                    <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-accent-light text-primary">
                      <GraduationCap size={22} />
                    </div>

                    <p className="mt-4 font-semibold text-text">
                      No students found
                    </p>

                    <p className="mt-1 text-sm text-text-muted">
                      {search
                        ? "Try changing your search."
                        : "Create your first student to get started."}
                    </p>

                  </td>

                </tr>

              ) : (

                filteredStudents.map(
                  (student) => (
                    <tr
                      key={student.id}
                      className="transition hover:bg-surface-muted"
                    >

                      <td className="px-6 py-4">

                        <div className="flex items-center gap-3">

                          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-accent-light text-sm font-bold text-primary">
                            {student.name
                              ?.charAt(0)
                              .toUpperCase()}
                          </div>

                          <div>

                            <p className="font-semibold text-text">
                              {student.name}
                            </p>

                            <p className="mt-1 text-xs font-medium text-text-muted">
                              {student.student_id}
                            </p>

                          </div>

                        </div>

                      </td>

                      <td className="px-6 py-4 text-sm text-text-muted">
                        {getCourseName(
                          student.course_id
                        )}
                      </td>

                      <td className="px-6 py-4 text-sm font-medium text-text">
                        {student.batch}
                      </td>

                      <td className="px-6 py-4 text-sm text-text">
                        Semester{" "}
                        {student.semester}
                      </td>

                      <td className="px-6 py-4 text-sm text-text-muted">
                        {student.email}
                      </td>

                      <td className="px-6 py-4">

                        <span
                          className={`rounded-full px-3 py-1 text-xs font-semibold ${
                            student.is_active
                              ? "bg-green-50 text-success"
                              : "bg-red-50 text-danger"
                          }`}
                        >
                          {student.is_active
                            ? "Active"
                            : "Inactive"}
                        </span>

                      </td>

                      <td className="px-6 py-4">

                        <div className="flex justify-end gap-2">

                          <button
                            type="button"
                            onClick={() =>
                              handleEdit(
                                student
                              )
                            }
                            className="rounded-lg p-2 text-primary transition hover:bg-accent-light"
                            title="Edit student"
                          >
                            <Pencil size={17} />
                          </button>

                          <button
                            type="button"
                            onClick={() =>
                              handleDelete(
                                student
                              )
                            }
                            className="rounded-lg p-2 text-danger transition hover:bg-red-50"
                            title="Delete student"
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
      {/* FORM */}
      {/* ================================================= */}

      {showForm && (
        <StudentForm
          student={editingStudent}
          courses={courses}
          onClose={() => {
            setShowForm(false);
            setEditingStudent(null);
          }}
          onSuccess={handleFormSuccess}
        />
      )}
      </div>
    </main>
    </div>
  );
}

export default Students;
