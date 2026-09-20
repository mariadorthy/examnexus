import { useEffect, useState } from "react";
import {
  X,
  GraduationCap,
} from "lucide-react";

const API_URL =
  "http://127.0.0.1:5000/api/students/";

function StudentForm({
  student,
  courses,
  onClose,
  onSuccess,
}) {
  const [formData, setFormData] = useState({
    student_id: "",
    name: "",
    course_id: "",
    email: "",
    password_hash: "",
    contact_no: "",
    gender: "",
    disability: "",
    batch: "",
    semester: "",
    class_name: "",
    session: "",
    dob: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const isEditing = Boolean(student);

  useEffect(() => {
    if (student) {
      setFormData({
        student_id:
          student.student_id || "",

        name:
          student.name || "",

        course_id:
          student.course_id?.toString() || "",

        email:
          student.email || "",

        /*
         * The GET students endpoint does not
         * return password_hash, so it remains empty
         * when editing.
         */
        password_hash: "",

        contact_no:
          student.contact_no || "",

        gender:
          student.gender || "",

        disability:
          student.disability || "",

        batch:
          student.batch || "",

        semester:
          student.semester?.toString() || "",

        class_name:
          student.class_name || "",

        session:
          student.session || "",

        dob:
          student.dob || "",
      });
    }
  }, [student]);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");

    if (!formData.student_id.trim()) {
      setError("Student ID is required.");
      return;
    }

    if (!formData.name.trim()) {
      setError("Student name is required.");
      return;
    }

    if (!formData.course_id) {
      setError("Please select a course.");
      return;
    }

    if (!formData.email.trim()) {
      setError("Email is required.");
      return;
    }

    if (!isEditing && !formData.password_hash) {
      setError("Password is required.");
      return;
    }

    if (!formData.batch.trim()) {
      setError("Batch is required.");
      return;
    }

    if (!formData.semester) {
      setError("Please select a semester.");
      return;
    }

    try {
      setLoading(true);

      const payload = {
        student_id:
          formData.student_id.trim(),

        name:
          formData.name.trim(),

        course_id:
          Number(formData.course_id),

        email:
          formData.email.trim(),

        batch:
          formData.batch.trim(),

        semester:
          Number(formData.semester),

        contact_no:
          formData.contact_no.trim() || null,

        gender:
          formData.gender || null,

        disability:
          formData.disability.trim() || null,

        class_name:
          formData.class_name.trim() || null,

        session:
          formData.session.trim() || null,

        dob:
          formData.dob || null,
      };

      /*
       * IMPORTANT:
       *
       * Your current Flask POST route expects
       * password_hash directly.
       *
       * For now we send the field exactly as
       * the backend expects.
       *
       * Ideally, the backend should receive a
       * plain password and hash it server-side.
       */

      if (formData.password_hash) {
        payload.password_hash =
          formData.password_hash;
      }

      /*
       * Current backend has POST only.
       *
       * PUT/PATCH will work once the corresponding
       * Flask update route is added.
       */

      if (isEditing) {
        const response = await fetch(
          `${API_URL}${student.id}`,
          {
            method: "PUT",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify(payload),
          }
        );

        if (!response.ok) {
          throw new Error(
            "Failed to update student."
          );
        }
      } else {
        const response = await fetch(
          API_URL,
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify(payload),
          }
        );

        if (!response.ok) {
          const responseData =
            await response.json().catch(
              () => null
            );

          throw new Error(
            responseData?.message ||
              "Failed to create student."
          );
        }
      }

      onSuccess();
    } catch (err) {
      console.error(
        "Student form error:",
        err
      );

      setError(
        err.message ||
          "Unable to save student."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4 py-6">

      <div className="max-h-[92vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-surface shadow-2xl">

        {/* ================================================= */}
        {/* HEADER */}
        {/* ================================================= */}

        <div className="flex items-center justify-between border-b border-border px-6 py-5">

          <div className="flex items-center gap-3">

            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-light text-primary">
              <GraduationCap size={20} />
            </div>

            <div>

              <h2 className="font-bold text-text">
                {isEditing
                  ? "Edit Student"
                  : "Add Student"}
              </h2>

              <p className="text-xs text-text-muted">
                {isEditing
                  ? "Update student information"
                  : "Create a new student record"}
              </p>

            </div>

          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 text-text-muted transition hover:bg-surface-muted hover:text-text"
          >
            <X size={20} />
          </button>

        </div>

        {/* ================================================= */}
        {/* FORM */}
        {/* ================================================= */}

        <form
          onSubmit={handleSubmit}
          className="space-y-5 p-6"
        >

          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-danger">
              {error}
            </div>
          )}

          {/* Student ID + Name */}

          <div className="grid gap-5 md:grid-cols-2">

            <div>

              <label className="mb-2 block text-sm font-semibold text-sidebar">
                Student ID
              </label>

              <input
                type="text"
                name="student_id"
                value={formData.student_id}
                onChange={handleChange}
                placeholder="e.g. STU2026001"
                className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-sm text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
              />

            </div>

            <div>

              <label className="mb-2 block text-sm font-semibold text-sidebar">
                Full Name
              </label>

              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="Enter student name"
                className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-sm text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
              />

            </div>

          </div>

          {/* Course + Semester */}

          <div className="grid gap-5 md:grid-cols-2">

            <div>

              <label className="mb-2 block text-sm font-semibold text-sidebar">
                Course
              </label>

              <select
                name="course_id"
                value={formData.course_id}
                onChange={handleChange}
                className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
              >

                <option value="">
                  Select course
                </option>

                {courses.map((course) => (
                  <option
                    key={course.id}
                    value={course.id}
                  >
                    {course.course_code} -{" "}
                    {course.course_name}
                  </option>
                ))}

              </select>

            </div>

            <div>

              <label className="mb-2 block text-sm font-semibold text-sidebar">
                Semester
              </label>

              <select
                name="semester"
                value={formData.semester}
                onChange={handleChange}
                className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
              >

                <option value="">
                  Select semester
                </option>

                {Array.from(
                  {
                    length: 12,
                  },
                  (_, index) =>
                    index + 1
                ).map((semester) => (
                  <option
                    key={semester}
                    value={semester}
                  >
                    Semester {semester}
                  </option>
                ))}

              </select>

            </div>

          </div>

          {/* Email + Password */}

          <div className="grid gap-5 md:grid-cols-2">

            <div>

              <label className="mb-2 block text-sm font-semibold text-sidebar">
                Email
              </label>

              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="student@example.com"
                autoComplete="email"
                className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-sm text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
              />

            </div>

            <div>

              <label className="mb-2 block text-sm font-semibold text-sidebar">
                {isEditing
                  ? "New Password"
                  : "Password"}
              </label>

              <input
                type="password"
                name="password_hash"
                value={formData.password_hash}
                onChange={handleChange}
                placeholder={
                  isEditing
                    ? "Leave blank to keep current"
                    : "Enter password"
                }
                autoComplete="new-password"
                className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-sm text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
              />

            </div>

          </div>

          {/* Batch + Session */}

          <div className="grid gap-5 md:grid-cols-2">

            <div>

              <label className="mb-2 block text-sm font-semibold text-sidebar">
                Batch
              </label>

              <input
                type="text"
                name="batch"
                value={formData.batch}
                onChange={handleChange}
                placeholder="e.g. 2023-2027"
                className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-sm text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
              />

            </div>

            <div>

              <label className="mb-2 block text-sm font-semibold text-sidebar">
                Session
              </label>

              <input
                type="text"
                name="session"
                value={formData.session}
                onChange={handleChange}
                placeholder="e.g. 2026-27"
                className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-sm text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
              />

            </div>

          </div>

          {/* Contact + Gender */}

          <div className="grid gap-5 md:grid-cols-2">

            <div>

              <label className="mb-2 block text-sm font-semibold text-sidebar">
                Contact Number
              </label>

              <input
                type="tel"
                name="contact_no"
                value={formData.contact_no}
                onChange={handleChange}
                placeholder="Enter contact number"
                className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-sm text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
              />

            </div>

            <div>

              <label className="mb-2 block text-sm font-semibold text-sidebar">
                Gender
              </label>

              <select
                name="gender"
                value={formData.gender}
                onChange={handleChange}
                className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
              >

                <option value="">
                  Select gender
                </option>

                <option value="Male">
                  Male
                </option>

                <option value="Female">
                  Female
                </option>

                <option value="Other">
                  Other
                </option>

              </select>

            </div>

          </div>

          {/* Date of Birth + Class */}

          <div className="grid gap-5 md:grid-cols-2">

            <div>

              <label className="mb-2 block text-sm font-semibold text-sidebar">
                Date of Birth
              </label>

              <input
                type="date"
                name="dob"
                value={formData.dob}
                onChange={handleChange}
                className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
              />

            </div>

            <div>

              <label className="mb-2 block text-sm font-semibold text-sidebar">
                Class Name
              </label>

              <input
                type="text"
                name="class_name"
                value={formData.class_name}
                onChange={handleChange}
                placeholder="e.g. III-A"
                className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-sm text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
              />

            </div>

          </div>

          {/* Disability */}

          <div>

            <label className="mb-2 block text-sm font-semibold text-sidebar">
              Disability / Special Requirement
            </label>

            <textarea
              name="disability"
              value={formData.disability}
              onChange={handleChange}
              rows="3"
              placeholder="Enter details if applicable"
              className="w-full resize-none rounded-xl border border-border bg-surface px-4 py-3 text-sm text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
            />

          </div>

          {/* BUTTONS */}

          <div className="flex justify-end gap-3 border-t border-border pt-5">

            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold text-sidebar transition hover:bg-surface-muted"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={loading}
              className="rounded-xl bg-sidebar px-5 py-3 text-sm font-semibold text-white transition hover:bg-primary disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading
                ? "Saving..."
                : isEditing
                  ? "Update Student"
                  : "Create Student"}
            </button>

          </div>

        </form>

      </div>

    </div>
  );
}

export default StudentForm;
