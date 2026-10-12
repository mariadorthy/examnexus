import {
  Users,
  BookOpen,
  ClipboardList,
  Building2,
  GraduationCap,
  CalendarDays,
  Plus,
  ArrowRight,
  Clock3,
  Menu,
} from "lucide-react";

import { useEffect, useState } from "react";

import AdminSidebar from "../../components/AdminSidebar";
import { get } from "../../services/api";
function AdminDashboard({
  user,
  onLogout,
  onNavigate,
}) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [statistics, setStatistics] = useState([
    {
      title: "Students",
      value: "—",
      description: "Active students",
      icon: Users,
    },
    {
      title: "Staff",
      value: "—",
      description: "Active staff members",
      icon: Users,
    },
    {
      title: "Courses",
      value: "—",
      description: "Active courses",
      icon: BookOpen,
    },
    {
      title: "Departments",
      value: "—",
      description: "Active departments",
      icon: Building2,
    },
    {
      title: "Subjects",
      value: "—",
      description: "Active subjects",
      icon: GraduationCap,
    },
    {
      title: "Halls",
      value: "—",
      description: "Active examination halls",
      icon: Building2,
    },
  ]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [upcomingExaminations, setUpcomingExaminations] = useState([]);

  const [recentActivity, setRecentActivity] = useState([]);

    const [allocation, setAllocation] = useState({
    total_examinations: 0,
    examinations_with_allocations: 0,
    total_allocations: 0,
    status: "NOT_STARTED",
  });

  // Setup readiness derived from backend `system_status`
  // (real `count > 0` booleans from /dashboard/).
  // `null` means "not determined yet" (loading or error) — we
  // must NOT render these as "Ready" or "Not configured".
  const [systemStatus, setSystemStatus] = useState({
    departments: null,
    courses: null,
    subjects: null,
    students: null,
    staff: null,
    halls: null,
  });

  /* ================================================= */
  /* LOAD DASHBOARD DATA */
  /* ================================================= */

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await get("/dashboard/");

if (!data.success) {
  throw new Error(
    data.message || "Failed to load dashboard data."
  );
}

      /* ================================================= */
      /* STATISTICS */
      /* ================================================= */

      setStatistics([
        {
          title: "Students",
          value: data.statistics?.students ?? 0,
          description: "Active students",
          icon: Users,
        },
        {
          title: "Staff",
          value: data.statistics?.staff ?? 0,
          description: "Active staff members",
          icon: Users,
        },
        {
          title: "Courses",
          value: data.statistics?.courses ?? 0,
          description: "Active courses",
          icon: BookOpen,
        },
        {
          title: "Departments",
          value: data.statistics?.departments ?? 0,
          description: "Active departments",
          icon: Building2,
        },
        {
          title: "Subjects",
          value: data.statistics?.subjects ?? 0,
          description: "Active subjects",
          icon: GraduationCap,
        },
        {
          title: "Halls",
          value: data.statistics?.halls ?? 0,
          description: "Active examination halls",
          icon: Building2,
        },
      ]);

      /* ================================================= */
      /* UPCOMING EXAMINATIONS */
      /* ================================================= */

      setUpcomingExaminations(
        data.upcoming_examinations || []
      );

      /* ================================================= */
      /* RECENT ACTIVITY */
      /* ================================================= */

      setRecentActivity(
        data.recent_activity || []
      );
      /* ================================================= */
      /* ALLOCATION */
      /* ================================================= */

      setAllocation(
        data.allocation || {
          total_examinations: 0,
          examinations_with_allocations: 0,
          total_allocations: 0,
          status: "NOT_STARTED",
        }
      );

      /* ================================================= */
      /* SYSTEM READINESS (from backend system_status) */
      /* ================================================= */

      if (data.system_status) {
        setSystemStatus({
          departments:
            data.system_status.departments ?? null,
          courses: data.system_status.courses ?? null,
          subjects: data.system_status.subjects ?? null,
          students: data.system_status.students ?? null,
          staff: data.system_status.staff ?? null,
          halls: data.system_status.halls ?? null,
        });
      } else {
        // Backend did not return readiness — keep it Unknown
        // rather than guessing.
        setSystemStatus({
          departments: null,
          courses: null,
          subjects: null,
          students: null,
          staff: null,
          halls: null,
        });
      }
    } catch (err) {
      console.error("Dashboard error:", err);

      setError(
        "Unable to load dashboard data. Please make sure the backend is running."
      );

      // Clear readiness on error so we never show stale
      // "Ready" pills after a failed refresh.
      setSystemStatus({
        departments: null,
        courses: null,
        subjects: null,
        students: null,
        staff: null,
        halls: null,
      });
    } finally {
      setLoading(false);
    }
  };

  /* ================================================= */
  /* DERIVED VALUES */
  /* ================================================= */

  // Map a readiness boolean to an honest label.
  // null  -> "Not checked"  (loading or API failure)
  // true  -> "Ready"        (records exist; not proof of full config)
  // false -> "Not configured"
  const readinessLabel = (flag) => {
    if (flag === null || flag === undefined) {
      return "Not checked";
    }
    return flag ? "Ready" : "Not configured";
  };

  // Derive the Next Step card contents from real data only.
  // Returns { title, body, action, actionLabel } or null.
  const getNextStep = () => {
    if (loading) {
      return {
        title: "Loading current status…",
        body:
          "Checking the latest examination and allocation information.",
        action: null,
        actionLabel: null,
      };
    }

    if (error) {
      return {
        title: "Unable to determine next step",
        body:
          "Dashboard data could not be loaded. Refresh the page to try again.",
        action: null,
        actionLabel: null,
      };
    }

    const totalExaminations =
      allocation.total_examinations ?? 0;
    const allocationStatus = allocation.status;

    // No examinations yet.
    if (totalExaminations === 0) {
      return {
        title: "Create your first examination",
        body:
          "Create an examination to begin the examination workflow.",
        action: "Examinations",
        actionLabel: "Create Examination",
      };
    }

    // Examinations exist but allocations have not started.
    if (allocationStatus === "NOT_STARTED") {
      return {
        title: "Review allocations",
        body:
          "Examinations exist but allocations have not started yet. Open the allocation workspace to generate hall, seat and invigilator allocations.",
        action: "Allocations",
        actionLabel: "Open Allocations",
      };
    }

    // Partial allocation progress.
    if (allocationStatus === "PARTIAL") {
      return {
        title: "Complete pending allocations",
        body:
          "Some examinations still require allocations. Continue in the allocation workspace to finish them.",
        action: "Allocations",
        actionLabel: "Continue Allocations",
      };
    }

    // Allocations completed for all examinations.
    if (allocationStatus === "COMPLETED") {
      return {
        title: "Allocations complete",
        body:
          "All examinations have allocations. Review, validate or publish them from the allocation workspace.",
        action: "Allocations",
        actionLabel: "Review Allocations",
      };
    }

    // Defensive fallback — unknown status string.
    return {
      title: "Continue examination workflow",
      body:
        "Open the examination workspace to review the current state.",
      action: "Examinations",
      actionLabel: "Open Examinations",
    };
  };

  const nextStep = getNextStep();

  return (
    <div className="min-h-screen bg-background">

      {/* ================================================= */}
      {/* SIDEBAR */}
      {/* ================================================= */}

      <AdminSidebar
        user={user}
        onLogout={onLogout}
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        activePage="Dashboard"
        onNavigate={onNavigate}
      />

      {/* ================================================= */}
      {/* MAIN */}
      {/* ================================================= */}

      <main className="lg:ml-72">

        {/* ================================================= */}
        {/* TOP BAR */}
        {/* ================================================= */}

        <header className="sticky top-0 z-20 flex h-20 items-center justify-between border-b border-border bg-background/95 px-5 backdrop-blur md:px-8">

          <div className="flex items-center gap-4">

            <button
              type="button"
              onClick={() => setSidebarOpen(true)}
              className="rounded-lg p-2 text-sidebar transition hover:bg-surface lg:hidden"
              aria-label="Open sidebar"
            >
              <Menu size={23} />
            </button>

            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-accent">
                Administration
              </p>

              <h1 className="text-xl font-bold text-text md:text-2xl">
                Dashboard
              </h1>
            </div>

          </div>

          {/* User */}

          <div className="flex items-center gap-3">

            <div className="hidden text-right sm:block">
              <p className="text-sm font-semibold text-text">
                {user?.name || "Administrator"}
              </p>

              <p className="text-xs text-text-muted">
                Administrator
              </p>
            </div>

            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary font-bold text-white">
              {user?.name
                ? user.name.charAt(0).toUpperCase()
                : "A"}
            </div>

          </div>

        </header>

        {/* ================================================= */}
        {/* CONTENT */}
        {/* ================================================= */}

        <div className="p-5 md:p-8">

          {/* ================================================= */}
          {/* WELCOME */}
          {/* ================================================= */}

          <section className="mb-8">

            <p className="text-sm font-medium text-accent">
              Overview
            </p>

            <h2 className="mt-1 text-2xl font-bold text-text md:text-3xl">
              Welcome back,{" "}
              {user?.name || "Administrator"}
            </h2>

            <p className="mt-2 text-text-muted">
              Here's an overview of your examination
              management system.
            </p>

          </section>

          {/* ================================================= */}
          {/* ERROR */}
          {/* ================================================= */}

          {error && (
            <div className="mb-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {/* ================================================= */}
          {/* STATISTICS */}
          {/* ================================================= */}

          <section className="mb-8 grid gap-5 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">

            {statistics.map((stat) => {
              const Icon = stat.icon;

              return (
                <div
                  key={stat.title}
                  className="rounded-2xl border border-border bg-surface p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
                >

                  <div className="flex items-start justify-between">

                    <div>
                      <p className="text-sm font-medium text-text-muted">
                        {stat.title}
                      </p>

                      <p className="mt-2 text-3xl font-bold text-text">
                        {loading ? "..." : stat.value}
                      </p>
                    </div>

                    <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-light text-primary">
                      <Icon size={21} />
                    </div>

                  </div>

                  <p className="mt-4 text-xs text-text-muted">
                    {stat.description}
                  </p>

                </div>
              );
            })}

          </section>

          {/* ================================================= */}
          {/* QUICK ACTIONS */}
          {/* ================================================= */}

          <section className="mb-8">

            <div className="mb-4">

              <h3 className="text-lg font-bold text-text">
                Quick Actions
              </h3>

              <p className="text-sm text-text-muted">
                Start managing your examination process.
              </p>

            </div>

            <div className="grid gap-4 md:grid-cols-3">

              {/* CREATE EXAMINATION */}
              <button
                type="button"
                onClick={() => onNavigate("Examinations")}
                aria-label="Create Examination"
                className="group rounded-2xl bg-sidebar p-6 text-left text-white shadow-lg shadow-sidebar/10 transition hover:bg-primary"
              >

                <div className="mb-5 flex items-center justify-between">

                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/10">
                    <Plus size={22} />
                  </div>
                  <ArrowRight
                    size={20}
                    className="transition group-hover:translate-x-1"
                  />

                </div>

                <h4 className="font-semibold">
                  Create Examination
                </h4>

                <p className="mt-1 text-sm text-accent-light">
                  Create a new examination and define its schedule.
                </p>

              </button>

              {/* TIMETABLE */}
              <button
                type="button"
                onClick={() => onNavigate("Timetable")}
                aria-label="Manage Timetable"
                className="group rounded-2xl border border-border bg-surface p-6 text-left shadow-sm transition hover:border-accent hover:shadow-md"
              >

                <div className="mb-5 flex items-center justify-between">

                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-light text-primary">
                    <CalendarDays size={22} />
                  </div>
                  <ArrowRight
                    size={20}
                    className="text-accent transition group-hover:translate-x-1"
                  />

                </div>

                <h4 className="font-semibold text-text">
                  Manage Timetable
                </h4>

                <p className="mt-1 text-sm text-text-muted">
                  Schedule examination dates, times and sessions.
                </p>

              </button>

              {/* ALLOCATION */}
              <button
                type="button"
                onClick={() => onNavigate("Allocations")}
                aria-label="Examination Allocation"
                className="group rounded-2xl border border-border bg-surface p-6 text-left shadow-sm transition hover:border-accent hover:shadow-md"
              >

                <div className="mb-5 flex items-center justify-between">

                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-light text-primary">
                    <ClipboardList size={22} />
                  </div>
                  <ArrowRight
                    size={20}
                    className="text-accent transition group-hover:translate-x-1"
                  />

                </div>

                <h4 className="font-semibold text-text">
                  Examination Allocation
                </h4>

                <p className="mt-1 text-sm text-text-muted">
                  Generate and review student hall allocations.
                </p>

              </button>

            </div>

          </section>

          {/* ================================================= */}
          {/* UPCOMING EXAMINATIONS */}
          {/* ================================================= */}

          <section className="mb-8">

            <div className="mb-4">

              <h3 className="text-lg font-bold text-text">
                Upcoming Examinations
              </h3>

              <p className="text-sm text-text-muted">
                The next scheduled examinations.
              </p>

            </div>

            <div className="rounded-2xl border border-border bg-surface shadow-sm">

              {upcomingExaminations.length === 0 ? (

                <div className="p-6 text-center text-sm text-text-muted">
                  No upcoming examinations.
                </div>

              ) : (

                <div className="divide-y divide-border">

                  {upcomingExaminations.map((exam) => (

                    <div
                      key={exam.id}
                      className="flex flex-col gap-3 p-5 md:flex-row md:items-center md:justify-between"
                    >

                      <div>

                        <p className="font-semibold text-text">
                          {exam.subject_code || "Subject"}
                          {" — "}
                          {exam.subject_name || "Unknown Subject"}
                        </p>

                        <p className="mt-1 text-sm text-text-muted">
                          {exam.exam_date}
                          {" • "}
                          {exam.start_time} - {exam.end_time}
                        </p>

                      </div>

                      <div className="flex items-center gap-3">

                        <span className="rounded-full bg-accent-light px-3 py-1 text-xs font-semibold text-primary">
                          {exam.session}
                        </span>

                        <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
                          {exam.exam_type}
                        </span>

                      </div>

                    </div>

                  ))}

                </div>

              )}

            </div>

          </section>

          {/* ================================================= */}
          {/* RECENT ACTIVITY */}
          {/* ================================================= */}

          <section className="mb-8">

            <div className="mb-4">

              <h3 className="text-lg font-bold text-text">
                Recent Activity
              </h3>

              <p className="text-sm text-text-muted">
                Recent activity in the examination system.
              </p>

            </div>

            <div className="rounded-2xl border border-border bg-surface shadow-sm">

              {recentActivity.length === 0 ? (

                <div className="p-6 text-center text-sm text-text-muted">
                  No recent activity available.
                </div>

              ) : (

                <div className="divide-y divide-border">

                  {recentActivity.map((activity, index) => (

                    <div
                      key={activity.id || index}
                      className="flex items-center gap-4 p-5"
                    >

                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent-light text-primary">
                        <Clock3 size={19} />
                      </div>

                      <div>

                        <p className="text-sm font-semibold text-text">
                          {activity.action || "System activity"}
                        </p>
                        {activity.description && (
                          <p className="mt-1 text-xs text-text-muted">
                            {activity.description}
                          </p>
                        )}

                        {activity.created_at && (
                          <p className="mt-1 text-xs text-text-muted">
                            {activity.created_at}
                          </p>
                        )}

                      </div>

                    </div>

                  ))}

                </div>

              )}

            </div>

          </section>

          {/* ================================================= */}
          {/* ALLOCATION OVERVIEW */}
          {/* ================================================= */}

          <section className="mb-8">

            <div className="mb-4">

              <h3 className="text-lg font-bold text-text">
                Allocation Overview
              </h3>

              <p className="text-sm text-text-muted">
                Current examination hall allocation status.
              </p>

            </div>

            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">

              {/* TOTAL EXAMINATIONS */}

              <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">

                <p className="text-sm font-medium text-text-muted">
                  Total Examinations
                </p>

                <p className="mt-2 text-3xl font-bold text-text">
                  {loading
                    ? "..."
                    : allocation.total_examinations}
                </p>

              </div>

              {/* ALLOCATED EXAMINATIONS */}

              <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">

                <p className="text-sm font-medium text-text-muted">
                  Allocated Examinations
                </p>

                <p className="mt-2 text-3xl font-bold text-text">
                  {loading
                    ? "..."
                    : allocation.examinations_with_allocations}
                </p>

              </div>

              {/* TOTAL ALLOCATIONS */}

              <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">

                <p className="text-sm font-medium text-text-muted">
                  Total Allocations
                </p>

                <p className="mt-2 text-3xl font-bold text-text">
                  {loading
                    ? "..."
                    : allocation.total_allocations}
                </p>

              </div>

              {/* STATUS */}

              <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">

                <p className="text-sm font-medium text-text-muted">
                  Allocation Status
                </p>

                <p className="mt-2 text-lg font-bold text-primary">
                  {loading
                    ? "..."
                    : allocation.status}
                </p>

              </div>

            </div>

          </section>

          {/* ================================================= */}
          {/* EXAMINATION SETUP + NEXT STEP */}
          {/* ================================================= */}

          <section className="grid gap-5 lg:grid-cols-2">

            {/* ================================================= */}
            {/* EXAMINATION SETUP */}
            {/* ================================================= */}

            <div className="rounded-2xl border border-border bg-surface p-6 shadow-sm">

              <div className="mb-5 flex items-center justify-between">

                <div>

                  <h3 className="font-bold text-text">
                    Examination Setup
                  </h3>

                  <p className="mt-1 text-sm text-text-muted">
                    Current system readiness
                  </p>

                </div>

                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-light text-primary">
                  <ClipboardList size={20} />
                </div>

              </div>

              <div className="space-y-4">

                <StatusRow
                  label="Departments"
                  status={readinessLabel(
                    systemStatus.departments
                  )}
                />

                <StatusRow
                  label="Courses"
                  status={readinessLabel(
                    systemStatus.courses
                  )}
                />

                <StatusRow
                  label="Subjects"
                  status={readinessLabel(
                    systemStatus.subjects
                  )}
                />

                <StatusRow
                  label="Students"
                  status={readinessLabel(
                    systemStatus.students
                  )}
                />

                <StatusRow
                  label="Staff"
                  status={readinessLabel(
                    systemStatus.staff
                  )}
                />

                <StatusRow
                  label="Halls"
                  status={readinessLabel(
                    systemStatus.halls
                  )}
                />

              </div>

            </div>

            {/* ================================================= */}
            {/* NEXT STEP */}
            {/* ================================================= */}

            <div className="rounded-2xl bg-accent p-6 text-white shadow-lg">

              <div className="flex h-full flex-col justify-between">
                <div>

                  <div className="mb-5 flex h-11 w-11 items-center justify-center rounded-xl bg-white/10">
                    <Clock3 size={22} />
                  </div>

                  <p className="text-sm font-semibold uppercase tracking-wider text-accent-light">
                    Next Step
                  </p>

                  <h3 className="mt-2 text-2xl font-bold">
                    {nextStep.title}
                  </h3>

                  <p className="mt-3 max-w-md text-sm leading-6 text-accent-light">
                    {nextStep.body}
                  </p>

                </div>

                {nextStep.action && (
                  <button
                    type="button"
                    onClick={() =>
                      onNavigate(nextStep.action)
                    }
                    aria-label={nextStep.actionLabel}
                    className="mt-8 flex w-fit items-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-sidebar transition hover:bg-background"
                  >
                    {nextStep.actionLabel}
                    <ArrowRight size={17} />
                  </button>
                )}
              </div>

            </div>

          </section>

        </div>

      </main>

    </div>
  );
}

/* ================================================= */
/* STATUS ROW */
/* ================================================= */

function StatusRow({ label, status }) {
  return (
    <div className="flex items-center justify-between">

      <div className="flex items-center gap-3">

        <div className="h-2.5 w-2.5 rounded-full bg-accent" />

        <span className="text-sm font-medium text-sidebar">
          {label}
        </span>

      </div>

      <span className="rounded-full bg-accent-light px-3 py-1 text-xs font-semibold text-primary">
        {status}
      </span>

    </div>
  );
}

export default AdminDashboard;
