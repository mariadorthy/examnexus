import { useState } from "react";
import {
  ArrowLeft,
  Building2,
  Save,
  X,
} from "lucide-react";

const API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";

function HallForm({
  hall,
  courses,
  onCancel,
  onSuccess,
}) {
  const isEditing = Boolean(hall);

  const [formData, setFormData] = useState({
    name: hall?.name || "",
    building_name: hall?.building_name || "",
    floor_no: hall?.floor_no ?? "",
    capacity: hall?.capacity ?? "",
    examination_capacity:
      hall?.examination_capacity ?? "",
    room_type: hall?.room_type || "",
    amenities: hall?.amenities || "",
    assigned_course_id:
      hall?.assigned_course_id || "",
    assigned_batch: hall?.assigned_batch || "",
    is_available:
      hall?.is_available !== undefined
        ? hall.is_available
        : true,
    is_under_maintenance:
      hall?.is_under_maintenance !== undefined
        ? hall.is_under_maintenance
        : false,
    is_accessible:
      hall?.is_accessible !== undefined
        ? hall.is_accessible
        : true,
  });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (event) => {
    const { name, value, type, checked } =
      event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");

    if (!formData.name.trim()) {
      setError("Please enter the hall name.");
      return;
    }

    if (!formData.building_name.trim()) {
      setError("Please enter the building name.");
      return;
    }

    if (formData.floor_no === "") {
      setError("Please enter the floor number.");
      return;
    }

    if (formData.capacity === "") {
      setError("Please enter the hall capacity.");
      return;
    }

    if (
      formData.examination_capacity === ""
    ) {
      setError(
        "Please enter the examination capacity."
      );
      return;
    }

    if (!formData.room_type) {
      setError("Please select a room type.");
      return;
    }

    if (
      Number(formData.examination_capacity) >
      Number(formData.capacity)
    ) {
      setError(
        "Examination capacity cannot be greater than total capacity."
      );
      return;
    }

    try {
      setLoading(true);

      /*
       * Current backend only supports POST.
       *
       * When PUT/PATCH is added later, update the
       * editing branch here.
       */

      if (isEditing) {
        throw new Error(
          "Hall editing API is not available yet. Add a PUT/PATCH hall route in the backend."
        );
      }

      const response = await fetch(
        `${API_URL}/api/halls/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: formData.name.trim(),
            building_name:
              formData.building_name.trim(),
            floor_no: Number(formData.floor_no),
            capacity: Number(formData.capacity),
            examination_capacity: Number(
              formData.examination_capacity
            ),
            room_type: formData.room_type,
            amenities:
              formData.amenities.trim() || null,
            assigned_course_id:
              formData.assigned_course_id
                ? Number(
                    formData.assigned_course_id
                  )
                : null,
            assigned_batch:
              formData.assigned_batch.trim() || null,

            /*
             * These fields are supported by the model,
             * but your current Flask POST route does not
             * read them.
             *
             * They are therefore not sent here until
             * the backend route is updated.
             */
          }),
        }
      );

      const result = await response.json();

      if (!response.ok) {
        throw new Error(
          result.message || "Failed to create hall."
        );
      }

      onSuccess();
    } catch (err) {
      console.error("Hall form error:", err);

      setError(
        err.message ||
          "Unable to save examination hall."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}

      <div className="border-b border-border bg-surface">
        <div className="flex items-center gap-4 px-5 py-6 md:px-8">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-xl border border-border p-2.5 text-sidebar transition hover:border-accent hover:bg-surface-muted"
          >
            <ArrowLeft size={20} />
          </button>

          <div>
            <p className="text-sm font-semibold uppercase tracking-widest text-accent">
              Hall Management
            </p>

            <h1 className="mt-1 text-2xl font-bold text-text">
              {isEditing
                ? "Edit Examination Hall"
                : "Add Examination Hall"}
            </h1>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-4xl p-5 md:p-8">
        {error && (
          <div className="mb-6 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            <X
              size={18}
              className="mt-0.5 shrink-0"
            />

            <span>{error}</span>
          </div>
        )}

        <form
          onSubmit={handleSubmit}
          className="space-y-6"
        >
          {/* Basic Information */}

          <section className="rounded-2xl border border-border bg-surface p-6 shadow-sm">
            <div className="mb-6 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-light text-primary">
                <Building2 size={20} />
              </div>

              <div>
                <h2 className="font-bold text-text">
                  Hall Information
                </h2>

                <p className="text-sm text-text-muted">
                  Enter the basic details of the examination hall.
                </p>
              </div>
            </div>

            <div className="grid gap-5 md:grid-cols-2">
              <FormField
                label="Hall Name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="Hall A"
                required
              />

              <FormField
                label="Building Name"
                name="building_name"
                value={formData.building_name}
                onChange={handleChange}
                placeholder="Main Block"
                required
              />

              <FormField
                label="Floor Number"
                name="floor_no"
                type="number"
                min="0"
                value={formData.floor_no}
                onChange={handleChange}
                placeholder="1"
                required
              />

              <div>
                <label className="mb-2 block text-sm font-semibold text-sidebar">
                  Room Type
                  <span className="ml-1 text-danger">
                    *
                  </span>
                </label>

                <select
                  name="room_type"
                  value={formData.room_type}
                  onChange={handleChange}
                  required
                  className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
                >
                  <option value="">
                    Select room type
                  </option>

                  <option value="CLASSROOM">
                    Classroom
                  </option>

                  <option value="LABORATORY">
                    Laboratory
                  </option>

                  <option value="AUDITORIUM">
                    Auditorium
                  </option>

                  <option value="SEMINAR_HALL">
                    Seminar Hall
                  </option>

                  <option value="OTHER">
                    Other
                  </option>
                </select>
              </div>
            </div>
          </section>

          {/* Capacity */}

          <section className="rounded-2xl border border-border bg-surface p-6 shadow-sm">
            <h2 className="font-bold text-text">
              Capacity
            </h2>

            <p className="mt-1 text-sm text-text-muted">
              Configure seating capacity for regular and examination use.
            </p>

            <div className="mt-6 grid gap-5 md:grid-cols-2">
              <FormField
                label="Total Capacity"
                name="capacity"
                type="number"
                min="1"
                value={formData.capacity}
                onChange={handleChange}
                placeholder="60"
                required
              />

              <FormField
                label="Examination Capacity"
                name="examination_capacity"
                type="number"
                min="1"
                value={formData.examination_capacity}
                onChange={handleChange}
                placeholder="50"
                required
              />
            </div>
          </section>

          {/* Assignment */}

          <section className="rounded-2xl border border-border bg-surface p-6 shadow-sm">
            <h2 className="font-bold text-text">
              Assignment
            </h2>

            <p className="mt-1 text-sm text-text-muted">
              Optionally assign this hall to a course and batch.
            </p>

            <div className="mt-6 grid gap-5 md:grid-cols-2">
              <div>
                <label className="mb-2 block text-sm font-semibold text-sidebar">
                  Assigned Course
                </label>

                <select
                  name="assigned_course_id"
                  value={formData.assigned_course_id}
                  onChange={handleChange}
                  className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
                >
                  <option value="">
                    No course assigned
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

              <FormField
                label="Assigned Batch"
                name="assigned_batch"
                value={formData.assigned_batch}
                onChange={handleChange}
                placeholder="2024"
              />

              <div className="md:col-span-2">
                <label className="mb-2 block text-sm font-semibold text-sidebar">
                  Amenities
                </label>

                <textarea
                  name="amenities"
                  value={formData.amenities}
                  onChange={handleChange}
                  rows="3"
                  placeholder="Projector, Air Conditioning, CCTV..."
                  className="w-full resize-none rounded-xl border border-border bg-surface px-4 py-3 text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
                />
              </div>
            </div>
          </section>

          {/* Status */}

          <section className="rounded-2xl border border-border bg-surface p-6 shadow-sm">
            <h2 className="font-bold text-text">
              Hall Status
            </h2>

            <div className="mt-5 space-y-4">
              <StatusCheckbox
                name="is_available"
                checked={formData.is_available}
                onChange={handleChange}
                title="Available for use"
                description="Allow this hall to be considered for examinations."
              />

              <StatusCheckbox
                name="is_under_maintenance"
                checked={
                  formData.is_under_maintenance
                }
                onChange={handleChange}
                title="Under maintenance"
                description="Mark the hall as temporarily unavailable due to maintenance."
              />

              <StatusCheckbox
                name="is_accessible"
                checked={formData.is_accessible}
                onChange={handleChange}
                title="Accessible"
                description="Indicate that the hall supports accessibility requirements."
              />
            </div>
          </section>

          {/* Actions */}

          <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
            <button
              type="button"
              onClick={onCancel}
              className="rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold text-sidebar transition hover:border-accent"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={loading}
              className="flex items-center justify-center gap-2 rounded-xl bg-sidebar px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-sidebar/10 transition hover:bg-primary disabled:cursor-not-allowed disabled:opacity-60"
            >
              <Save size={17} />

              {loading
                ? "Saving..."
                : isEditing
                  ? "Update Hall"
                  : "Save Hall"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function FormField({
  label,
  name,
  type = "text",
  value,
  onChange,
  placeholder,
  required = false,
  min,
}) {
  return (
    <div>
      <label className="mb-2 block text-sm font-semibold text-sidebar">
        {label}

        {required && (
          <span className="ml-1 text-danger">*</span>
        )}
      </label>

      <input
        type={type}
        name={name}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
        min={min}
        className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
      />
    </div>
  );
}

function StatusCheckbox({
  name,
  checked,
  onChange,
  title,
  description,
}) {
  return (
    <label className="flex cursor-pointer items-center justify-between gap-4 rounded-xl border border-border bg-surface-muted p-4">
      <div>
        <p className="font-semibold text-text">
          {title}
        </p>

        <p className="mt-1 text-sm text-text-muted">
          {description}
        </p>
      </div>

      <input
        type="checkbox"
        name={name}
        checked={checked}
        onChange={onChange}
        className="h-5 w-5 shrink-0 rounded border-gray-300 accent-sidebar"
      />
    </label>
  );
}

export default HallForm;
