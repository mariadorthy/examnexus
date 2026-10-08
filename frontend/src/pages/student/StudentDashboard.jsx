import { useEffect, useState } from "react";
import { get } from "../../services/api";
import {
  GraduationCap,
  BookOpen,
  CalendarDays,
  User,
  Mail,
  LogOut,
} from "lucide-react";

function StudentDashboard({
  user,
  onLogout,
}) {
  const [dashboardUser, setDashboardUser] =
    useState(user);
  const [loading, setLoading] =
    useState(true);
  const [error, setError] =
    useState("");

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        setLoading(true);
        setError("");

        const data = await get(
          "/dashboard/student"
        );

        setDashboardUser(data.user);
      } catch (error) {
        console.error(
          "Student dashboard error:",
          error
        );

        setError(
          error.message ||
            "Failed to load student dashboard."
        );
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <div className="flex min-h-screen items-center justify-center">
          <p className="text-text-muted">
            Loading dashboard...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background">
        <div className="flex min-h-screen items-center justify-center px-6">
          <div className="w-full max-w-md rounded-2xl border border-border bg-surface p-8 text-center shadow-sm">
            <h2 className="text-xl font-bold text-text">
              Unable to load dashboard
            </h2>

            <p className="mt-3 text-sm text-red-600">
              {error}
            </p>

            <button
              type="button"
              onClick={onLogout}
              className="mt-6 rounded-xl bg-sidebar px-5 py-3 font-semibold text-white"
            >
              Return to Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* HEADER */}
      <header className="border-b border-border bg-surface">
        <div className="flex items-center justify-between px-5 py-4 md:px-8">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wider text-primary">
              ExamNexus
            </p>

            <h1 className="mt-1 text-2xl font-bold text-text">
              Student Dashboard
            </h1>
          </div>

          <button
            type="button"
            onClick={onLogout}
            className="flex items-center gap-2 rounded-xl border border-border px-4 py-2.5 text-sm font-semibold text-text transition hover:bg-background"
          >
            <LogOut size={17} />
            Logout
          </button>
        </div>
      </header>

      {/* CONTENT */}
      <main className="p-5 md:p-8">
        <div className="mx-auto max-w-7xl">
          {/* WELCOME */}
          <section className="rounded-2xl bg-sidebar p-6 text-white shadow-sm md:p-8">
            <p className="text-sm font-medium opacity-80">
              Welcome back
            </p>

            <h2 className="mt-2 text-3xl font-bold">
              {dashboardUser?.name}
            </h2>

            <p className="mt-2 text-sm opacity-80">
              Student ID:{" "}
              {dashboardUser?.student_id ||
                "—"}
            </p>
          </section>

          {/* STAT CARDS */}
          <section className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-2xl border border-border bg-surface p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-text-muted">
                    Student ID
                  </p>

                  <p className="mt-2 text-xl font-bold text-text">
                    {dashboardUser?.student_id ||
                      "—"}
                  </p>
                </div>

                <User
                  size={24}
                  className="text-primary"
                />
              </div>
            </div>

            <div className="rounded-2xl border border-border bg-surface p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-text-muted">
                    Course
                  </p>

                  <p className="mt-2 text-xl font-bold text-text">
                    {dashboardUser?.course_id ??
                      "—"}
                  </p>
                </div>

                <BookOpen
                  size={24}
                  className="text-primary"
                />
              </div>
            </div>

            <div className="rounded-2xl border border-border bg-surface p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-text-muted">
                    Semester
                  </p>

                  <p className="mt-2 text-xl font-bold text-text">
                    {dashboardUser?.semester ??
                      "—"}
                  </p>
                </div>

                <GraduationCap
                  size={24}
                  className="text-primary"
                />
              </div>
            </div>

            <div className="rounded-2xl border border-border bg-surface p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-text-muted">
                    Batch
                  </p>

                  <p className="mt-2 text-xl font-bold text-text">
                    {dashboardUser?.batch || "—"}
                  </p>
                </div>

                <CalendarDays
                  size={24}
                  className="text-primary"
                />
              </div>
            </div>
          </section>

          {/* PROFILE */}
          <section className="mt-6 rounded-2xl border border-border bg-surface p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10">
                <Mail
                  size={20}
                  className="text-primary"
                />
              </div>

              <div>
                <h3 className="font-bold text-text">
                  Student Profile
                </h3>

                <p className="text-sm text-text-muted">
                  Your authenticated account information
                </p>
              </div>
            </div>

            <div className="mt-6 grid gap-5 md:grid-cols-2">
              <div>
                <p className="text-sm text-text-muted">
                  Full Name
                </p>

                <p className="mt-1 font-semibold text-text">
                  {dashboardUser?.name || "—"}
                </p>
              </div>

              <div>
                <p className="text-sm text-text-muted">
                  Email
                </p>

                <p className="mt-1 font-semibold text-text">
                  {dashboardUser?.email || "—"}
                </p>
              </div>

              <div>
                <p className="text-sm text-text-muted">
                  Student ID
                </p>

                <p className="mt-1 font-semibold text-text">
                  {dashboardUser?.student_id ||
                    "—"}
                </p>
              </div>

              <div>
                <p className="text-sm text-text-muted">
                  Class
                </p>

                <p className="mt-1 font-semibold text-text">
                  {dashboardUser?.class_name ||
                    "—"}
                </p>
              </div>

              <div>
                <p className="text-sm text-text-muted">
                  Session
                </p>

                <p className="mt-1 font-semibold text-text">
                  {dashboardUser?.session || "—"}
                </p>
              </div>

              <div>
                <p className="text-sm text-text-muted">
                  Semester
                </p>

                <p className="mt-1 font-semibold text-text">
                  {dashboardUser?.semester ??
                    "—"}
                </p>
              </div>
            </div>
          </section>

          {/* COMING SOON */}
          <section className="mt-6 rounded-2xl border border-dashed border-border bg-surface p-6">
            <div className="flex items-center gap-3">
              <CalendarDays
                size={22}
                className="text-primary"
              />

           <div className="space-y-6">

    {/* =====================================================
        EXAMINATION TIMETABLE
    ====================================================== */}

    <section className="rounded-2xl border border-border bg-card p-6 shadow-sm">

        <div className="mb-5 flex items-center gap-3">
            <CalendarDays className="h-6 w-6" />

            <div>
                <h2 className="text-lg font-semibold">
                    Examination Timetable
                </h2>

                <p className="text-sm text-muted-foreground">
                    Your published examination schedule
                </p>
            </div>
        </div>

        {data?.timetable?.length > 0 ? (

            <div className="space-y-4">

                {data.timetable.map((exam) => (

                    <div
                        key={exam.id}
                        className="rounded-xl border border-border p-4"
                    >

                        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">

                            <div>
                                <h3 className="font-semibold">
                                    {exam.subject_name || "Subject"}
                                </h3>

                                <p className="text-sm text-muted-foreground">
                                    {exam.subject_code || "—"}
                                </p>
                            </div>

                            <span className="rounded-full border px-3 py-1 text-xs">
                                {exam.session}
                            </span>

                        </div>

                        <div className="mt-4 grid gap-3 text-sm md:grid-cols-4">

                            <div>
                                <p className="text-muted-foreground">
                                    Examination
                                </p>
                                <p className="font-medium">
                                    {exam.examination_name}
                                </p>
                            </div>

                            <div>
                                <p className="text-muted-foreground">
                                    Date
                                </p>
                                <p className="font-medium">
                                    {exam.exam_date}
                                </p>
                            </div>

                            <div>
                                <p className="text-muted-foreground">
                                    Time
                                </p>
                                <p className="font-medium">
                                    {exam.start_time} - {exam.end_time}
                                </p>
                            </div>

                            <div>
                                <p className="text-muted-foreground">
                                    Duration
                                </p>
                                <p className="font-medium">
                                    {exam.duration_minutes} minutes
                                </p>
                            </div>

                        </div>

                    </div>

                ))}

            </div>

        ) : (

            <p className="text-sm text-muted-foreground">
                No published examinations are currently available.
            </p>

        )}

    </section>


    {/* =====================================================
        HALL TICKETS
    ====================================================== */}

    <section className="rounded-2xl border border-border bg-card p-6 shadow-sm">

        <div className="mb-5 flex items-center gap-3">
            <BookOpen className="h-6 w-6" />

            <div>
                <h2 className="text-lg font-semibold">
                    Hall Tickets
                </h2>

                <p className="text-sm text-muted-foreground">
                    Your examination hall, seat and verification QR
                </p>
            </div>
        </div>


        {data?.hall_tickets?.length > 0 ? (

            <div className="space-y-6">

                {data.hall_tickets.map((ticket) => (

                    <div
                        key={ticket.id}
                        className="rounded-xl border border-border p-5"
                    >

                        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">

                            <div className="flex-1">

                                <div className="mb-4">
                                    <h3 className="text-lg font-semibold">
                                        {ticket.examination_name}
                                    </h3>

                                    <p className="mt-1 text-sm text-muted-foreground">
                                        Status: {ticket.status}
                                    </p>
                                </div>


                                {ticket.entries?.length > 0 ? (

                                    <div className="space-y-3">

                                        {ticket.entries.map((entry) => (

                                            <div
                                                key={entry.timetable_id}
                                                className="rounded-lg border border-border p-4"
                                            >

                                                <div className="grid gap-4 text-sm md:grid-cols-2 lg:grid-cols-3">

                                                    <div>
                                                        <p className="text-muted-foreground">
                                                            Subject
                                                        </p>
                                                        <p className="font-medium">
                                                            {entry.subject_name}
                                                        </p>
                                                    </div>

                                                    <div>
                                                        <p className="text-muted-foreground">
                                                            Date
                                                        </p>
                                                        <p className="font-medium">
                                                            {entry.exam_date}
                                                        </p>
                                                    </div>

                                                    <div>
                                                        <p className="text-muted-foreground">
                                                            Session
                                                        </p>
                                                        <p className="font-medium">
                                                            {entry.session}
                                                        </p>
                                                    </div>

                                                    <div>
                                                        <p className="text-muted-foreground">
                                                            Time
                                                        </p>
                                                        <p className="font-medium">
                                                            {entry.start_time} - {entry.end_time}
                                                        </p>
                                                    </div>

                                                    <div>
                                                        <p className="text-muted-foreground">
                                                            Hall
                                                        </p>
                                                        <p className="font-medium">
                                                            {entry.hall_name}
                                                        </p>
                                                    </div>

                                                    <div>
                                                        <p className="text-muted-foreground">
                                                            Seat
                                                        </p>
                                                        <p className="font-medium">
                                                            {entry.seat_number}
                                                        </p>
                                                    </div>

                                                </div>

                                                <div className="mt-4 text-sm text-muted-foreground">
                                                    {entry.building_name}
                                                    {" · "}
                                                    Floor {entry.floor_no}
                                                </div>

                                            </div>

                                        ))}

                                    </div>

                                ) : (

                                    <p className="text-sm text-muted-foreground">
                                        Seat allocation information is not available yet.
                                    </p>

                                )}

                            </div>


                            {/* QR */}

                            <div className="flex shrink-0 flex-col items-center rounded-xl border border-border p-4">

                                <img
                                    src={`data:image/png;base64,${ticket.qr_base64}`}
                                    alt="Hall ticket verification QR code"
                                    className="h-40 w-40 rounded-lg border border-border bg-white p-2"
                                />

                                <p className="mt-3 text-center text-xs text-muted-foreground">
                                    Scan to verify hall ticket
                                </p>

                            </div>

                        </div>

                    </div>

                ))}

            </div>

        ) : (

            <p className="text-sm text-muted-foreground">
                Hall tickets have not been issued yet.
            </p>

        )}

    </section>

</div>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

export default StudentDashboard;