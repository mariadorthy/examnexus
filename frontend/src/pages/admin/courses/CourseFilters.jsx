import { Filter, RotateCcw } from "lucide-react";

function CourseFilters({
  filters,
  onChange,
  onReset,
  departments,
  programLevelOptions,
  studyShiftOptions,
  sessionOptions,
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
                {department.department_code} — {department.department_name}
              </option>
            ))}
          </select>
        </div>

        {/* PROGRAM LEVEL */}

        <div>
          <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-text-muted">
            Program Level
          </label>

          <select
            value={filters.program_level}
            onChange={(event) =>
              onChange("program_level", event.target.value)
            }
            className="w-full rounded-xl border border-border bg-surface-muted px-3 py-2.5 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
          >
            <option value="">All levels</option>

            {programLevelOptions.map((level) => (
              <option key={level} value={level}>
                {level}
              </option>
            ))}
          </select>
        </div>

        {/* STUDY SHIFT */}

        <div>
          <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-text-muted">
            Study Shift
          </label>

          <select
            value={filters.study_shift}
            onChange={(event) =>
              onChange("study_shift", event.target.value)
            }
            className="w-full rounded-xl border border-border bg-surface-muted px-3 py-2.5 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
          >
            <option value="">All shifts</option>

            {studyShiftOptions.map((shift) => (
              <option key={shift} value={shift}>
                {shift}
              </option>
            ))}
          </select>
        </div>

        {/* SESSION */}

        <div>
          <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-text-muted">
            Session
          </label>

          <select
            value={filters.session}
            onChange={(event) =>
              onChange("session", event.target.value)
            }
            className="w-full rounded-xl border border-border bg-surface-muted px-3 py-2.5 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
          >
            <option value="">All sessions</option>

            {sessionOptions.map((session) => (
              <option key={session} value={session}>
                {session}
              </option>
            ))}
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

export default CourseFilters;