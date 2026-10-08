import { useEffect, useState } from "react";
import { get } from "../../services/api";
import {
  GraduationCap,
  BookOpen,
  CalendarDays,
  User,
  Mail,
  LogOut,
  Menu,
  Ticket,
} from "lucide-react";

import PortalSidebar from "../../components/PortalSidebar";

function StudentDashboard({
  user,
  onLogout,
}) {
  const [dashboardUser, setDashboardUser] =
    useState(user);

  const [dashboardData, setDashboardData] =
    useState({
      timetable: [],
      hall_tickets: [],
    });

  const [loading, setLoading] =
    useState(true);
const [sidebarOpen, setSidebarOpen] =
  useState(false);
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

        setDashboardData({
          timetable: data.timetable || [],
          hall_tickets: data.hall_tickets || [],
        });
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
    <PortalSidebar
      user={dashboardUser}
      onLogout={onLogout}
      sidebarOpen={sidebarOpen}
      setSidebarOpen={setSidebarOpen}
      activePage="Dashboard"
      role="student"
    />

    <main className="lg:ml-72">

      {/* TOPBAR */}
      <header className="sticky top-0 z-30 border-b border-border bg-surface/95 backdrop-blur">
        <div className="flex h-20 items-center justify-between px-5 md:px-8">

          <div className="flex items-center gap-3">

            <button
              type="button"
              onClick={() => setSidebarOpen(true)}
              className="rounded-xl border border-border p-2.5 text-sidebar lg:hidden"
            >
              <Menu size={20} />
            </button>

            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-primary">
                Student Portal
              </p>

              <h1 className="text-xl font-bold text-text">
                Dashboard
              </h1>
            </div>

          </div>

          <div className="hidden text-right sm:block">
            <p className="text-sm font-semibold text-text">
              {dashboardUser?.name}
            </p>

            <p className="text-xs text-text-muted">
              Student
            </p>
          </div>

        </div>
      </header>

      <div className="p-5 md:p-8">
        <div className="mx-auto max-w-7xl">

          {/* WELCOME */}
          <section className="rounded-2xl bg-sidebar p-6 text-white shadow-sm md:p-8">

            <p className="text-sm font-medium text-white/70">
              Welcome back
            </p>

            <h2 className="mt-2 text-3xl font-bold md:text-4xl">
              {dashboardUser?.name || "Student"}
            </h2>

            <p className="mt-2 text-sm text-white/70">
              Student ID:{" "}
              {dashboardUser?.student_id || "—"}
            </p>

          </section>

          {/* STAT CARDS */}
          <section className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">

            <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
              <div className="flex items-start justify-between">

                <div>
                  <p className="text-sm text-text-muted">
                    Student ID
                  </p>

                  <p className="mt-2 text-xl font-bold text-text">
                    {dashboardUser?.student_id || "—"}
                  </p>
                </div>

                <div className="rounded-xl bg-primary/10 p-3">
                  <User
                    size={22}
                    className="text-primary"
                  />
                </div>

              </div>
            </div>

            <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
              <div className="flex items-start justify-between">

                <div>
                  <p className="text-sm text-text-muted">
                    Course
                  </p>

                  <p className="mt-2 text-xl font-bold text-text">
                    {dashboardUser?.course_id ?? "—"}
                  </p>
                </div>

                <div className="rounded-xl bg-primary/10 p-3">
                  <BookOpen
                    size={22}
                    className="text-primary"
                  />
                </div>

              </div>
            </div>

            <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
              <div className="flex items-start justify-between">

                <div>
                  <p className="text-sm text-text-muted">
                    Semester
                  </p>

                  <p className="mt-2 text-xl font-bold text-text">
                    {dashboardUser?.semester ?? "—"}
                  </p>
                </div>

                <div className="rounded-xl bg-primary/10 p-3">
                  <GraduationCap
                    size={22}
                    className="text-primary"
                  />
                </div>

              </div>
            </div>

            <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
              <div className="flex items-start justify-between">

                <div>
                  <p className="text-sm text-text-muted">
                    Upcoming Exams
                  </p>

                  <p className="mt-2 text-xl font-bold text-text">
                    {dashboardData.timetable.length}
                  </p>
                </div>

                <div className="rounded-xl bg-primary/10 p-3">
                  <CalendarDays
                    size={22}
                    className="text-primary"
                  />
                </div>

              </div>
            </div>

          </section>

          {/* EXAMINATION TIMETABLE */}
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
                    Your published examination schedule
                  </p>
                </div>

              </div>

            </div>

            <div className="p-6">

              {dashboardData.timetable.length > 0 ? (

                <div className="grid gap-5 lg:grid-cols-2">

                  {dashboardData.timetable.map(
                    (exam) => (

                      <div
                        key={exam.id}
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
                            {exam.session}
                          </span>

                        </div>

                        <div className="mt-5 grid gap-4 sm:grid-cols-2">

                          <div>
                            <p className="text-xs font-medium uppercase tracking-wide text-text-muted">
                              Examination
                            </p>

                            <p className="mt-1 font-semibold text-text">
                              {exam.examination_name}
                            </p>
                          </div>

                          <div>
                            <p className="text-xs font-medium uppercase tracking-wide text-text-muted">
                              Date
                            </p>

                            <p className="mt-1 font-semibold text-text">
                              {exam.exam_date}
                            </p>
                          </div>

                          <div>
                            <p className="text-xs font-medium uppercase tracking-wide text-text-muted">
                              Time
                            </p>

                            <p className="mt-1 font-semibold text-text">
                              {exam.start_time} -{" "}
                              {exam.end_time}
                            </p>
                          </div>

                          <div>
                            <p className="text-xs font-medium uppercase tracking-wide text-text-muted">
                              Duration
                            </p>

                            <p className="mt-1 font-semibold text-text">
                              {exam.duration_minutes} minutes
                            </p>
                          </div>

                        </div>

                      </div>

                    )
                  )}

                </div>

              ) : (

                <div className="rounded-xl border border-dashed border-border p-10 text-center">

                  <CalendarDays
                    size={30}
                    className="mx-auto text-text-muted"
                  />

                  <p className="mt-3 font-semibold text-text">
                    No published examinations
                  </p>

                  <p className="mt-1 text-sm text-text-muted">
                    Your examination schedule will appear here.
                  </p>

                </div>

              )}

            </div>
          </section>

          {/* HALL TICKETS */}
          <section className="mt-6 rounded-2xl border border-border bg-surface shadow-sm">

            <div className="border-b border-border p-6">

              <div className="flex items-center gap-3">

                <div className="rounded-xl bg-primary/10 p-3">
                  <Ticket
                    size={21}
                    className="text-primary"
                  />
                </div>

                <div>
                  <h2 className="text-lg font-bold text-text">
                    Hall Tickets
                  </h2>

                  <p className="text-sm text-text-muted">
                    Your examination hall, seat and verification QR
                  </p>
                </div>

              </div>

            </div>

            <div className="p-6">

              {dashboardData.hall_tickets.length > 0 ? (

                <div className="space-y-5">

                  {dashboardData.hall_tickets.map(
                    (ticket) => (

                      <div
                        key={ticket.id}
                        className="rounded-2xl border border-border bg-background p-5"
                      >

                        <div className="flex flex-col gap-5 lg:flex-row lg:justify-between">

                          <div className="flex-1">

                            <div className="flex flex-wrap items-center gap-3">

                              <h3 className="text-lg font-bold text-text">
                                {ticket.examination_name}
                              </h3>

                              <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
                                {ticket.status}
                              </span>

                            </div>

                            <div className="mt-5 grid gap-4 md:grid-cols-2">

                              {ticket.entries?.map(
                                (entry) => (

                                  <div
                                    key={entry.timetable_id}
                                    className="rounded-xl border border-border bg-surface p-4"
                                  >

                                    <div className="grid gap-4 sm:grid-cols-2">

                                      <div>
                                        <p className="text-xs uppercase tracking-wide text-text-muted">
                                          Subject
                                        </p>

                                        <p className="mt-1 font-semibold text-text">
                                          {entry.subject_name}
                                        </p>
                                      </div>

                                      <div>
                                        <p className="text-xs uppercase tracking-wide text-text-muted">
                                          Date
                                        </p>

                                        <p className="mt-1 font-semibold text-text">
                                          {entry.exam_date}
                                        </p>
                                      </div>

                                      <div>
                                        <p className="text-xs uppercase tracking-wide text-text-muted">
                                          Session
                                        </p>

                                        <p className="mt-1 font-semibold text-text">
                                          {entry.session}
                                        </p>
                                      </div>

                                      <div>
                                        <p className="text-xs uppercase tracking-wide text-text-muted">
                                          Time
                                        </p>

                                        <p className="mt-1 font-semibold text-text">
                                          {entry.start_time} -{" "}
                                          {entry.end_time}
                                        </p>
                                      </div>

                                      <div>
                                        <p className="text-xs uppercase tracking-wide text-text-muted">
                                          Hall
                                        </p>

                                        <p className="mt-1 font-semibold text-text">
                                          {entry.hall_name}
                                        </p>
                                      </div>

                                      <div>
                                        <p className="text-xs uppercase tracking-wide text-text-muted">
                                          Seat
                                        </p>

                                        <p className="mt-1 text-lg font-bold text-primary">
                                          {entry.seat_number}
                                        </p>
                                      </div>

                                    </div>

                                    <div className="mt-4 border-t border-border pt-3 text-sm text-text-muted">
                                      {entry.building_name}
                                      {" · "}
                                      Floor {entry.floor_no}
                                    </div>

                                  </div>

                                )
                              )}

                            </div>

                          </div>

                          {/* QR */}
                          <div className="flex shrink-0 flex-col items-center justify-center rounded-2xl border border-border bg-surface p-5">

                            <img
                              src={`data:image/png;base64,${ticket.qr_base64}`}
                              alt="Hall ticket verification QR code"
                              className="h-40 w-40 rounded-xl border border-border bg-white p-2"
                            />

                            <p className="mt-3 text-center text-xs font-medium text-text-muted">
                              Scan to verify
                            </p>

                          </div>

                        </div>

                      </div>

                    )
                  )}

                </div>

              ) : (

                <div className="rounded-xl border border-dashed border-border p-10 text-center">

                  <Ticket
                    size={30}
                    className="mx-auto text-text-muted"
                  />

                  <p className="mt-3 font-semibold text-text">
                    Hall tickets have not been issued yet
                  </p>

                  <p className="mt-1 text-sm text-text-muted">
                    Once your examination is published and the hall ticket is generated, it will appear here.
                  </p>

                </div>

              )}

            </div>
          </section>

          {/* PROFILE */}
          <section className="mt-6 rounded-2xl border border-border bg-surface p-6 shadow-sm">

            <div className="flex items-center gap-3">

              <div className="rounded-xl bg-primary/10 p-3">
                <Mail
                  size={21}
                  className="text-primary"
                />
              </div>

              <div>
                <h2 className="font-bold text-text">
                  Student Profile
                </h2>

                <p className="text-sm text-text-muted">
                  Your authenticated account information
                </p>
              </div>

            </div>

            <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">

              <div>
                <p className="text-xs uppercase tracking-wide text-text-muted">
                  Full Name
                </p>

                <p className="mt-1 font-semibold text-text">
                  {dashboardUser?.name || "—"}
                </p>
              </div>

              <div>
                <p className="text-xs uppercase tracking-wide text-text-muted">
                  Email
                </p>

                <p className="mt-1 break-all font-semibold text-text">
                  {dashboardUser?.email || "—"}
                </p>
              </div>

              <div>
                <p className="text-xs uppercase tracking-wide text-text-muted">
                  Student ID
                </p>

                <p className="mt-1 font-semibold text-text">
                  {dashboardUser?.student_id || "—"}
                </p>
              </div>

              <div>
                <p className="text-xs uppercase tracking-wide text-text-muted">
                  Class
                </p>

                <p className="mt-1 font-semibold text-text">
                  {dashboardUser?.class_name || "—"}
                </p>
              </div>

              <div>
                <p className="text-xs uppercase tracking-wide text-text-muted">
                  Session
                </p>

                <p className="mt-1 font-semibold text-text">
                  {dashboardUser?.session || "—"}
                </p>
              </div>

              <div>
                <p className="text-xs uppercase tracking-wide text-text-muted">
                  Semester
                </p>

                <p className="mt-1 font-semibold text-text">
                  {dashboardUser?.semester ?? "—"}
                </p>
              </div>

            </div>

          </section>

        </div>
      </div>
    </main>
  </div>
);
}

export default StudentDashboard;