import { useState } from "react";
import { post, put } from "../../../services/api";
import {
  Save,
  UserPlus,
  X,
} from "lucide-react";

function StaffForm({
  staff,
  departments,
  onCancel,
  onSuccess,
}) {
  const isEditing = Boolean(staff);

  const [formData, setFormData] = useState({
    name: staff?.name || "",
    department_id: staff?.department_id || "",
    email: staff?.email || "",
    contact_no: staff?.contact_no || "",
    designation: staff?.designation || "",
    dob: staff?.dob || "",
    assigned_courses: staff?.assigned_courses || "",
    gender: staff?.gender || "",
    availability:
      staff?.availability !== undefined
        ? staff.availability
        : true,
    assigned_batch: staff?.assigned_batch || "",
   password: "",
    image: staff?.image || "",
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
      setError("Please enter the staff name.");
      return;
    }

    if (!formData.department_id) {
      setError("Please select a department.");
      return;
    }

    if (!formData.email.trim()) {
      setError("Please enter the email address.");
      return;
    }

    if (!formData.designation.trim()) {
      setError("Please enter the designation.");
      return;
    }

    if (!isEditing && !formData.password.trim()) {
      setError("Please enter a password.");
      return;
    }

    try {
      setLoading(true);

const payload = {
  name: formData.name.trim(),
  department_id: Number(formData.department_id),
  email: formData.email.trim().toLowerCase(),
  contact_no: formData.contact_no.trim() || null,
  designation: formData.designation.trim(),
  dob: formData.dob || null,
  assigned_courses:
    formData.assigned_courses.trim() || null,
  gender: formData.gender || null,
  availability: formData.availability,
  assigned_batch:
    formData.assigned_batch.trim() || null,
  image: formData.image.trim() || null,
};

if (formData.password.trim()) {
  payload.password = formData.password;
}

if (isEditing) {
  await put(`/staff/${staff.id}`, payload);
} else {
  await post("/staff/", payload);
}

onSuccess();
    } catch (err) {
      console.error("Staff form error:", err);

      setError(
        err.message ||
          "Unable to save staff member."
      );
    } finally {
      setLoading(false);
    }
  };

 return (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm">
    <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl border border-border bg-surface shadow-2xl">

      {/* Modal Header */}
      <div className="flex items-center justify-between border-b border-border px-6 py-5">
        <div>
          <p className="text-sm font-semibold uppercase tracking-widest text-accent">
            Staff Management
          </p>

          <h2 className="mt-1 text-xl font-bold text-text">
            {isEditing ? "Edit Staff" : "Add Staff"}
          </h2>
        </div>

        <button
          type="button"
          onClick={onCancel}
          className="rounded-lg p-2 text-text-muted transition hover:bg-surface-muted hover:text-text"
          aria-label="Close staff form"
        >
          <X size={20} />
        </button>
      </div>

      {/* Modal Body */}
      <div className="p-6">
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
                <UserPlus size={20} />
              </div>

              <div>
                <h2 className="font-bold text-text">
                  Basic Information
                </h2>

                <p className="text-sm text-text-muted">
                  Enter the staff member's details.
                </p>
              </div>
            </div>

            <div className="grid gap-5 md:grid-cols-2">
              <FormField
                label="Full Name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="Dr. John Smith"
                required
              />

              <FormField
                label="Email Address"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="john@examnexus.edu"
                required
              />

              <FormField
                label="Contact Number"
                name="contact_no"
                value={formData.contact_no}
                onChange={handleChange}
                placeholder="+91 9876543210"
              />

              <FormField
                label="Date of Birth"
                name="dob"
                type="date"
                value={formData.dob}
                onChange={handleChange}
              />

              <div>
                <label className="mb-2 block text-sm font-semibold text-sidebar">
                  Gender
                </label>

                <select
                  name="gender"
                  value={formData.gender}
                  onChange={handleChange}
                  className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
                >
                  <option value="">Select gender</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <FormField
                label="Designation"
                name="designation"
                value={formData.designation}
                onChange={handleChange}
                placeholder="Assistant Professor"
                required
              />
            </div>
          </section>

          {/* Department & Assignment */}
          <section className="rounded-2xl border border-border bg-surface p-6 shadow-sm">
            <h2 className="font-bold text-text">
              Department & Assignment
            </h2>

            <p className="mt-1 text-sm text-text-muted">
              Configure the staff member's academic assignment.
            </p>

            <div className="mt-6 grid gap-5 md:grid-cols-2">
              <div>
                <label className="mb-2 block text-sm font-semibold text-sidebar">
                  Department
                  <span className="ml-1 text-danger">*</span>
                </label>

                <select
                  name="department_id"
                  value={formData.department_id}
                  onChange={handleChange}
                  required
                  className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
                >
                  <option value="">
                    Select department
                  </option>

                  {departments.map((department) => (
                    <option
                      key={department.id}
                      value={department.id}
                    >
                      {department.department_name}
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
                  Assigned Courses
                </label>

                <textarea
                  name="assigned_courses"
                  value={formData.assigned_courses}
                  onChange={handleChange}
                  rows="3"
                  placeholder="Enter assigned course codes or names"
                  className="w-full resize-none rounded-xl border border-border bg-surface px-4 py-3 text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
                />
              </div>
            </div>
          </section>

          {/* Account */}
          <section className="rounded-2xl border border-border bg-surface p-6 shadow-sm">
            <h2 className="font-bold text-text">
              Account
            </h2>

            <p className="mt-1 text-sm text-text-muted">
              Set login credentials for this staff member.
            </p>

            <div className="mt-6">
              <FormField
                label={
                  isEditing
                    ? "New Password"
                    : "Password"
                }
                name="password"
                type="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="Enter password"
                required={!isEditing}
              />

              <p className="mt-2 text-xs text-text-light">
                {isEditing
                  ? "Leave blank to keep the current password."
                  : "The password will be securely hashed before storage."}
              </p>
            </div>
          </section>

          {/* Status */}
          <section className="rounded-2xl border border-border bg-surface p-6 shadow-sm">
            <label className="flex cursor-pointer items-center justify-between gap-4">
              <div>
                <p className="font-semibold text-text">
                  Staff Availability
                </p>

                <p className="mt-1 text-sm text-text-muted">
                  Mark this staff member as available for examination duties.
                </p>
              </div>

              <input
                type="checkbox"
                name="availability"
                checked={formData.availability}
                onChange={handleChange}
                className="h-5 w-5 rounded border-gray-300 accent-sidebar"
              />
            </label>
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
                  ? "Update Staff"
                  : "Save Staff"}
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
        className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
      />
    </div>
  );
}

export default StaffForm;
