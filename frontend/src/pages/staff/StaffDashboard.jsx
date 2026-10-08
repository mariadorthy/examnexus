import { useEffect, useState } from "react";
import { get } from "../../services/api";
import {
  Building2,
  CalendarDays,
  Clock,
  Mail,
  BriefcaseBusiness,
  Menu,
} from "lucide-react";

import PortalSidebar from "../../components/PortalSidebar";

function StaffDashboard({
  user,
  onLogout,
}) {
const [dashboardUser, setDashboardUser] =
  useState(user);

const [dashboardData, setDashboardData] =
  useState({
    examination_duties: [],
  });
const [sidebarOpen, setSidebarOpen] =
  useState(false);
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
          "/dashboard/staff"
        );

setDashboardUser(data.user);

setDashboardData({
  examination_duties:
    data.examination_duties || [],
});
      } catch (error) {
        console.error(
          "Staff dashboard error:",
          error
        );

        setError(
          error.message ||
            "Failed to load staff dashboard."
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
      role="staff"
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
                Staff Portal
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
              Staff Member
            </p>
          </div>
        </div>
      </header>

      <div className="p-5 md:p-8">
        <div className="mx-auto max-w-7xl">

          {/* WELCOME */}
          <section className="overflow-hidden rounded-2xl bg-sidebar p-6 text-white shadow-sm md:p-8">
            <p className="text-sm font-medium text-white/70">
              Welcome back
            </p>

            <h2 className="mt-2 text-3xl font-bold md:text-4xl">
              {dashboardUser?.name || "Staff Member"}
            </h2>

            <p className="mt-2 text-sm text-white/70">
              {dashboardUser?.designation || "Staff"}{" "}
              · Examination Invigilation Portal
            </p>
          </section>

          {/* STAT CARDS */}
          <section className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">

            <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-text-muted">
                    Department
                  </p>

                  <p className="mt-2 text-xl font-bold text-text">
                    {dashboardUser?.department_id ?? "—"}
                  </p>
                </div>

                <div className="rounded-xl bg-primary/10 p-3">
                  <Building2
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
                    Availability
                  </p>

                  <p className="mt-2 text-xl font-bold text-text">
                    {dashboardUser?.availability
                      ? "Available"
                      : "Unavailable"}
                  </p>
                </div>

                <div className="rounded-xl bg-primary/10 p-3">
                  <Clock
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
                    Assigned Duties
                  </p>

                  <p className="mt-2 text-xl font-bold text-text">
                    {dashboardData.examination_duties.length}
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

            <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-text-muted">
                    Role
                  </p>

                  <p className="mt-2 text-xl font-bold capitalize text-text">
                    {dashboardUser?.role || "Staff"}
                  </p>
                </div>

                <div className="rounded-xl bg-primary/10 p-3">
                  <BriefcaseBusiness
                    size={22}
                    className="text-primary"
                  />
                </div>
              </div>
            </div>

          </section>

          {/* EXAMINATION DUTIES */}
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
                    Examination Duties
                  </h2>

                  <p className="text-sm text-text-muted">
                    Your assigned invigilation duties
                  </p>
                </div>
              </div>
            </div>

            <div className="p-6">

              {dashboardData.examination_duties.length > 0 ? (
                <div className="grid gap-5 lg:grid-cols-2">

                  {dashboardData.examination_duties.map(
                    (duty) => (
                      <div
                        key={duty.id}
                        className="rounded-2xl border border-border bg-background p-5 transition hover:shadow-md"
                      >

                        <div className="flex items-start justify-between gap-4">
                          <div>
                            <h3 className="font-bold text-text">
                              {duty.examination_name}
                            </h3>

                            <p className="mt-1 text-sm text-text-muted">
                              {duty.subject_code || "—"} ·{" "}
                              {duty.subject_name || "Subject"}
                            </p>
                          </div>

                          <span className="shrink-0 rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
                            {duty.role}
                          </span>
                        </div>

                        <div className="mt-5 grid gap-4 sm:grid-cols-2">

                          <div>
                            <p className="text-xs font-medium uppercase tracking-wide text-text-muted">
                              Date
                            </p>

                            <p className="mt-1 font-semibold text-text">
                              {duty.exam_date}
                            </p>
                          </div>

                          <div>
                            <p className="text-xs font-medium uppercase tracking-wide text-text-muted">
                              Session
                            </p>

                            <p className="mt-1 font-semibold text-text">
                              {duty.session}
                            </p>
                          </div>

                          <div>
                            <p className="text-xs font-medium uppercase tracking-wide text-text-muted">
                              Time
                            </p>

                            <p className="mt-1 font-semibold text-text">
                              {duty.start_time} -{" "}
                              {duty.end_time}
                            </p>
                          </div>

                          <div>
                            <p className="text-xs font-medium uppercase tracking-wide text-text-muted">
                              Status
                            </p>

                            <p className="mt-1 font-semibold text-text">
                              {duty.status}
                            </p>
                          </div>

                        </div>

                        <div className="mt-5 rounded-xl border border-border bg-surface p-4">
                          <p className="text-xs font-medium uppercase tracking-wide text-text-muted">
                            Assigned Hall
                          </p>

                          <p className="mt-1 font-semibold text-text">
                            {duty.hall_name ||
                              "Hall not assigned"}
                          </p>

                          {duty.building_name && (
                            <p className="mt-1 text-sm text-text-muted">
                              {duty.building_name}
                              {" · "}
                              Floor {duty.floor_no}
                            </p>
                          )}
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
                    No examination duties assigned
                  </p>

                  <p className="mt-1 text-sm text-text-muted">
                    Your assigned invigilation duties will appear here.
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
                  Staff Profile
                </h2>

                <p className="text-sm text-text-muted">
                  Your authenticated account information
                </p>
              </div>
            </div>

            <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">

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
                  Designation
                </p>

                <p className="mt-1 font-semibold text-text">
                  {dashboardUser?.designation || "—"}
                </p>
              </div>

              <div>
                <p className="text-xs uppercase tracking-wide text-text-muted">
                  Department
                </p>

                <p className="mt-1 font-semibold text-text">
                  {dashboardUser?.department_id ?? "—"}
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

export default StaffDashboard;