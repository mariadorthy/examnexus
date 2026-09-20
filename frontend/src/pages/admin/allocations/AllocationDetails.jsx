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

  const halls = {};

  allocations.forEach((allocation) => {
    const hallName = allocation.hall || "Unknown Hall";

    if (!halls[hallName]) {
      halls[hallName] = [];
    }

    halls[hallName].push(allocation);
  });

  const hallGroups = Object.entries(halls);

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
              label="Date"
              value={examination.exam_date}
            />

            <InfoCard
              icon={ClipboardList}
              label="Session"
              value={examination.session}
            />

            <InfoCard
              icon={Users}
              label="Students"
              value={allocations.length}
            />

            <InfoCard
              icon={Building2}
              label="Halls"
              value={hallGroups.length}
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
                No allocation records
              </h3>

              <p className="mt-2 text-sm text-text-muted">
                There are no students allocated to
                this examination.
              </p>

            </div>
          ) : (
            <div className="space-y-6">

              {hallGroups.map(
                ([hallName, hallAllocations]) => (
                  <section
                    key={hallName}
                    className="overflow-hidden rounded-2xl border border-border"
                  >

                    {/* Hall Header */}

                    <div className="flex flex-col gap-2 border-b border-border bg-surface-muted px-5 py-4 sm:flex-row sm:items-center sm:justify-between">

                      <div className="flex items-center gap-3">

                        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-light text-primary">
                          <Building2 size={19} />
                        </div>

                        <div>
                          <h3 className="font-bold text-text">
                            {hallName}
                          </h3>

                          <p className="text-xs text-text-muted">
                            {hallAllocations.length}{" "}
                            student
                            {hallAllocations.length !==
                            1
                              ? "s"
                              : ""}{" "}
                            allocated
                          </p>
                        </div>

                      </div>

                      <span className="w-fit rounded-full bg-accent-light px-3 py-1 text-xs font-semibold text-primary">
                        {hallAllocations.length} seats
                      </span>

                    </div>

                    {/* Students */}

                    <div className="overflow-x-auto">

                      <table className="w-full min-w-[600px]">

                        <thead>
                          <tr className="border-b border-border">

                            <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                              #
                            </th>

                            <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                              Student ID
                            </th>

                            <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                              Student Name
                            </th>

                            <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                              Seat
                            </th>

                            <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                              Status
                            </th>

                          </tr>
                        </thead>

                        <tbody>

                          {hallAllocations.map(
                            (
                              allocation,
                              index
                            ) => (
                              <tr
                                key={allocation.id}
                                className="border-b border-border last:border-0 hover:bg-surface-muted"
                              >

                                <td className="px-5 py-3.5 text-sm text-text-muted">
                                  {index + 1}
                                </td>

                                <td className="px-5 py-3.5 text-sm font-semibold text-sidebar">
                                  {
                                    allocation.student_id
                                  }
                                </td>

                                <td className="px-5 py-3.5 text-sm text-text">
                                  {
                                    allocation.student_name
                                  }
                                </td>

                                <td className="px-5 py-3.5">

                                  <span className="inline-flex items-center gap-1.5 rounded-lg bg-accent-light px-3 py-1.5 text-xs font-bold text-primary">
                                    <Armchair
                                      size={14}
                                    />

                                    {allocation.seat_number ||
                                      "—"}
                                  </span>

                                </td>

                                <td className="px-5 py-3.5">

                                  <span className="rounded-full bg-green-50 px-3 py-1 text-xs font-semibold text-success">
                                    {
                                      allocation.status
                                    }
                                  </span>

                                </td>

                              </tr>
                            )
                          )}

                        </tbody>

                      </table>

                    </div>

                  </section>
                )
              )}

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
