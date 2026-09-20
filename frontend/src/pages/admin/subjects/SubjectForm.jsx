import { useEffect, useState } from "react";
import { X, BookOpen } from "lucide-react";

const API_URL =
  "http://127.0.0.1:5000/api/subjects/";

function SubjectForm({
  subject,
  courses,
  onClose,
  onSuccess,
}) {
  const [formData, setFormData] = useState({
    subject_code: "",
    subject_name: "",
    course_id: "",
    semester: "",
    subject_type: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const isEditing = Boolean(subject);

  useEffect(() => {
    if (subject) {
      setFormData({
        subject_code:
          subject.subject_code || "",
        subject_name:
          subject.subject_name || "",
        course_id:
          subject.course_id?.toString() || "",
        semester:
          subject.semester?.toString() || "",
        subject_type:
          subject.subject_type || "",
      });
    }
  }, [subject]);

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

    if (!formData.subject_code.trim()) {
      setError("Subject code is required.");
      return;
    }

    if (!formData.subject_name.trim()) {
      setError("Subject name is required.");
      return;
    }

    if (!formData.course_id) {
      setError("Please select a course.");
      return;
    }

    if (!formData.semester) {
      setError("Please select a semester.");
      return;
    }

    if (!formData.subject_type.trim()) {
      setError("Subject type is required.");
      return;
    }

    try {
      setLoading(true);

      const payload = {
        subject_code:
          formData.subject_code.trim(),

        subject_name:
          formData.subject_name.trim(),

        course_id:
          Number(formData.course_id),

        semester:
          Number(formData.semester),

        subject_type:
          formData.subject_type.trim(),
      };

      /*
       * Current backend only has POST.
       *
       * PUT/PATCH can be connected when the
       * backend update route is added.
       */

      if (isEditing) {
        const response = await fetch(
          `${API_URL}${subject.id}`,
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
            "Failed to update subject."
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
              "Failed to create subject."
          );
        }
      }

      onSuccess();
    } catch (err) {
      console.error(
        "Subject form error:",
        err
      );

      setError(
        err.message ||
          "Unable to save subject."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4 py-6">

      <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-surface shadow-2xl">

        {/* HEADER */}

        <div className="flex items-center justify-between border-b border-border px-6 py-5">

          <div className="flex items-center gap-3">

            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-light text-primary">
              <BookOpen size={20} />
            </div>

            <div>
              <h2 className="font-bold text-text">
                {isEditing
                  ? "Edit Subject"
                  : "Add Subject"}
              </h2>

              <p className="text-xs text-text-muted">
                {isEditing
                  ? "Update subject details"
                  : "Create a new subject"}
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

        {/* FORM */}

        <form
          onSubmit={handleSubmit}
          className="space-y-5 p-6"
        >

          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-danger">
              {error}
            </div>
          )}

          {/* Subject Code */}

          <div>

            <label className="mb-2 block text-sm font-semibold text-sidebar">
              Subject Code
            </label>

            <input
              type="text"
              name="subject_code"
              value={formData.subject_code}
              onChange={handleChange}
              placeholder="e.g. CS301"
              className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-sm text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
            />

          </div>

          {/* Subject Name */}

          <div>

            <label className="mb-2 block text-sm font-semibold text-sidebar">
              Subject Name
            </label>

            <input
              type="text"
              name="subject_name"
              value={formData.subject_name}
              onChange={handleChange}
              placeholder="e.g. Database Management Systems"
              className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-sm text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
            />

          </div>

          {/* Course */}

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

          {/* Semester */}

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
                (_, index) => index + 1
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

          {/* Subject Type */}

          <div>

            <label className="mb-2 block text-sm font-semibold text-sidebar">
              Subject Type
            </label>

            <select
              name="subject_type"
              value={formData.subject_type}
              onChange={handleChange}
              className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
            >

              <option value="">
                Select subject type
              </option>

              <option value="THEORY">
                Theory
              </option>

              <option value="PRACTICAL">
                Practical
              </option>

              <option value="LAB">
                Lab
              </option>

              <option value="PROJECT">
                Project
              </option>

              <option value="ELECTIVE">
                Elective
              </option>

            </select>

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
                  ? "Update Subject"
                  : "Create Subject"}
            </button>

          </div>

        </form>

      </div>

    </div>
  );
}

export default SubjectForm;
