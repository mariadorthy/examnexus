import { useEffect, useState } from "react";

import {
  Ticket,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Search,
} from "lucide-react";

import AdminSidebar from "../../../components/AdminSidebar";
import AdminTopbar from "../../../components/AdminTopbar";

import {
  get,
  post,
} from "../../../services/api";
import {
  getHallTicket,
} from "../../../services/hallTicketService";


function HallTickets({
  user,
  onLogout,
  onNavigate,
}) {
  const [sidebarOpen, setSidebarOpen] =
    useState(false);

  const [examinations, setExaminations] = useState([]);
  const [selectedExamination, setSelectedExamination] =
    useState("");

  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [selectedStudentId, setSelectedStudentId] =
    useState("");
  const [ticket, setTicket] = useState(null);
  const [ticketLoading, setTicketLoading] =
    useState(false);
  const [ticketError, setTicketError] = useState("");

  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    loadExaminations();
  }, []);

  useEffect(() => {
    if (selectedExamination) {
      loadTickets(selectedExamination);
    } else {
      setTickets([]);
      setTicket(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedExamination]);

  const loadExaminations = async () => {
    try {
      const data = await get("/examinations/");
      setExaminations(data || []);
    } catch (err) {
      console.error(err);
      setError("Unable to load examinations.");
    }
  };

  const loadTickets = async (examinationId) => {
    try {
      setLoading(true);
      setError("");
      setSuccess("");
      setTicket(null);
      setSelectedStudentId("");

      // We reuse the reports endpoint for a quick list.
      // It returns students with seats; hall tickets are a
      // subset. We then check ticket existence per row via
      // the single-ticket endpoint on demand.
      const report = await get(
        `/reports/students/${examinationId}`
      );

      // Deduplicate by student_id
      const byStudent = new Map();

      (report?.rows || []).forEach((row) => {
        if (!byStudent.has(row.student_id)) {
          byStudent.set(row.student_id, row);
        }
      });

      setTickets(Array.from(byStudent.values()));
    } catch (err) {
      console.error(err);
      setError(
        err.message || "Unable to load hall tickets."
      );
      setTickets([]);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async (force = false) => {
    if (!selectedExamination) {
      setError("Please select an examination.");
      return;
    }

    const confirmed = window.confirm(
      force
        ? "Reissue hall tickets for all students? Existing verification tokens will be replaced."
        : "Generate hall tickets for all students?"
    );

    if (!confirmed) return;

    try {
      setGenerating(true);
      setError("");
      setSuccess("");

      const data = await post(
        `/hall-tickets/generate/${selectedExamination}`,
        { force }
      );

      if (!data.success) {
        throw new Error(
          data.message ||
            "Failed to generate hall tickets."
        );
      }

      setSuccess(
        data.message ||
          "Hall tickets generated successfully."
      );

      await loadTickets(selectedExamination);
    } catch (err) {
      console.error(err);
      setError(
        err.message ||
          "Unable to generate hall tickets."
      );
    } finally {
      setGenerating(false);
    }
  };

  const handleShowTicket = async (studentId) => {
    if (!selectedExamination) return;

    try {
      setTicketLoading(true);
      setTicketError("");
      setTicket(null);
      setSelectedStudentId(studentId);

      const data = await getHallTicket(
        selectedExamination,
        studentId
      );

      if (!data.success) {
        throw new Error(
          data.message || "Hall ticket not found."
        );
      }

      setTicket(data);
    } catch (err) {
      console.error(err);
      setTicketError(
        err.message ||
          "Unable to load the selected hall ticket."
      );
    } finally {
      setTicketLoading(false);
    }
  };

  const filteredTickets = tickets.filter((row) => {
    if (!searchTerm) return true;

    const term = searchTerm.toLowerCase();

    return (
      String(row.student_code || "")
        .toLowerCase()
        .includes(term) ||
      String(row.student_name || "")
        .toLowerCase()
        .includes(term)
    );
  });

  return (
    <div className="min-h-screen bg-background">

      <AdminSidebar
        user={user}
        onLogout={onLogout}
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        activePage="Hall Tickets"
        onNavigate={onNavigate}
      />

      <main className="lg:ml-72">

        <AdminTopbar
          user={user}
          title="Hall Tickets"
          section="Administration"
          onOpenSidebar={() => setSidebarOpen(true)}
        />

        <div className="p-5 md:p-8">

          {/* HEADER */}

          <section className="mb-8">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">

              <div>
                <p className="text-sm font-semibold uppercase tracking-widest text-accent">
                  Examination Management
                </p>

                <h1 className="mt-1 text-2xl font-bold text-text md:text-3xl">
                  Hall Tickets
                </h1>

                <p className="mt-2 max-w-2xl text-sm leading-6 text-text-muted">
                  Generate and inspect hall tickets for a
                  published examination. Each ticket carries a
                  verification token rendered as a QR code.
                </p>
              </div>

              <button
                type="button"
                onClick={() =>
                  selectedExamination &&
                  loadTickets(selectedExamination)
                }
                disabled={!selectedExamination || loading}
                className="flex w-fit items-center gap-2 rounded-xl border border-border bg-surface px-4 py-2.5 text-sm font-semibold text-sidebar shadow-sm transition hover:border-accent hover:bg-surface-muted disabled:cursor-not-allowed disabled:opacity-60"
              >
                <RefreshCw
                  size={17}
                  className={loading ? "animate-spin" : ""}
                />
                Refresh
              </button>

            </div>
          </section>

          {/* SELECTOR + GENERATE */}

          <section className="mb-6 rounded-2xl border border-border bg-surface p-5 shadow-sm md:p-6">

            <div className="grid gap-5 lg:grid-cols-[1fr_auto] lg:items-end">

              <div>
                <label
                  htmlFor="hall-ticket-examination"
                  className="mb-2 block text-sm font-semibold text-sidebar"
                >
                  Select Examination
                </label>

                <select
                  id="hall-ticket-examination"
                  value={selectedExamination}
                  onChange={(event) =>
                    setSelectedExamination(event.target.value)
                  }
                  className="w-full rounded-xl border border-border bg-surface px-4 py-3.5 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
                >
                  <option value="">
                    Select an examination
                  </option>

                  {examinations.map((exam) => (
                    <option key={exam.id} value={exam.id}>
                      {`Examination #${exam.id}`} —{" "}
                      {exam.name}
                    </option>
                  ))}
                </select>
              </div>

              <button
                type="button"
                onClick={() => handleGenerate(false)}
                disabled={
                  !selectedExamination || generating || loading
                }
                className="flex items-center justify-center gap-2 rounded-xl bg-sidebar px-5 py-3.5 text-sm font-semibold text-white shadow-lg shadow-sidebar/10 transition hover:bg-primary disabled:cursor-not-allowed disabled:opacity-60"
              >
                {generating ? (
                  <>
                    <RefreshCw
                      size={18}
                      className="animate-spin"
                    />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles size={18} />
                    Generate Hall Tickets
                  </>
                )}
              </button>

            </div>

            {selectedExamination && tickets.length > 0 && (
              <div className="mt-4 flex justify-end">
                <button
                  type="button"
                  onClick={() => handleGenerate(true)}
                  disabled={generating}
                  className="text-xs font-semibold text-text-muted underline-offset-4 transition hover:text-primary hover:underline disabled:opacity-50"
                >
                  Force reissue all tickets
                </button>
              </div>
            )}

          </section>

          {/* MESSAGES */}

          {error && (
            <div className="mb-6 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              <AlertCircle size={19} className="mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="mb-6 flex items-start gap-3 rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
              <CheckCircle2 size={19} className="mt-0.5 shrink-0" />
              <span>{success}</span>
            </div>
          )}

          {/* TWO COLUMN LAYOUT */}

          {selectedExamination && (
            <section className="grid gap-6 lg:grid-cols-[1.1fr_1fr]">

              {/* ================= LIST ================= */}

              <div className="rounded-2xl border border-border bg-surface shadow-sm">

                <div className="border-b border-border p-5 md:p-6">

                  <h2 className="font-bold text-text">
                    Eligible Students
                  </h2>

                  <p className="mt-1 text-sm text-text-muted">
                    {filteredTickets.length} student
                    {filteredTickets.length === 1 ? "" : "s"}
                  </p>

                  <div className="mt-4 flex items-center gap-2 rounded-xl border border-border bg-surface px-3 py-2">

                    <Search size={16} className="text-text-muted" />

                    <input
                      type="text"
                      value={searchTerm}
                      onChange={(event) =>
                        setSearchTerm(event.target.value)
                      }
                      placeholder="Search student code or name"
                      className="w-full bg-transparent text-sm text-text outline-none placeholder:text-text-light"
                    />

                  </div>

                </div>

                {loading ? (
                  <div className="flex items-center justify-center py-16">
                    <RefreshCw
                      size={24}
                      className="animate-spin text-accent"
                    />
                    <span className="ml-3 text-sm text-text-muted">
                      Loading...
                    </span>
                  </div>
                ) : filteredTickets.length === 0 ? (
                  <div className="p-10 text-center">
                    <Ticket
                      size={28}
                      className="mx-auto text-text-muted"
                    />
                    <p className="mt-3 font-semibold text-text">
                      No students available
                    </p>
                    <p className="mt-1 text-sm text-text-muted">
                      This examination has no eligible seat
                      allocations yet.
                    </p>
                  </div>
                ) : (
                  <div className="max-h-[560px] overflow-y-auto">

                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-border bg-surface-muted">
                          <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                            Code
                          </th>
                          <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                            Name
                          </th>
                          <th className="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-text-muted">
                            Action
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredTickets.map((row) => {
                          const isSelected =
                            String(row.student_id) ===
                            String(selectedStudentId);

                          return (
                            <tr
                              key={row.student_id}
                              className={`border-b border-border last:border-0 ${
                                isSelected
                                  ? "bg-accent-light"
                                  : "hover:bg-surface-muted"
                              }`}
                            >
                              <td className="px-5 py-3 text-sm font-semibold text-sidebar">
                                {row.student_code}
                              </td>
                              <td className="px-5 py-3 text-sm text-text">
                                {row.student_name}
                              </td>
                              <td className="px-5 py-3 text-right">
                                <button
                                  type="button"
                                  onClick={() =>
                                    handleShowTicket(row.student_id)
                                  }
                                  className="rounded-lg border border-border px-3 py-1.5 text-xs font-semibold text-sidebar transition hover:border-accent hover:bg-accent-light"
                                >
                                  View Ticket
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>

                  </div>
                )}

              </div>

              {/* ================= PREVIEW ================= */}

              <div className="rounded-2xl border border-border bg-surface shadow-sm">

                <div className="border-b border-border p-5 md:p-6">
                  <h2 className="font-bold text-text">
                    Hall Ticket Preview
                  </h2>
                  <p className="mt-1 text-sm text-text-muted">
                    Select a student to preview their ticket.
                  </p>
                </div>

                {!selectedStudentId ? (
                  <div className="p-10 text-center">
                    <Ticket
                      size={28}
                      className="mx-auto text-text-muted"
                    />
                    <p className="mt-3 font-semibold text-text">
                      No ticket selected
                    </p>
                    <p className="mt-1 text-sm text-text-muted">
                      Click View Ticket on a student row.
                    </p>
                  </div>
                ) : ticketLoading ? (
                  <div className="flex items-center justify-center py-16">
                    <RefreshCw
                      size={24}
                      className="animate-spin text-accent"
                    />
                    <span className="ml-3 text-sm text-text-muted">
                      Loading ticket...
                    </span>
                  </div>
                ) : ticketError ? (
                  <div className="p-6">
                    <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                      <AlertCircle size={19} className="mt-0.5 shrink-0" />
                      <span>{ticketError}</span>
                    </div>
                  </div>
                ) : ticket ? (
                  <div className="p-5 md:p-6">

                    <div className="flex flex-col gap-5 md:flex-row">

                      <div className="flex-1">

                        <p className="text-lg font-bold text-text">
                          {ticket.payload.student.name}
                        </p>

                        <p className="text-sm text-text-muted">
                          {ticket.payload.student.student_id}
                        </p>

                        <div className="mt-4 space-y-1.5 text-sm text-text">
                          <p>
                            <span className="font-semibold">
                              Examination:{" "}
                            </span>
                            {ticket.payload.examination.name}
                          </p>
                          <p>
                            <span className="font-semibold">
                              Type:{" "}
                            </span>
                            {ticket.payload.examination.exam_type}
                          </p>
                          <p>
                            <span className="font-semibold">
                              Semester:{" "}
                            </span>
                            {ticket.payload.examination.semester}
                          </p>
                        </div>

                      </div>

                      <div className="flex flex-col items-center justify-center">

                        <img
                          src={`data:image/png;base64,${ticket.ticket.qr_base64}`}
                          alt="QR code"
                          className="h-32 w-32 rounded-lg border border-border bg-white p-2"
                        />

                        <p className="mt-2 break-all text-[10px] text-text-light">
                          {ticket.ticket.verification_token}
                        </p>

                      </div>

                    </div>

                    <div className="mt-6">

                      <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-text-muted">
                        Examination Entries
                      </p>

                      <div className="overflow-hidden rounded-xl border border-border">

                        <table className="w-full">
                          <thead>
                            <tr className="border-b border-border bg-surface-muted">
                              <th className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wider text-text-muted">
                                Date
                              </th>
                              <th className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wider text-text-muted">
                                Session
                              </th>
                              <th className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wider text-text-muted">
                                Hall
                              </th>
                              <th className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wider text-text-muted">
                                Seat
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {ticket.payload.entries.map(
                              (entry, idx) => (
                                <tr
                                  key={idx}
                                  className="border-b border-border last:border-0"
                                >
                                  <td className="px-3 py-2 text-xs text-text">
                                    {entry.exam_date}
                                  </td>
                                  <td className="px-3 py-2 text-xs font-semibold text-sidebar">
                                    {entry.session}
                                  </td>
                                  <td className="px-3 py-2 text-xs text-text">
                                    {entry.hall_name}
                                  </td>
                                  <td className="px-3 py-2 text-xs font-bold text-primary">
                                    {entry.seat_number}
                                  </td>
                                </tr>
                              )
                            )}
                          </tbody>
                        </table>

                      </div>

                    </div>

                    <div className="mt-5 flex justify-end">
                      <button
                        type="button"
                        onClick={() => window.print()}
                        className="rounded-xl border border-border px-4 py-2 text-xs font-semibold text-sidebar transition hover:border-accent hover:bg-surface-muted"
                      >
                        Print this ticket
                      </button>
                    </div>

                  </div>
                ) : null}

              </div>

            </section>
          )}

        </div>

      </main>

    </div>
  );
}


export default HallTickets;