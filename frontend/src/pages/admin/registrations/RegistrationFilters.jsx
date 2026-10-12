import { Filter, RotateCcw } from "lucide-react";

function RegistrationFilters({
  filters,
  onChange,
  onReset,
  examinationOptions,
  statusOptions,
  feeStatusOptions,
  eligibilityOptions,
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

        {/* EXAMINATION */}

        <div>
          <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-text-muted">
            Examination
          </label>

          <select
            value={filters.examination_id}
            onChange={(event) =>
              onChange("examination_id", event.target.value)
            }
            className="w-full rounded-xl border border-border bg-surface-muted px-3 py-2.5 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
          >
            <option value="">All examinations</option>

            {examinationOptions.map((examination) => (
              <option
                key={examination.id}
                value={examination.id}
              >
                {examination.label}
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
            value={filters.status}
            onChange={(event) =>
              onChange("status", event.target.value)
            }
            className="w-full rounded-xl border border-border bg-surface-muted px-3 py-2.5 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
          >
            <option value="">All statuses</option>

            {statusOptions.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </div>

        {/* FEE STATUS */}

        <div>
          <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-text-muted">
            Fee Status
          </label>

          <select
            value={filters.fee_status}
            onChange={(event) =>
              onChange("fee_status", event.target.value)
            }
            className="w-full rounded-xl border border-border bg-surface-muted px-3 py-2.5 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
          >
            <option value="">All</option>

            {feeStatusOptions.map((feeStatus) => (
              <option key={feeStatus} value={feeStatus}>
                {feeStatus}
              </option>
            ))}
          </select>
        </div>

        {/* ELIGIBILITY */}

        <div>
          <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-text-muted">
            Eligibility
          </label>

          <select
            value={filters.eligibility}
            onChange={(event) =>
              onChange("eligibility", event.target.value)
            }
            className="w-full rounded-xl border border-border bg-surface-muted px-3 py-2.5 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
          >
            <option value="">All</option>

            {eligibilityOptions.map((eligibility) => (
              <option key={eligibility} value={eligibility}>
                {eligibility}
              </option>
            ))}
          </select>
        </div>

      </div>

    </div>
  );
}

export default RegistrationFilters;