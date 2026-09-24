import { useState } from "react";
import {
  Save,
  X,
} from "lucide-react";

import { post, put } from "../../../services/api";

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

   if (Number(formData.floor_no) < 0) {
  setError("Floor number cannot be negative.");
  return;
}

if (Number(formData.capacity) <= 0) {
  setError("Hall capacity must be greater than zero.");
  return;
}

if (Number(formData.examination_capacity) <= 0) {
  setError(
    "Examination capacity must be greater than zero."
  );
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
const payload = {
  name: formData.name.trim(),
  building_name: formData.building_name.trim(),
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
      ? Number(formData.assigned_course_id)
      : null,
  assigned_batch:
    formData.assigned_batch.trim() || null,
  is_available: formData.is_available,
  is_under_maintenance:
    formData.is_under_maintenance,
  is_accessible: formData.is_accessible,
};

if (isEditing) {
  await put(`/halls/${hall.id}`, payload);
} else {
  await post("/halls/", payload);
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
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm">
    <div className="max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-2xl border border-border bg-surface shadow-2xl">

      <div className="flex items-center justify-between border-b border-border px-6 py-5">
        <div>
          <p className="text-sm font-semibold uppercase tracking-widest text-accent">
            Hall Management
          </p>

          <h2 className="mt-1 text-xl font-bold text-text">
            {isEditing
              ? "Edit Examination Hall"
              : "Add Examination Hall"}
          </h2>
        </div>

        <button
          type="button"
          onClick={onCancel}
          className="rounded-lg p-2 text-text-muted transition hover:bg-surface-muted hover:text-text"
          aria-label="Close hall form"
        >
          <X size={20} />
        </button>
      </div>

     <div className="p-6">
  {error && (
    <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      {error}
    </div>
  )}

  <form
    onSubmit={handleSubmit}
    className="space-y-6"
  >
    {/* Basic Information */}

    <div>
      <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-accent">
        Basic Information
      </h3>

      <div className="grid gap-5 md:grid-cols-2">
        <FormField
          label="Hall Name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          placeholder="e.g. Hall 101"
          required
        />

        <FormField
          label="Building Name"
          name="building_name"
          value={formData.building_name}
          onChange={handleChange}
          placeholder="e.g. Main Block"
          required
        />

        <FormField
          label="Floor Number"
          name="floor_no"
          type="number"
          value={formData.floor_no}
          onChange={handleChange}
          placeholder="e.g. 1"
          min="0"
          required
        />

        <div>
          <label className="mb-2 block text-sm font-semibold text-sidebar">
            Room Type
            <span className="ml-1 text-danger">*</span>
          </label>

          <select
            name="room_type"
            value={formData.room_type}
            onChange={handleChange}
            required
            className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
          >
            <option value="">Select room type</option>
            <option value="CLASSROOM">Classroom</option>
            <option value="LABORATORY">Laboratory</option>
            <option value="AUDITORIUM">Auditorium</option>
            <option value="SEMINAR_HALL">Seminar Hall</option>
            <option value="OTHER">Other</option>
          </select>
        </div>
      </div>
    </div>

    {/* Capacity */}

    <div>
      <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-accent">
        Capacity
      </h3>

      <div className="grid gap-5 md:grid-cols-2">
        <FormField
          label="Total Capacity"
          name="capacity"
          type="number"
          value={formData.capacity}
          onChange={handleChange}
          placeholder="e.g. 60"
          min="1"
          required
        />

        <FormField
          label="Examination Capacity"
          name="examination_capacity"
          type="number"
          value={formData.examination_capacity}
          onChange={handleChange}
          placeholder="e.g. 50"
          min="1"
          required
        />
      </div>
    </div>

    {/* Assignment */}

    <div>
      <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-accent">
        Assignment
      </h3>

      <div className="grid gap-5 md:grid-cols-2">
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
            <option value="">Not assigned</option>

            {courses.map((course) => (
              <option
                key={course.id}
                value={course.id}
              >
                {course.course_code} - {course.course_name}
              </option>
            ))}
          </select>
        </div>

        <FormField
          label="Assigned Batch"
          name="assigned_batch"
          value={formData.assigned_batch}
          onChange={handleChange}
          placeholder="e.g. 2024"
        />
      </div>
    </div>

    {/* Amenities */}

    <div>
      <label className="mb-2 block text-sm font-semibold text-sidebar">
        Amenities
      </label>

      <textarea
        name="amenities"
        value={formData.amenities}
        onChange={handleChange}
        placeholder="e.g. Projector, AC, Wi-Fi, Smart Board"
        rows={3}
        className="w-full resize-none rounded-xl border border-border bg-surface px-4 py-3 text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
      />
    </div>

    {/* Hall Configuration */}

    <div>
      <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-accent">
        Hall Configuration
      </h3>

      <div className="grid gap-4 md:grid-cols-3">
        <StatusCheckbox
          name="is_available"
          checked={formData.is_available}
          onChange={handleChange}
          title="Available"
          description="Hall can be used for examinations."
        />

        <StatusCheckbox
          name="is_under_maintenance"
          checked={formData.is_under_maintenance}
          onChange={handleChange}
          title="Maintenance"
          description="Hall is currently under maintenance."
        />

        <StatusCheckbox
          name="is_accessible"
          checked={formData.is_accessible}
          onChange={handleChange}
          title="Accessible"
          description="Hall supports accessibility requirements."
        />
      </div>
    </div>

    {/* Actions */}

    <div className="flex justify-end gap-3 border-t border-border pt-5">
      <button
        type="button"
        onClick={onCancel}
        disabled={loading}
        className="flex items-center gap-2 rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold text-sidebar transition hover:bg-surface-muted"
      >
        <X size={17} />
        Cancel
      </button>

      <button
        type="submit"
        disabled={loading}
        className="flex items-center gap-2 rounded-xl bg-sidebar px-5 py-3 text-sm font-semibold text-white transition hover:bg-primary disabled:cursor-not-allowed disabled:opacity-60"
      >
        <Save size={17} />
        {loading
          ? "Saving..."
          : isEditing
            ? "Update Hall"
            : "Create Hall"}
      </button>
    </div>
  </form>
</div>
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
