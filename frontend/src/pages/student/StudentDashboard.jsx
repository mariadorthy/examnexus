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

              <div>
                <h3 className="font-bold text-text">
                  Examination Information
                </h3>

                <p className="mt-1 text-sm text-text-muted">
                  Examination timetable, eligibility,
                  hall allocation, seat information and
                  hall ticket will appear here as those
                  modules are implemented.
                </p>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

export default StudentDashboard;