import { Filter, RotateCcw } from "lucide-react";

function StaffFilters({
  filters,
  onChange,
  onReset,
  departments,
  designationOptions,
  genderOptions,
}) {
  const activeCount = Object.values(filters).filter(
    (value) => value !== ""
  ).length;

  return (
    <div className="mb-5 rounded-2xl border border-border bg-surface p-4 shadow-sm">

      <div className="mb-4 flex items-center justify-between">

        <div className="flex items-center gap-2">
          <Filter size={17} className="text-text-muted" />

          <h3 className="text-sm font-semibold text-text">
            Filters
          </h3>

          {activeCount > 0 && (
            <span className="rounded-full bg-accent-light px-2 py-0.5 text-xs font-semibold text-primary">
              {activeCount} active
            </span>
          )}
        </div>

        {activeCount > 0 && (
          <button
            type="button"
            onClick={onReset}
            className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold text-text-muted transition hover:bg-surface-muted hover:text-text"
          >
            <RotateCcw size={14} />
            Reset
          </button>
        )}

      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">

        {/* DEPARTMENT */}

        <div>
          <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-text-muted">
            Department
          </label>

          <select
            value={filters.department_id}
            onChange={(event) =>
              onChange("department_id", event.target.value)
            }
            className="w-full rounded-xl border border-border bg-surface-muted px-3 py-2.5 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
          >
            <option value="">All departments</option>

            {departments.map((department) => (
              <option key={department.id} value={department.id}>
                {department.department_name}
              </option>
            ))}
          </select>
        </div>

        {/* DESIGNATION */}

        <div>
          <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-text-muted">
            Designation
          </label>

          <select
            value={filters.designation}
            onChange={(event) =>
              onChange("designation", event.target.value)
            }
            className="w-full rounded-xl border border-border bg-surface-muted px-3 py-2.5 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
          >
            <option value="">All designations</option>

            {designationOptions.map((designation) => (
              <option key={designation} value={designation}>
                {designation}
              </option>
            ))}
          </select>
        </div>

        {/* GENDER */}

        <div>
          <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-text-muted">
            Gender
          </label>

          <select
            value={filters.gender}
            onChange={(event) =>
              onChange("gender", event.target.value)
            }
            className="w-full rounded-xl border border-border bg-surface-muted px-3 py-2.5 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
          >
            <option value="">All genders</option>

            {genderOptions.map((gender) => (
              <option key={gender} value={gender}>
                {gender}
              </option>
            ))}
          </select>
        </div>

        {/* AVAILABILITY */}

        <div>
          <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-text-muted">
            Availability
          </label>

          <select
            value={filters.availability}
            onChange={(event) =>
              onChange("availability", event.target.value)
            }
            className="w-full rounded-xl border border-border bg-surface-muted px-3 py-2.5 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
          >
            <option value="">All</option>
            <option value="true">Available</option>
            <option value="false">Unavailable</option>
          </select>
        </div>

        {/* STATUS */}

        <div>
          <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-text-muted">
            Status
          </label>

          <select
            value={filters.is_active}
            onChange={(event) =>
              onChange("is_active", event.target.value)
            }
            className="w-full rounded-xl border border-border bg-surface-muted px-3 py-2.5 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
          >
            <option value="">All statuses</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
        </div>

      </div>

    </div>
  );
}

export default StaffFilters;