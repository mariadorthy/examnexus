import { useEffect, useState } from "react";
import { get } from "../../services/api";
import {
  Users,
  Building2,
  CalendarDays,
  Clock,
  Mail,
  BriefcaseBusiness,
  LogOut,
} from "lucide-react";

function StaffDashboard({
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
          "/dashboard/staff"
        );

        setDashboardUser(data.user);
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
      {/* HEADER */}
      <header className="border-b border-border bg-surface">
        <div className="flex items-center justify-between px-5 py-4 md:px-8">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wider text-primary">
              ExamNexus
            </p>

            <h1 className="mt-1 text-2xl font-bold text-text">
              Staff Dashboard
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
              Staff member •{" "}
              {dashboardUser?.designation ||
                "Staff"}
            </p>
          </section>

          {/* STAT CARDS */}
          <section className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-2xl border border-border bg-surface p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-text-muted">
                    Department
                  </p>

                  <p className="mt-2 text-xl font-bold text-text">
                    {dashboardUser?.department_id ??
                      "—"}
                  </p>
                </div>

                <Building2
                  size={24}
                  className="text-primary"
                />
              </div>
            </div>

            <div className="rounded-2xl border border-border bg-surface p-5">
              <div className="flex items-center justify-between">
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

                <Clock
                  size={24}
                  className="text-primary"
                />
              </div>
            </div>

            <div className="rounded-2xl border border-border bg-surface p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-text-muted">
                    Assigned Batch
                  </p>

                  <p className="mt-2 text-xl font-bold text-text">
                    {dashboardUser?.assigned_batch ||
                      "—"}
                  </p>
                </div>

                <Users
                  size={24}
                  className="text-primary"
                />
              </div>
            </div>

            <div className="rounded-2xl border border-border bg-surface p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-text-muted">
                    Role
                  </p>

                  <p className="mt-2 text-xl font-bold capitalize text-text">
                    {dashboardUser?.role}
                  </p>
                </div>

                <BriefcaseBusiness
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
                  Staff Profile
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
                  Designation
                </p>

                <p className="mt-1 font-semibold text-text">
                  {dashboardUser?.designation ||
                    "—"}
                </p>
              </div>

              <div>
                <p className="text-sm text-text-muted">
                  Department ID
                </p>

                <p className="mt-1 font-semibold text-text">
                  {dashboardUser?.department_id ??
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
<section className="rounded-2xl border border-border bg-card p-6 shadow-sm">

    <div className="mb-5 flex items-center gap-3">
        <CalendarDays className="h-6 w-6" />

        <div>
            <h2 className="text-lg font-semibold">
                Examination Duties
            </h2>

            <p className="text-sm text-muted-foreground">
                Your assigned invigilation duties
            </p>
        </div>
    </div>


    {data?.examination_duties?.length > 0 ? (

        <div className="space-y-4">

            {data.examination_duties.map((duty) => (

                <div
                    key={duty.id}
                    className="rounded-xl border border-border p-4"
                >

                    <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">

                        <div>
                            <h3 className="font-semibold">
                                {duty.examination_name}
                            </h3>

                            <p className="text-sm text-muted-foreground">
                                {duty.subject_code || "—"} ·{" "}
                                {duty.subject_name || "Subject"}
                            </p>
                        </div>

                        <span className="rounded-full border px-3 py-1 text-xs">
                            {duty.role}
                        </span>

                    </div>


                    <div className="mt-4 grid gap-4 text-sm md:grid-cols-2 lg:grid-cols-4">

                        <div>
                            <p className="text-muted-foreground">
                                Date
                            </p>
                            <p className="font-medium">
                                {duty.exam_date}
                            </p>
                        </div>

                        <div>
                            <p className="text-muted-foreground">
                                Session
                            </p>
                            <p className="font-medium">
                                {duty.session}
                            </p>
                        </div>

                        <div>
                            <p className="text-muted-foreground">
                                Time
                            </p>
                            <p className="font-medium">
                                {duty.start_time} - {duty.end_time}
                            </p>
                        </div>

                        <div>
                            <p className="text-muted-foreground">
                                Status
                            </p>
                            <p className="font-medium">
                                {duty.status}
                            </p>
                        </div>

                    </div>


                    <div className="mt-4 rounded-lg border border-border p-4">

                        <p className="text-xs text-muted-foreground">
                            Assigned Hall
                        </p>

                        <p className="mt-1 font-medium">
                            {duty.hall_name || "Hall not assigned"}
                        </p>

                        {duty.building_name && (
                            <p className="text-sm text-muted-foreground">
                                {duty.building_name}
                                {" · "}
                                Floor {duty.floor_no}
                            </p>
                        )}

                    </div>

                </div>

            ))}

        </div>

    ) : (

        <p className="text-sm text-muted-foreground">
            No examination duties have been assigned yet.
        </p>

    )}

</section>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

export default StaffDashboard;