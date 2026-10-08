import { useEffect, useState } from "react";
import { get } from "../../services/api";
import {
  CheckCircle2,
  XCircle,
  ShieldCheck,
  GraduationCap,
  BookOpen,
  CalendarDays,
  Ticket,
  MapPin,
  Clock3,
  Loader2,
} from "lucide-react";

function HallTicketVerification() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);

  const token = window.location.pathname
    .split("/")
    .filter(Boolean)
    .pop();

  useEffect(() => {
    const verifyTicket = async () => {
      if (!token) {
        setResult({
          valid: false,
          message: "Invalid verification link.",
        });
        setLoading(false);
        return;
      }

      try {
        const data = await get(
          `/hall-tickets/verify/${token}`
        );

        setResult(data);
      } catch (error) {
        setResult({
          valid: false,
          message:
            error.message ||
            "Unable to verify hall ticket.",
        });
      } finally {
        setLoading(false);
      }
    };

    verifyTicket();
  }, [token]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background px-6">
        <div className="text-center">
          <Loader2
            size={42}
            className="mx-auto animate-spin text-primary"
          />

          <p className="mt-4 font-semibold text-text">
            Verifying hall ticket...
          </p>

          <p className="mt-1 text-sm text-text-muted">
            Authenticating examination credentials.
          </p>
        </div>
      </div>
    );
  }

  const valid = result?.valid;
  const timetable = result?.timetable || [];

  return (
    <div className="min-h-screen bg-background px-5 py-8 md:px-8 md:py-10">
      <div className="mx-auto max-w-5xl">

        {/* BRAND */}
        <header className="mb-8 text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-sidebar text-white shadow-sm">
            <ShieldCheck size={30} />
          </div>

          <h1 className="mt-4 text-3xl font-bold text-text">
            ExamNexus
          </h1>

          <p className="mt-1 text-sm text-text-muted">
            Official Hall Ticket Verification
          </p>
        </header>

        {/* VERIFICATION BANNER */}
        <section
          className={`overflow-hidden rounded-3xl border shadow-sm ${
            valid
              ? "border-green-200 bg-green-50"
              : "border-red-200 bg-red-50"
          }`}
        >
          <div className="flex flex-col items-center gap-4 p-7 text-center md:flex-row md:text-left">

            <div
              className={`flex h-16 w-16 shrink-0 items-center justify-center rounded-full ${
                valid
                  ? "bg-green-100"
                  : "bg-red-100"
              }`}
            >
              {valid ? (
                <CheckCircle2
                  size={36}
                  className="text-green-600"
                />
              ) : (
                <XCircle
                  size={36}
                  className="text-red-600"
                />
              )}
            </div>

            <div className="flex-1">
              <p
                className={`text-xs font-bold uppercase tracking-widest ${
                  valid
                    ? "text-green-700"
                    : "text-red-700"
                }`}
              >
                {valid
                  ? "Identity Verified"
                  : "Verification Failed"}
              </p>

              <h2 className="mt-1 text-2xl font-bold text-text">
                {valid
                  ? "Authentic Hall Ticket"
                  : "Invalid Hall Ticket"}
              </h2>

              <p
                className={`mt-1 text-sm ${
                  valid
                    ? "text-green-700"
                    : "text-red-700"
                }`}
              >
                {result?.message}
              </p>
            </div>

            <div
              className={`rounded-full px-4 py-2 text-xs font-bold ${
                valid
                  ? "bg-green-100 text-green-700"
                  : "bg-red-100 text-red-700"
              }`}
            >
              {result?.status || "INVALID"}
            </div>
          </div>
        </section>

        {/* STUDENT IDENTITY */}
        {result && (
          <section className="mt-6 rounded-2xl border border-border bg-surface p-6 shadow-sm">

            <div className="flex items-center gap-3">

              <div className="rounded-xl bg-primary/10 p-3">
                <GraduationCap
                  size={22}
                  className="text-primary"
                />
              </div>

              <div>
                <h2 className="text-lg font-bold text-text">
                  Student Identity
                </h2>

                <p className="text-sm text-text-muted">
                  Verified examination candidate
                </p>
              </div>

            </div>

            <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">

              <div>
                <p className="text-xs uppercase tracking-wide text-text-muted">
                  Full Name
                </p>

                <p className="mt-1 font-semibold text-text">
                  {result.student_name || "—"}
                </p>
              </div>

              <div>
                <p className="text-xs uppercase tracking-wide text-text-muted">
                  Student ID
                </p>

                <p className="mt-1 font-semibold text-text">
                  {result.student_code || "—"}
                </p>
              </div>

              <div>
                <p className="text-xs uppercase tracking-wide text-text-muted">
                  Semester
                </p>

                <p className="mt-1 font-semibold text-text">
                  {result.student_semester ?? "—"}
                </p>
              </div>

              <div>
                <p className="text-xs uppercase tracking-wide text-text-muted">
                  Batch
                </p>

                <p className="mt-1 font-semibold text-text">
                  {result.student_batch || "—"}
                </p>
              </div>

            </div>
          </section>
        )}

        {/* EXAMINATION */}
        {result && (
          <section className="mt-6 rounded-2xl border border-border bg-surface p-6 shadow-sm">

            <div className="flex items-center gap-3">

              <div className="rounded-xl bg-primary/10 p-3">
                <BookOpen
                  size={22}
                  className="text-primary"
                />
              </div>

              <div>
                <h2 className="text-lg font-bold text-text">
                  Examination
                </h2>

                <p className="text-sm text-text-muted">
                  Official examination information
                </p>
              </div>

            </div>

            <div className="mt-6 grid gap-5 sm:grid-cols-2">

              <div>
                <p className="text-xs uppercase tracking-wide text-text-muted">
                  Examination
                </p>

                <p className="mt-1 text-lg font-bold text-text">
                  {result.examination || "—"}
                </p>
              </div>

              <div>
                <p className="text-xs uppercase tracking-wide text-text-muted">
                  Examination Type
                </p>

                <p className="mt-1 font-semibold text-text">
                  {result.exam_type || "—"}
                </p>
              </div>

            </div>
          </section>
        )}

        {/* EXAMINATION TIMETABLE */}
        {valid && (
          <section className="mt-6 rounded-2xl border border-border bg-surface shadow-sm">

            <div className="border-b border-border p-6">

              <div className="flex items-center gap-3">

                <div className="rounded-xl bg-primary/10 p-3">
                  <CalendarDays
                    size={21}
                    className="text-primary"
                  />
                </div>

                <div>
                  <h2 className="text-lg font-bold text-text">
                    Examination Timetable
                  </h2>

                  <p className="text-sm text-text-muted">
                    Verified examination schedule
                  </p>
                </div>

              </div>

            </div>

            <div className="p-6">

              {timetable.length > 0 ? (

                <div className="grid gap-5 lg:grid-cols-2">

                  {timetable.map((exam) => (

                    <div
                      key={exam.timetable_id}
                      className="rounded-2xl border border-border bg-background p-5 transition hover:shadow-md"
                    >

                      <div className="flex items-start justify-between gap-4">

                        <div>
                          <h3 className="text-lg font-bold text-text">
                            {exam.subject_name || "Subject"}
                          </h3>

                          <p className="mt-1 text-sm text-text-muted">
                            {exam.subject_code || "—"}
                          </p>
                        </div>

                        <span className="shrink-0 rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
                          {exam.session || "—"}
                        </span>

                      </div>

                      <div className="mt-5 grid gap-4 sm:grid-cols-2">

                        <div className="flex items-start gap-3">
                          <CalendarDays
                            size={18}
                            className="mt-0.5 text-primary"
                          />

                          <div>
                            <p className="text-xs uppercase tracking-wide text-text-muted">
                              Date
                            </p>

                            <p className="mt-1 font-semibold text-text">
                              {exam.exam_date || "—"}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-start gap-3">
                          <Clock3
                            size={18}
                            className="mt-0.5 text-primary"
                          />

                          <div>
                            <p className="text-xs uppercase tracking-wide text-text-muted">
                              Time
                            </p>

                            <p className="mt-1 font-semibold text-text">
                              {exam.start_time || "—"} -{" "}
                              {exam.end_time || "—"}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-start gap-3">
                          <MapPin
                            size={18}
                            className="mt-0.5 text-primary"
                          />

                          <div>
                            <p className="text-xs uppercase tracking-wide text-text-muted">
                              Examination Hall
                            </p>

                            <p className="mt-1 font-semibold text-text">
                              {exam.hall_name || "—"}
                            </p>

                            <p className="mt-1 text-sm text-text-muted">
                              {exam.building_name || "—"}
                              {" · "}
                              Floor {exam.floor_no ?? "—"}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-start gap-3">
                          <Ticket
                            size={18}
                            className="mt-0.5 text-primary"
                          />

                          <div>
                            <p className="text-xs uppercase tracking-wide text-text-muted">
                              Assigned Seat
                            </p>

                            <p className="mt-1 text-lg font-bold text-primary">
                              {exam.seat_number || "—"}
                            </p>

                            {exam.row_label && (
                              <p className="mt-1 text-sm text-text-muted">
                                Row {exam.row_label}
                              </p>
                            )}
                          </div>
                        </div>

                      </div>

                    </div>

                  ))}

                </div>

              ) : (

                <div className="rounded-xl border border-dashed border-border p-10 text-center">

                  <CalendarDays
                    size={30}
                    className="mx-auto text-text-muted"
                  />

                  <p className="mt-3 font-semibold text-text">
                    No timetable entries available
                  </p>

                </div>

              )}

            </div>
          </section>
        )}

        {/* VERIFICATION FOOTER */}
        <div className="mt-8 rounded-2xl border border-border bg-surface p-5 text-center shadow-sm">

          <div className="flex items-center justify-center gap-2">

            <ShieldCheck
              size={18}
              className={
                valid
                  ? "text-green-600"
                  : "text-red-600"
              }
            />

            <p className="text-sm font-semibold text-text">
              {valid
                ? "This hall ticket has been verified by ExamNexus."
                : "This hall ticket could not be verified."}
            </p>

          </div>

          <p className="mt-2 text-xs text-text-muted">
            Public read-only verification · No login required
          </p>

        </div>

      </div>
    </div>
  );
}

export default HallTicketVerification;