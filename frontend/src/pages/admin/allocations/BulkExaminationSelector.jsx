import { useMemo, useState } from "react";
import {
  ClipboardList,
  RefreshCw,
  Search,
  X,
} from "lucide-react";


function BulkExaminationSelector({
  examinations,
  selectedBulkExaminations,
  onToggle,
  onSelectAll,
  loading,
  disabled,
  showStatusFilter = false,
}) {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const allSelected =
    examinations.length > 0 &&
    selectedBulkExaminations.length === examinations.length;

  const statusOptions = useMemo(() => {
    const fromData = [
      ...new Set(
        examinations
          .map((e) => e.status)
          .filter(Boolean)
      ),
    ];
    return fromData.length
      ? fromData.sort()
      : [
          "DRAFT",
          "GENERATED",
          "VALIDATED",
          "REVIEW",
          "APPROVED",
          "PUBLISHED",
        ];
  }, [examinations]);

  const filteredExaminations = useMemo(() => {
    const searchText = search.trim().toLowerCase();

    return examinations.filter((examination) => {
      if (
        statusFilter &&
        examination.status !== statusFilter
      ) {
        return false;
      }

      if (!searchText) {
        return true;
      }

      const haystack = [
        `Examination #${examination.id}`,
        examination.name,
        examination.course_name,
        examination.course_code,
        examination.exam_type,
        examination.status,
        examination.semester !== undefined &&
        examination.semester !== null
          ? `Semester ${examination.semester}`
          : "",
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      return haystack.includes(searchText);
    });
  }, [examinations, search, statusFilter]);

  const hasActiveFilters = Boolean(search || statusFilter);

  return (
    <section className="mb-6 rounded-2xl border border-border bg-surface p-5 shadow-sm md:p-6">

      <div className="flex flex-col gap-4 border-b border-border pb-5 md:flex-row md:items-center md:justify-between">

        <div>
          <p className="text-sm font-semibold uppercase tracking-wider text-accent">
            Bulk Allocation
          </p>

          <h2 className="mt-1 text-lg font-bold text-text">
            Allocate Multiple Examinations
          </h2>

          <p className="mt-1 max-w-2xl text-sm leading-6 text-text-muted">
            Select multiple examinations to run bulk
            actions. The selection is shared across all
            allocation tabs.
          </p>
        </div>

        <button
          type="button"
          onClick={onSelectAll}
          disabled={
            loading ||
            examinations.length === 0 ||
            disabled
          }
          className="w-fit rounded-xl border border-border px-4 py-2.5 text-sm font-semibold text-sidebar transition hover:border-accent hover:bg-surface-muted disabled:cursor-not-allowed disabled:opacity-50"
        >
          {allSelected ? "Clear All" : "Select All"}
        </button>

      </div>

      {loading ? (
        <div className="flex items-center justify-center py-10">
          <RefreshCw
            size={24}
            className="animate-spin text-accent"
          />
          <span className="ml-3 text-sm text-text-muted">
            Loading examinations...
          </span>
        </div>
      ) : examinations.length === 0 ? (
        <div className="py-10 text-center">
          <ClipboardList
            size={28}
            className="mx-auto text-text-muted"
          />
          <p className="mt-3 text-sm font-semibold text-text">
            No examinations available
          </p>
          <p className="mt-1 text-sm text-text-muted">
            Create an examination before running bulk
            actions.
          </p>
        </div>
      ) : (
        <>
          {/* FILTERS */}

          <div className="mt-5 flex flex-wrap items-end gap-3">

            <div className="relative min-w-[260px] flex-1">

              <Search
                size={18}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-text-light"
              />

              <input
                type="text"
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
                placeholder="Search examinations by name, course, type, semester..."
                className="w-full rounded-xl border border-border bg-surface-muted py-2.5 pl-10 pr-10 text-sm text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
              />

              {search && (
                <button
                  type="button"
                  onClick={() => setSearch("")}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-light hover:text-text"
                  aria-label="Clear search"
                >
                  <X size={16} />
                </button>
              )}

            </div>

            {showStatusFilter && (
              <div>
                <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-text-muted">
                  Status
                </label>
                <select
                  value={statusFilter}
                  onChange={(event) =>
                    setStatusFilter(event.target.value)
                  }
                  className="rounded-xl border border-border bg-surface-muted px-3 py-2.5 text-sm text-text outline-none focus:border-primary"
                >
                  <option value="">All statuses</option>
                  {statusOptions.map((status) => (
                    <option key={status} value={status}>
                      {status}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {hasActiveFilters && (
              <button
                type="button"
                onClick={() => {
                  setSearch("");
                  setStatusFilter("");
                }}
                className="rounded-xl px-3 py-2.5 text-xs font-semibold text-text-muted hover:bg-surface-muted hover:text-text"
              >
                Reset
              </button>
            )}

          </div>

          {filteredExaminations.length === 0 ? (
            <div className="mt-5 rounded-xl border border-dashed border-border bg-surface-muted py-8 text-center">
              <p className="text-sm font-semibold text-text">
                No matching examinations
              </p>
              <p className="mt-1 text-xs text-text-muted">
                Try a different search term or clear the status filter.
              </p>
            </div>
          ) : (
            <div className="mt-5 grid gap-3 md:grid-cols-2">

              {filteredExaminations.map((examination) => {
                const examinationId = String(examination.id);
                const isSelected =
                  selectedBulkExaminations.includes(
                    examinationId
                  );

                return (
                  <label
                    key={examination.id}
                    className={`flex cursor-pointer items-start gap-3 rounded-xl border p-4 transition ${
                      isSelected
                        ? "border-primary bg-accent-light"
                        : "border-border hover:border-accent hover:bg-surface-muted"
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() =>
                        onToggle(examinationId)
                      }
                      disabled={disabled}
                      className="mt-1 h-4 w-4 accent-primary"
                    />

                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-text">
                        {`Examination #${examination.id}`}
                      </p>

                      <p className="mt-1 truncate text-sm text-text-muted">
                        {examination.name}
                      </p>

                      <div className="mt-2 flex flex-wrap gap-2">
                        <span className="rounded-full bg-surface-muted px-2.5 py-1 text-xs font-medium text-text-muted">
                          {examination.course_name ||
                            "Course —"}
                        </span>
                        <span className="rounded-full bg-surface-muted px-2.5 py-1 text-xs font-medium text-text-muted">
                          Semester {examination.semester ?? "—"}
                        </span>
                        <span className="rounded-full bg-surface-muted px-2.5 py-1 text-xs font-medium text-text-muted">
                          {examination.status || "—"}
                        </span>
                      </div>
                    </div>
                  </label>
                );
              })}

            </div>
          )}

          <div className="mt-5 rounded-xl bg-surface-muted p-4">
            <p className="text-sm font-semibold text-text">
              {selectedBulkExaminations.length} examination
              {selectedBulkExaminations.length !== 1
                ? "s"
                : ""}{" "}
              selected
            </p>
            <p className="mt-1 text-xs text-text-muted">
              Only examinations with valid timetable entries
              and eligible students can be allocated.
            </p>
          </div>
        </>
      )}

    </section>
  );
}


export default BulkExaminationSelector;