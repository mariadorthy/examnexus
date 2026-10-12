import { Filter, RotateCcw } from "lucide-react";

function SubjectFilters({
  filters,
  onChange,
  onReset,
  courses,
  semesterOptions,
  subjectTypeOptions,
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

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">

        {/* COURSE */}

        <div>
          <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-text-muted">
            Course
          </label>

          <select
            value={filters.course_id}
            onChange={(event) =>
              onChange("course_id", event.target.value)
            }
            className="w-full rounded-xl border border-border bg-surface-muted px-3 py-2.5 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
          >
            <option value="">All courses</option>

            {courses.map((course) => (
              <option key={course.id} value={course.id}>
                {course.course_code} — {course.course_name}
              </option>
            ))}
          </select>
        </div>

        {/* SEMESTER */}

        <div>
          <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-text-muted">
            Semester
          </label>

          <select
            value={filters.semester}
            onChange={(event) =>
              onChange("semester", event.target.value)
            }
            className="w-full rounded-xl border border-border bg-surface-muted px-3 py-2.5 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
          >
            <option value="">All semesters</option>

            {semesterOptions.map((semester) => (
              <option key={semester} value={semester}>
                Semester {semester}
              </option>
            ))}
          </select>
        </div>

        {/* SUBJECT TYPE */}

        <div>
          <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-text-muted">
            Type
          </label>

          <select
            value={filters.subject_type}
            onChange={(event) =>
              onChange("subject_type", event.target.value)
            }
            className="w-full rounded-xl border border-border bg-surface-muted px-3 py-2.5 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
          >
            <option value="">All types</option>

            {subjectTypeOptions.map((type) => (
              <option key={type} value={type}>
                {type}
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

export default SubjectFilters;