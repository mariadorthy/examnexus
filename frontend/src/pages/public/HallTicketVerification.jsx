import { useEffect, useState } from "react";
import { get } from "../../services/api";
import {
  CheckCircle2,
  XCircle,
  ShieldCheck,
  GraduationCap,
  CalendarDays,
  Ticket,
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
            Please wait.
          </p>
        </div>
      </div>
    );
  }

  const valid = result?.valid;

  return (
    <div className="min-h-screen bg-background px-5 py-10">
      <div className="mx-auto max-w-xl">

        {/* BRAND */}
        <div className="mb-8 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-sidebar text-white">
            <ShieldCheck size={28} />
          </div>

          <h1 className="mt-4 text-2xl font-bold text-text">
            ExamNexus
          </h1>

          <p className="mt-1 text-sm text-text-muted">
            Hall Ticket Verification
          </p>
        </div>

        {/* RESULT */}
        <div className="overflow-hidden rounded-3xl border border-border bg-surface shadow-lg">

          <div
            className={`p-7 text-center ${
              valid
                ? "bg-primary/10"
                : "bg-red-50"
            }`}
          >
            {valid ? (
              <CheckCircle2
                size={58}
                className="mx-auto text-green-600"
              />
            ) : (
              <XCircle
                size={58}
                className="mx-auto text-red-600"
              />
            )}

            <h2 className="mt-4 text-2xl font-bold text-text">
              {valid
                ? "Valid Hall Ticket"
                : "Invalid Hall Ticket"}
            </h2>

            <p
              className={`mt-2 text-sm font-medium ${
                valid
                  ? "text-green-700"
                  : "text-red-700"
              }`}
            >
              {result?.message}
            </p>
          </div>

          {result && (
            <div className="p-7">

              {/* STUDENT */}
              <div className="rounded-2xl border border-border bg-background p-5">
                <div className="flex items-center gap-3">
                  <div className="rounded-xl bg-primary/10 p-3">
                    <GraduationCap
                      size={22}
                      className="text-primary"
                    />
                  </div>

                  <div>
                    <p className="text-xs font-medium uppercase tracking-wide text-text-muted">
                      Student
                    </p>

                    <p className="mt-1 text-lg font-bold text-text">
                      {result.student_name || "—"}
                    </p>

                    <p className="mt-1 text-sm text-text-muted">
                      {result.student_code || "—"}
                    </p>
                  </div>
                </div>
              </div>

              {/* EXAMINATION */}
              <div className="mt-4 rounded-2xl border border-border bg-background p-5">
                <div className="flex items-center gap-3">
                  <div className="rounded-xl bg-primary/10 p-3">
                    <CalendarDays
                      size={22}
                      className="text-primary"
                    />
                  </div>

                  <div>
                    <p className="text-xs font-medium uppercase tracking-wide text-text-muted">
                      Examination
                    </p>

                    <p className="mt-1 text-lg font-bold text-text">
                      {result.examination || "—"}
                    </p>

                    <p className="mt-1 text-sm text-text-muted">
                      {result.exam_type || "—"}
                    </p>
                  </div>
                </div>
              </div>

              {/* STATUS */}
              <div className="mt-4 flex items-center justify-between rounded-2xl border border-border bg-background p-5">
                <div className="flex items-center gap-3">
                  <Ticket
                    size={22}
                    className="text-primary"
                  />

                  <span className="font-semibold text-text">
                    Ticket Status
                  </span>
                </div>

                <span
                  className={`rounded-full px-3 py-1 text-xs font-bold ${
                    valid
                      ? "bg-green-100 text-green-700"
                      : "bg-red-100 text-red-700"
                  }`}
                >
                  {result.status || "INVALID"}
                </span>
              </div>

            </div>
          )}
        </div>

        <p className="mt-6 text-center text-xs text-text-muted">
          This verification is provided by ExamNexus.
        </p>

      </div>
    </div>
  );
}

export default HallTicketVerification;