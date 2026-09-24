import { useEffect, useState } from "react";
import {
  Plus,
  Search,
  Pencil,
  GraduationCap,
  RefreshCw,
  Power,
  Eye,
  X,
  Loader2,
} from "lucide-react";

import StudentForm from "./StudentForm";
import { get, patch } from "../../../services/api";
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

const [viewingStudent, setViewingStudent] =
  useState(null);

const [detailsLoading, setDetailsLoading] =
  useState(false);

const [statusLoading, setStatusLoading] =
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

console.log(
  "STUDENTS GET response:",
  studentsData
);
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
  const handleViewDetails = async (student) => {
  try {
    setDetailsLoading(true);

    const data = await get(
      `/students/${student.id}`
    );

    setViewingStudent(data);
  } catch (err) {
    console.error(
      "Student details error:",
      err
    );

    setError(
      err.message ||
      "Unable to load student details."
    );
  } finally {
    setDetailsLoading(false);
  }
};
const handleStatusChange = async (student) => {
  try {
    setStatusLoading(student.id);

    const newStatus = !student.is_active;

    console.log("STUDENT CLICKED:", {
      id: student.id,
      student_id: student.student_id,
      current: student.is_active,
      sending: newStatus,
    });

    const response = await patch(
      `/students/${student.id}/status`,
      {
        is_active: newStatus,
      }
    );

    console.log("STUDENT PATCH RESPONSE:", response);

    const updatedData = await get("/students/");

const updatedStudent = updatedData.find(
  (item) => item.id === student.id
);

console.log("STUDENT AFTER GET:", updatedStudent);

setStudents((currentStudents) =>
  currentStudents.map((item) =>
    item.id === student.id
      ? {
          ...item,
          is_active: updatedStudent?.is_active,
        }
      : item
  )
);
  } catch (err) {
        console.error(
      "Student status error:",
      err
    );

    setError(
      err.message ||
        "Unable to update student status."
    );
  } finally {
    setStatusLoading(null);
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
    handleViewDetails(student)
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
    handleStatusChange(student)
  }
  disabled={
    statusLoading === student.id
  }
  className={`rounded-lg p-2 transition ${
    student.is_active
      ? "text-danger hover:bg-danger/10"
      : "text-success hover:bg-accent-light"
  }`}
  title={
    student.is_active
      ? "Deactivate student"
      : "Activate student"
  }
>
  {statusLoading === student.id ? (
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

{viewingStudent && (
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
        setViewingStudent(null);
      }
    }}
  >
    <div
      className="
        w-full max-w-3xl
        max-h-[90vh]
        overflow-y-auto
        overflow-hidden
        rounded-2xl bg-surface
        shadow-2xl
      "
    >

      {/* HEADER */}

      <div
        className="
          flex items-center justify-between
          border-b border-border
          px-6 py-5
        "
      >
        <div className="flex items-center gap-3">

          <div
            className="
              flex h-11 w-11
              items-center justify-center
              rounded-xl
              bg-accent-light
              text-primary
            "
          >
            <GraduationCap size={21} />
          </div>

          <div>
            <h2 className="text-lg font-bold text-text">
              Student Details
            </h2>

            <p className="text-sm text-text-muted">
              Student and academic information.
            </p>
          </div>

        </div>

        <button
          type="button"
          onClick={() =>
            setViewingStudent(null)
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

      {/* DETAILS */}

      <div className="p-6">

        <div className="grid gap-4 sm:grid-cols-2">

          <div
            className="
              rounded-xl border border-border
              bg-surface-muted p-4
            "
          >
            <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">
              Student ID
            </p>

            <p className="mt-2 text-lg font-bold text-primary">
              {viewingStudent.student_id}
            </p>
          </div>

          <div
            className="
              rounded-xl border border-border
              bg-surface-muted p-4
            "
          >
            <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">
              Status
            </p>

            <p className="mt-2 text-lg font-bold text-text">
              {viewingStudent.is_active
                ? "Active"
                : "Inactive"}
            </p>
          </div>

        </div>

        <div
          className="
            mt-4 rounded-xl
            border border-border
            bg-surface-muted p-4
          "
        >
          <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">
            Name
          </p>

          <p className="mt-2 text-lg font-bold text-text">
            {viewingStudent.name}
          </p>
        </div>

        <div className="mt-4 grid gap-4 sm:grid-cols-2">

          <div
            className="
              rounded-xl border border-border
              bg-surface-muted p-4
            "
          >
            <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">
              Course
            </p>

            <p className="mt-2 text-sm font-bold text-text">
              {getCourseName(
                viewingStudent.course_id
              )}
            </p>
          </div>

          <div
            className="
              rounded-xl border border-border
              bg-surface-muted p-4
            "
          >
            <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">
              Semester
            </p>

            <p className="mt-2 text-sm font-bold text-text">
              Semester {viewingStudent.semester}
            </p>
          </div>

          <div
            className="
              rounded-xl border border-border
              bg-surface-muted p-4
            "
          >
            <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">
              Batch
            </p>

            <p className="mt-2 text-sm font-bold text-text">
              {viewingStudent.batch}
            </p>
          </div>

          <div
            className="
              rounded-xl border border-border
              bg-surface-muted p-4
            "
          >
            <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">
              Class
            </p>

            <p className="mt-2 text-sm font-bold text-text">
              {viewingStudent.class_name || "—"}
            </p>
          </div>

          <div
            className="
              rounded-xl border border-border
              bg-surface-muted p-4
            "
          >
            <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">
              Session
            </p>

            <p className="mt-2 text-sm font-bold text-text">
              {viewingStudent.session || "—"}
            </p>
          </div>

          <div
            className="
              rounded-xl border border-border
              bg-surface-muted p-4
            "
          >
            <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">
              Email
            </p>

            <p className="mt-2 text-sm font-bold text-text break-all">
              {viewingStudent.email}
            </p>
          </div>

          <div
            className="
              rounded-xl border border-border
              bg-surface-muted p-4
            "
          >
            <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">
              Contact Number
            </p>

            <p className="mt-2 text-sm font-bold text-text">
              {viewingStudent.contact_no || "—"}
            </p>
          </div>

          <div
            className="
              rounded-xl border border-border
              bg-surface-muted p-4
            "
          >
            <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">
              Gender
            </p>

            <p className="mt-2 text-sm font-bold text-text">
              {viewingStudent.gender || "—"}
            </p>
          </div>

          <div
            className="
              rounded-xl border border-border
              bg-surface-muted p-4
            "
          >
            <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">
              Date of Birth
            </p>

            <p className="mt-2 text-sm font-bold text-text">
              {viewingStudent.dob || "—"}
            </p>
          </div>

          <div
            className="
              rounded-xl border border-border
              bg-surface-muted p-4
            "
          >
            <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">
              Email Verification
            </p>

            <p className="mt-2 text-sm font-bold text-text">
              {viewingStudent.email_verified
                ? "Verified"
                : "Not Verified"}
            </p>
          </div>

          <div
            className="
              rounded-xl border border-border
              bg-surface-muted p-4
            "
          >
            <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">
              Two-Factor Authentication
            </p>

            <p className="mt-2 text-sm font-bold text-text">
              {viewingStudent.two_factor_enabled
                ? "Enabled"
                : "Disabled"}
            </p>
          </div>

          <div
            className="
              rounded-xl border border-border
              bg-surface-muted p-4
            "
          >
            <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">
              Disability / Accessibility
            </p>

            <p className="mt-2 text-sm font-bold text-text">
              {viewingStudent.disability || "None"}
            </p>
          </div>

        </div>

      </div>

      {/* FOOTER */}

      <div
        className="
          flex justify-end
          border-t border-border
          px-6 py-4
        "
      >
        <button
          type="button"
          onClick={() =>
            setViewingStudent(null)
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

export default Students;
