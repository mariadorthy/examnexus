import { useEffect, useState } from "react";
import { Save, X } from "lucide-react";

const API_URL =
  "http://127.0.0.1:5000/api/examinations/";

function ExaminationForm({
  examination,
  subjects,
  subjectsLoading,
  onSuccess,
  onCancel,
}) {
  const [formData, setFormData] = useState({
    subject_id: "",
    exam_date: "",
    session: "",
    start_time: "",
    end_time: "",
    duration_minutes: "",
    exam_type: "",
  });

  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const isEditing = Boolean(examination);

  useEffect(() => {
    if (examination) {
      setFormData({
        subject_id: examination.subject_id || "",
        exam_date: examination.exam_date || "",
        session: examination.session || "",
        start_time: examination.start_time || "",
        end_time: examination.end_time || "",
        duration_minutes:
          examination.duration_minutes || "",
        exam_type: examination.exam_type || "",
      });
    } else {
      setFormData({
        subject_id: "",
        exam_date: "",
        session: "",
        start_time: "",
        end_time: "",
        duration_minutes: "",
        exam_type: "",
      });
    }

    setError("");
  }, [examination]);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const calculateDuration = () => {
    if (
      !formData.start_time ||
      !formData.end_time
    ) {
      return;
    }

    const [startHour, startMinute] =
      formData.start_time.split(":").map(Number);

    const [endHour, endMinute] =
      formData.end_time.split(":").map(Number);

    const start =
      startHour * 60 + startMinute;

    const end =
      endHour * 60 + endMinute;

    if (end > start) {
      setFormData((previous) => ({
        ...previous,
        duration_minutes: end - start,
      }));
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");

    if (!formData.subject_id) {
      setError("Please select a subject.");
      return;
    }

    if (!formData.exam_date) {
      setError("Please select an examination date.");
      return;
    }

    if (!formData.session.trim()) {
      setError("Please enter the examination session.");
      return;
    }

    if (!formData.start_time) {
      setError("Please select the start time.");
      return;
    }

    if (!formData.end_time) {
      setError("Please select the end time.");
      return;
    }

    if (
      !formData.duration_minutes ||
      Number(formData.duration_minutes) <= 0
    ) {
      setError("Please enter a valid duration.");
      return;
    }

    if (!formData.exam_type.trim()) {
      setError("Please enter the examination type.");
      return;
    }

    try {
      setSaving(true);

      /*
       * Current backend only supports POST.
       *
       * PUT/PATCH can be connected here when
       * update routes are added to Flask.
       */

      if (isEditing) {
        setError(
          "Editing is not available yet because the backend does not have an update examination route."
        );

        return;
      }

      const response = await fetch(API_URL, {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
        },

        body: JSON.stringify({
          subject_id: Number(
            formData.subject_id
          ),
          exam_date: formData.exam_date,
          session: formData.session.trim(),
          start_time: formData.start_time,
          end_time: formData.end_time,
          duration_minutes: Number(
            formData.duration_minutes
          ),
          exam_type: formData.exam_type.trim(),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.message ||
            "Failed to create examination."
        );
      }

      onSuccess();
    } catch (err) {
      console.error("Examination save error:", err);

      setError(
        err.message ||
          "Unable to create examination."
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-5"
    >

      {/* ================================================= */}
      {/* ERROR */}
      {/* ================================================= */}

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* ================================================= */}
      {/* SUBJECT */}
      {/* ================================================= */}

      <div>

        <label className="mb-2 block text-sm font-semibold text-sidebar">
          Subject
        </label>

        <select
          name="subject_id"
          value={formData.subject_id}
          onChange={handleChange}
          disabled={subjectsLoading}
          className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10 disabled:opacity-60"
        >
          <option value="">
            {subjectsLoading
              ? "Loading subjects..."
              : "Select subject"}
          </option>

          {subjects.map((subject) => (
            <option
              key={subject.id}
              value={subject.id}
            >
              {subject.subject_code} —{" "}
              {subject.subject_name}
            </option>
          ))}
        </select>

      </div>

      {/* ================================================= */}
      {/* DATE + SESSION */}
      {/* ================================================= */}

      <div className="grid gap-5 md:grid-cols-2">

        <div>

          <label className="mb-2 block text-sm font-semibold text-sidebar">
            Examination Date
          </label>

          <input
            type="date"
            name="exam_date"
            value={formData.exam_date}
            onChange={handleChange}
            className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
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
            placeholder="Morning"
            className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
          />

        </div>

      </div>

      {/* ================================================= */}
      {/* TIMES */}
      {/* ================================================= */}

      <div className="grid gap-5 md:grid-cols-2">

        <div>

          <label className="mb-2 block text-sm font-semibold text-sidebar">
            Start Time
          </label>

          <input
            type="time"
            name="start_time"
            value={formData.start_time}
            onChange={handleChange}
            onBlur={calculateDuration}
            className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
          />

        </div>

        <div>

          <label className="mb-2 block text-sm font-semibold text-sidebar">
            End Time
          </label>

          <input
            type="time"
            name="end_time"
            value={formData.end_time}
            onChange={handleChange}
            onBlur={calculateDuration}
            className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
          />

        </div>

      </div>

      {/* ================================================= */}
      {/* DURATION + TYPE */}
      {/* ================================================= */}

      <div className="grid gap-5 md:grid-cols-2">

        <div>

          <label className="mb-2 block text-sm font-semibold text-sidebar">
            Duration (minutes)
          </label>

          <input
            type="number"
            name="duration_minutes"
            min="1"
            value={formData.duration_minutes}
            onChange={handleChange}
            placeholder="180"
            className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
          />

        </div>

        <div>

          <label className="mb-2 block text-sm font-semibold text-sidebar">
            Examination Type
          </label>

          <select
            name="exam_type"
            value={formData.exam_type}
            onChange={handleChange}
            className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
          >
            <option value="">
              Select type
            </option>

            <option value="REGULAR">
              Regular
            </option>

            <option value="INTERNAL">
              Internal
            </option>

            <option value="MODEL">
              Model Examination
            </option>

            <option value="SUPPLEMENTARY">
              Supplementary
            </option>

            <option value="PRACTICAL">
              Practical
            </option>

          </select>

        </div>

      </div>

      {/* ================================================= */}
      {/* ACTIONS */}
      {/* ================================================= */}

      <div className="flex flex-col-reverse gap-3 border-t border-border pt-5 sm:flex-row sm:justify-end">

        <button
          type="button"
          onClick={onCancel}
          disabled={saving}
          className="flex items-center justify-center gap-2 rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold text-sidebar transition hover:bg-surface-muted disabled:opacity-50"
        >
          <X size={17} />

          Cancel
        </button>

        <button
          type="submit"
          disabled={saving}
          className="flex items-center justify-center gap-2 rounded-xl bg-sidebar px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-sidebar/10 transition hover:bg-primary disabled:cursor-not-allowed disabled:opacity-60"
        >
          <Save size={17} />

          {saving
            ? "Saving..."
            : isEditing
              ? "Update Examination"
              : "Create Examination"}
        </button>

      </div>

    </form>
  );
}

export default ExaminationForm;
