import { useEffect, useState } from "react";
import {
  RefreshCw,
  Sparkles,
  Armchair,
  Users,
  Building2,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";

import { get, post } from "../../../services/api";


function SeatAllocationPanel({
  examinations,
  onMessage,
}) {

  const [selectedExamination, setSelectedExamination] =
    useState("");

  const [seatRows, setSeatRows] = useState([]);

  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (selectedExamination) {
      loadSeats(selectedExamination);
    } else {
      setSeatRows([]);
    }
  }, [selectedExamination]);

  const loadSeats = async (examinationId) => {

    try {
      setLoading(true);

      const data = await get(
        `/allocations/seats/${examinationId}`
      );

      setSeatRows(Array.isArray(data) ? data : []);

    } catch (err) {

      console.error("Seat load error:", err);

      setSeatRows([]);

    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async (force) => {

    if (!selectedExamination) {
      onMessage(
        "Please select an examination first.",
        "error"
      );
      return;
    }

    const confirmed = window.confirm(
      force
        ? "Regenerate seat allocation for this examination? Existing seats will be replaced."
        : "Generate seat allocation for this examination?"
    );

    if (!confirmed) return;

    try {

      setGenerating(true);

      const data = await post(
        `/allocations/seats/generate/${selectedExamination}`,
        { force }
      );

      if (!data.success) {
        throw new Error(
          data.message || "Failed to generate seats."
        );
      }

      onMessage(
        data.message || "Seat allocation generated.",
        "success"
      );

      await loadSeats(selectedExamination);

    } catch (err) {

      onMessage(
        err.message || "Unable to generate seat allocation.",
        "error"
      );

    } finally {
      setGenerating(false);
    }
  };

  // ---------------------------------------------------------
  // GROUP BY TIMETABLE → HALL
  // ---------------------------------------------------------

  const grouped = seatRows.reduce((accumulator, row) => {

    const key = `${row.exam_date}-${row.session}`;

    if (!accumulator[key]) {
      accumulator[key] = {
        exam_date: row.exam_date,
        session: row.session,
        halls: {},
      };
    }

    const hallKey = row.hall_id;

    if (!accumulator[key].halls[hallKey]) {
      accumulator[key].halls[hallKey] = {
        hall: row.hall,
        building_name: row.building_name,
        floor_no: row.floor_no,
        purpose: row.purpose,
        seats: [],
      };
    }

    accumulator[key].halls[hallKey].seats.push(row);

    return accumulator;

  }, {});

  return (
    <section className="space-y-6">

      {/* ============================================= */}
      {/* CONTROLS */}
      {/* ============================================= */}

      <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm md:p-6">

        <div className="grid gap-5 lg:grid-cols-[1fr_auto_auto] lg:items-end">

          <div>

            <label
              htmlFor="seat-examination"
              className="mb-2 block text-sm font-semibold text-sidebar"
            >
              Select Examination
            </label>

            <select
              id="seat-examination"
              value={selectedExamination}
              onChange={(event) =>
                setSelectedExamination(event.target.value)
              }
              className="w-full rounded-xl border border-border bg-surface px-4 py-3.5 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
            >

              <option value="">
                Select an examination
              </option>

              {examinations.map((examination) => (
                <option
                  key={examination.id}
                  value={examination.id}
                >
                  {`Examination #${examination.id} — ${examination.name}`}
                </option>
              ))}

            </select>

          </div>

          <button
            type="button"
            onClick={() => handleGenerate(false)}
            disabled={
              !selectedExamination || generating
            }
            className="flex items-center justify-center gap-2 rounded-xl bg-sidebar px-5 py-3.5 text-sm font-semibold text-white shadow-lg shadow-sidebar/10 transition hover:bg-primary disabled:cursor-not-allowed disabled:opacity-60"
          >

            {generating ? (
              <>
                <RefreshCw size={18} className="animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles size={18} />
                Generate Seats
              </>
            )}

          </button>

          <button
            type="button"
            onClick={() => handleGenerate(true)}
            disabled={
              !selectedExamination || generating
            }
            className="flex items-center justify-center gap-2 rounded-xl border border-border bg-surface px-5 py-3.5 text-sm font-semibold text-sidebar transition hover:border-accent hover:bg-surface-muted disabled:cursor-not-allowed disabled:opacity-60"
          >
            <RefreshCw size={17} />
            Regenerate
          </button>

        </div>

        <p className="mt-4 text-xs text-text-muted">
          Seat allocation uses existing hall allocations.
          Generate hall allocation first if it does not exist.
        </p>

      </div>

      {/* ============================================= */}
      {/* RESULTS */}
      {/* ============================================= */}

      {selectedExamination && (

        <div className="rounded-2xl border border-border bg-surface shadow-sm">

          <div className="flex items-center justify-between border-b border-border p-5 md:p-6">

            <div>
              <h2 className="font-bold text-text">
                Seat Allocation
              </h2>

              <p className="mt-1 text-sm text-text-muted">
                Student → Hall → Seat for every timetable
                slot.
              </p>
            </div>

            <span className="rounded-full bg-accent-light px-3 py-1 text-xs font-semibold text-primary">
              {seatRows.length} seats
            </span>

          </div>

          {loading ? (

            <div className="flex items-center justify-center py-16">

              <RefreshCw
                size={26}
                className="animate-spin text-accent"
              />

              <span className="ml-3 text-sm text-text-muted">
                Loading seat allocation...
              </span>

            </div>

          ) : seatRows.length === 0 ? (

            <div className="px-5 py-14 text-center">

              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-accent-light text-primary">
                <Armchair size={27} />
              </div>

              <h3 className="mt-5 font-bold text-text">
                No seat allocation found
              </h3>

              <p className="mx-auto mt-2 max-w-md text-sm text-text-muted">
                Generate seat allocation after hall
                allocation has been created for this
                examination.
              </p>

            </div>

          ) : (

            <div className="space-y-6 p-5 md:p-6">

              {Object.entries(grouped).map(
                ([slotKey, slotData]) => {

                  const halls = Object.values(slotData.halls);

                  const totalSeats = halls.reduce(
                    (sum, hall) => sum + hall.seats.length,
                    0
                  );

                  return (
                    <div
                      key={slotKey}
                      className="overflow-hidden rounded-2xl border border-border"
                    >

                      <div className="flex flex-col gap-2 border-b border-border bg-surface-muted px-5 py-4 sm:flex-row sm:items-center sm:justify-between">

                        <div>
                          <h3 className="font-bold text-text">
                            {slotData.exam_date}
                            {" — "}
                            {slotData.session}
                          </h3>
                        </div>

                        <div className="flex flex-wrap gap-2">

                          <span className="rounded-full bg-accent-light px-3 py-1 text-xs font-semibold text-primary">
                            {halls.length} halls
                          </span>

                          <span className="rounded-full bg-green-50 px-3 py-1 text-xs font-semibold text-success">
                            {totalSeats} students
                          </span>

                        </div>

                      </div>

                      <div className="divide-y divide-border">

                        {halls.map((hall) => (

                          <div key={hall.hall} className="p-5">

                            <div className="mb-3 flex flex-wrap items-center gap-3">

                              <div className="flex items-center gap-2">

                                <Building2
                                  size={17}
                                  className="text-primary"
                                />

                                <span className="text-sm font-semibold text-text">
                                  {hall.hall}
                                </span>

                              </div>

                              <span className="text-xs text-text-muted">
                                {hall.building_name} • Floor{" "}
                                {hall.floor_no}
                              </span>

                              <span className="rounded-full bg-accent-light px-2.5 py-1 text-[10px] font-semibold text-primary">
                                {hall.purpose}
                              </span>

                              <span className="ml-auto text-xs text-text-muted">
                                {hall.seats.length} seat
                                {hall.seats.length !== 1 ? "s" : ""}
                              </span>

                            </div>

                            <div className="overflow-x-auto">

                              <table className="w-full min-w-[500px]">

                                <thead>

                                  <tr className="border-b border-border">

                                    <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                                      Seat
                                    </th>

                                    <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                                      Student ID
                                    </th>

                                    <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                                      Student Name
                                    </th>

                                  </tr>

                                </thead>

                                <tbody>

                                  {hall.seats.map((seat) => (

                                    <tr
                                      key={seat.id}
                                      className="border-b border-border last:border-0 hover:bg-surface-muted"
                                    >

                                      <td className="px-3 py-2 text-sm font-semibold text-primary">
                                        {seat.seat_number}
                                      </td>

                                      <td className="px-3 py-2 text-sm text-text">
                                        {seat.student_code || "—"}
                                      </td>

                                      <td className="px-3 py-2 text-sm text-text">
                                        {seat.student_name || "—"}
                                      </td>

                                    </tr>

                                  ))}

                                </tbody>

                              </table>

                            </div>

                          </div>

                        ))}

                      </div>

                    </div>
                  );
                }
              )}

            </div>

          )}

        </div>

      )}

    </section>
  );
}

export default SeatAllocationPanel;