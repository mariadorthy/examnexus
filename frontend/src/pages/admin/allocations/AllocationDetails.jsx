import {
  X,
  ClipboardList,
  Users,
  Building2,
  Armchair,
} from "lucide-react";

function AllocationDetails({
  examination,
  allocations,
  onClose,
}) {
  if (!examination) {
    return null;
  }

const hallGroups = allocations.reduce(
  (groups, allocation) => {
    const key = `${allocation.exam_date || "unknown"}-${allocation.session || "unknown"}`;

    if (!groups[key]) {
      groups[key] = [];
    }

    groups[key].push(allocation);

    return groups;
  },
  {}
);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm">

      <div className="flex max-h-[90vh] w-full max-w-6xl flex-col overflow-hidden rounded-2xl bg-surface shadow-2xl">

        {/* ================================================= */}
        {/* HEADER */}
        {/* ================================================= */}

        <header className="flex items-center justify-between border-b border-border px-5 py-4 md:px-6">

          <div className="flex items-center gap-3">

            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-light text-primary">
              <ClipboardList size={21} />
            </div>

            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-accent">
                Allocation Details
              </p>

              <h2 className="text-lg font-bold text-text">
                Examination #{examination.id}
              </h2>
            </div>

          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 text-text-muted transition hover:bg-surface-muted hover:text-text"
            aria-label="Close allocation details"
          >
            <X size={22} />
          </button>

        </header>

        {/* ================================================= */}
        {/* EXAM INFO */}
        {/* ================================================= */}

        <div className="border-b border-border bg-surface-muted px-5 py-4 md:px-6">

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">

<InfoCard
  icon={ClipboardList}
  label="Examination"
  value={examination.name}
/>

<InfoCard
  icon={Users}
  label="Eligible Students"
  value={allocations.length > 0 ? "Available" : "—"}
/>

<InfoCard
  icon={Building2}
  label="Hall Records"
  value={allocations.length}
/>

<InfoCard
  icon={Armchair}
  label="Allocated Capacity"
  value={allocations.reduce(
    (total, allocation) =>
      total + (allocation.allocated_capacity || 0),
    0
  )}
/>

          </div>

        </div>

        {/* ================================================= */}
        {/* CONTENT */}
        {/* ================================================= */}

        <div className="overflow-y-auto p-5 md:p-6">

          {allocations.length === 0 ? (
            <div className="py-12 text-center">

              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-accent-light text-primary">
                <Armchair size={27} />
              </div>

              <h3 className="mt-4 font-bold text-text">
  No hall allocation records
</h3>

<p className="mt-2 text-sm text-text-muted">
  No examination halls have been allocated
  to this examination yet.
</p>

            </div>
          ) : (
            <div className="space-y-6">

             <div className="space-y-6">

  {Object.entries(hallGroups).map(
    ([slotKey, slotAllocations]) => {

      const firstAllocation = slotAllocations[0];

      return (
        <section
          key={slotKey}
          className="overflow-hidden rounded-2xl border border-border"
        >

          {/* Timetable Slot Header */}

          <div className="border-b border-border bg-surface-muted px-5 py-4">

            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">

              <div>
                <h3 className="font-bold text-text">
                  {firstAllocation.exam_date || "Unknown Date"}
                  {" — "}
                  {firstAllocation.session || "Unknown Session"}
                </h3>

                <p className="mt-1 text-xs text-text-muted">
                  {firstAllocation.start_time || "—"}
                  {" - "}
                  {firstAllocation.end_time || "—"}
                </p>
              </div>

              <span className="w-fit rounded-full bg-accent-light px-3 py-1 text-xs font-semibold text-primary">
                {slotAllocations.length} halls
              </span>

            </div>

          </div>

          {/* Hall Allocations */}

          <div className="overflow-x-auto">

            <table className="w-full min-w-[850px]">

              <thead>
                <tr className="border-b border-border">

                  <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Hall
                  </th>

                  <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Building
                  </th>

                  <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Floor
                  </th>

                  <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Hall Capacity
                  </th>

                  <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Allocated Capacity
                  </th>

                  <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Purpose
                  </th>

                  <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Status
                  </th>

                </tr>
              </thead>

              <tbody>

                {slotAllocations.map(
                  (allocation) => (
                    <tr
                      key={allocation.id}
                      className="border-b border-border last:border-0 hover:bg-surface-muted"
                    >

                      <td className="px-5 py-4 text-sm font-semibold text-text">
                        {allocation.hall || "Unknown Hall"}
                      </td>

                      <td className="px-5 py-4 text-sm text-text">
                        {allocation.building_name || "—"}
                      </td>

                      <td className="px-5 py-4 text-sm text-text">
                        {allocation.floor_no ?? "—"}
                      </td>

                      <td className="px-5 py-4 text-sm text-text">
                        {allocation.examination_capacity ?? 0}
                      </td>

                      <td className="px-5 py-4 text-sm font-semibold text-primary">
                        {allocation.allocated_capacity ?? 0}
                      </td>

                      <td className="px-5 py-4">

                        <span className="inline-flex rounded-full bg-accent-light px-3 py-1 text-xs font-semibold text-primary">
                          {allocation.purpose || "NORMAL"}
                        </span>

                      </td>

                      <td className="px-5 py-4">

                        <span className="inline-flex rounded-full bg-green-50 px-3 py-1 text-xs font-semibold text-success">
                          {allocation.status}
                        </span>

                      </td>

                    </tr>
                  )
                )}

              </tbody>

            </table>

          </div>

        </section>
      );
    }
  )}

</div>

            </div>
          )}

        </div>

        {/* ================================================= */}
        {/* FOOTER */}
        {/* ================================================= */}

        <footer className="flex justify-end border-t border-border bg-surface-muted px-5 py-4 md:px-6">

          <button
            type="button"
            onClick={onClose}
            className="rounded-xl bg-sidebar px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-primary"
          >
            Close
          </button>

        </footer>

      </div>

    </div>
  );
}

/* ================================================= */
/* INFO CARD */
/* ================================================= */

function InfoCard({
  icon: Icon,
  label,
  value,
}) {
  return (
    <div className="flex items-center gap-3 rounded-xl bg-surface p-3 shadow-sm">

      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent-light text-primary">
        <Icon size={17} />
      </div>

      <div className="min-w-0">

        <p className="text-xs text-text-light">
          {label}
        </p>

        <p className="truncate text-sm font-semibold text-text">
          {value}
        </p>

      </div>

    </div>
  );
}

export default AllocationDetails;
