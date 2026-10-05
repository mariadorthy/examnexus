import { useEffect, useState } from "react";

import {
  BarChart3,
  RefreshCw,
  AlertCircle,
  Users,
  Building2,
  UserCheck,
} from "lucide-react";

import AdminSidebar from "../../../components/AdminSidebar";
import AdminTopbar from "../../../components/AdminTopbar";

import { get } from "../../../services/api";
import {
  getAllocationReport,
  getStudentAllocationReport,
  getHallUtilizationReport,
  getInvigilatorReport,
} from "../../../services/reportService";


const TABS = [
  { key: "allocation", label: "Allocation", icon: BarChart3 },
  { key: "students", label: "Students", icon: Users },
  { key: "halls", label: "Hall Utilization", icon: Building2 },
  { key: "invigilators", label: "Invigilators", icon: UserCheck },
];


function Reports({
  user,
  onLogout,
  onNavigate,
}) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [examinations, setExaminations] = useState([]);
  const [selectedExamination, setSelectedExamination] =
    useState("");
  const [activeTab, setActiveTab] = useState("allocation");

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    loadExaminations();
  }, []);

  useEffect(() => {
    if (selectedExamination) {
      loadReport(selectedExamination, activeTab);
    } else {
      setData(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedExamination, activeTab]);

  const loadExaminations = async () => {
    try {
      const result = await get("/examinations/");
      setExaminations(result || []);
    } catch (err) {
      console.error(err);
      setError("Unable to load examinations.");
    }
  };

  const loadReport = async (examinationId, tab) => {
    try {
      setLoading(true);
      setError("");

      let result;

      if (tab === "allocation") {
        result = await getAllocationReport(examinationId);
      } else if (tab === "students") {
        result = await getStudentAllocationReport(examinationId);
      } else if (tab === "halls") {
        result = await getHallUtilizationReport(examinationId);
      } else if (tab === "invigilators") {
        result = await getInvigilatorReport(examinationId);
      }

      setData(result);
    } catch (err) {
      console.error(err);
      setError(
        err.message || "Unable to load report data."
      );
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">

      <AdminSidebar
        user={user}
        onLogout={onLogout}
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        activePage="Reports"
        onNavigate={onNavigate}
      />

      <main className="lg:ml-72">

        <AdminTopbar
          user={user}
          title="Reports"
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
                  Reports
                </h1>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-text-muted">
                  Read-only snapshots of allocation, student,
                  hall and invigilator data for a published or
                  generated examination.
                </p>
              </div>

              <button
                type="button"
                onClick={() =>
                  selectedExamination &&
                  loadReport(selectedExamination, activeTab)
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

          {/* SELECTOR */}

          <section className="mb-6 rounded-2xl border border-border bg-surface p-5 shadow-sm md:p-6">

            <label
              htmlFor="report-examination"
              className="mb-2 block text-sm font-semibold text-sidebar"
            >
              Select Examination
            </label>

            <select
              id="report-examination"
              value={selectedExamination}
              onChange={(event) =>
                setSelectedExamination(event.target.value)
              }
              className="w-full max-w-xl rounded-xl border border-border bg-surface px-4 py-3.5 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
            >
              <option value="">Select an examination</option>
              {examinations.map((exam) => (
                <option key={exam.id} value={exam.id}>
                  {`Examination #${exam.id}`} — {exam.name}
                </option>
              ))}
            </select>

          </section>

          {/* TABS */}

          <section className="mb-6 rounded-2xl border border-border bg-surface p-2 shadow-sm">

            <div className="grid gap-2 md:grid-cols-4">

              {TABS.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.key;

                return (
                  <button
                    key={tab.key}
                    type="button"
                    onClick={() => setActiveTab(tab.key)}
                    className={`flex items-center justify-center gap-2 rounded-xl px-4 py-3 text-sm font-semibold transition ${
                      isActive
                        ? "bg-sidebar text-white shadow-md"
                        : "text-text hover:bg-surface-muted"
                    }`}
                  >
                    <Icon size={17} />
                    {tab.label}
                  </button>
                );
              })}

            </div>

          </section>

          {/* ERROR */}

          {error && (
            <div className="mb-6 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              <AlertCircle size={19} className="mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* LOADING */}

          {loading && (
            <div className="flex items-center justify-center py-16">
              <RefreshCw
                size={26}
                className="animate-spin text-accent"
              />
              <span className="ml-3 text-sm text-text-muted">
                Loading report...
              </span>
            </div>
          )}

          {/* DATA */}

          {!loading && data && (
            <ReportTable tab={activeTab} data={data} />
          )}

          {!loading && !data && !error && (
            <div className="rounded-2xl border border-dashed border-border bg-surface p-12 text-center">
              <BarChart3
                size={28}
                className="mx-auto text-text-muted"
              />
              <h3 className="mt-4 text-lg font-bold text-text">
                Select an examination
              </h3>
              <p className="mx-auto mt-2 max-w-md text-sm text-text-muted">
                Choose an examination above to view its
                reports.
              </p>
            </div>
          )}

        </div>

      </main>

    </div>
  );
}


function ReportTable({ tab, data }) {
  const rows = data?.rows || [];

  if (rows.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-border bg-surface p-12 text-center">
        <p className="text-sm text-text-muted">
          No data available for this report.
        </p>
      </div>
    );
  }

  if (tab === "allocation") {
    return (
      <Shell title="Allocation Report">
        <table className="w-full min-w-[960px]">
          <thead>
            <tr className="border-b border-border bg-surface-muted">
              {[
                "Date",
                "Session",
                "Hall",
                "Building",
                "Purpose",
                "Capacity",
                "Seats",
                "Invigilators",
              ].map((h) => (
                <th
                  key={h}
                  className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, idx) => (
              <tr
                key={idx}
                className="border-b border-border last:border-0 hover:bg-surface-muted"
              >
                <td className="px-4 py-3 text-sm">
                  {row.exam_date}
                </td>
                <td className="px-4 py-3 text-sm font-semibold text-sidebar">
                  {row.session}
                </td>
                <td className="px-4 py-3 text-sm">
                  {row.hall}
                </td>
                <td className="px-4 py-3 text-sm">
                  {row.building_name}
                </td>
                <td className="px-4 py-3">
                  <span className="rounded-full bg-accent-light px-2.5 py-1 text-xs font-semibold text-primary">
                    {row.purpose}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm font-semibold">
                  {row.allocated_capacity}
                </td>
                <td className="px-4 py-3 text-sm">
                  {row.seats_used}
                </td>
                <td className="px-4 py-3 text-sm font-bold text-primary">
                  {row.invigilators}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Shell>
    );
  }

  if (tab === "students") {
    return (
      <Shell title="Student Allocation Report">
        <table className="w-full min-w-[900px]">
          <thead>
            <tr className="border-b border-border bg-surface-muted">
              {[
                "Student",
                "Name",
                "Date",
                "Session",
                "Hall",
                "Seat",
              ].map((h) => (
                <th
                  key={h}
                  className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, idx) => (
              <tr
                key={idx}
                className="border-b border-border last:border-0 hover:bg-surface-muted"
              >
                <td className="px-4 py-3 text-sm font-semibold text-sidebar">
                  {row.student_code}
                </td>
                <td className="px-4 py-3 text-sm">
                  {row.student_name}
                </td>
                <td className="px-4 py-3 text-sm">
                  {row.exam_date}
                </td>
                <td className="px-4 py-3 text-sm">
                  {row.session}
                </td>
                <td className="px-4 py-3 text-sm">
                  {row.hall}
                </td>
                <td className="px-4 py-3 text-sm font-bold text-primary">
                  {row.seat_number}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Shell>
    );
  }

  if (tab === "halls") {
    return (
      <Shell title="Hall Utilization Report">
        <table className="w-full min-w-[900px]">
          <thead>
            <tr className="border-b border-border bg-surface-muted">
              {[
                "Date",
                "Session",
                "Hall",
                "Capacity",
                "Seats Used",
                "Utilization",
              ].map((h) => (
                <th
                  key={h}
                  className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, idx) => (
              <tr
                key={idx}
                className="border-b border-border last:border-0 hover:bg-surface-muted"
              >
                <td className="px-4 py-3 text-sm">
                  {row.exam_date}
                </td>
                <td className="px-4 py-3 text-sm font-semibold text-sidebar">
                  {row.session}
                </td>
                <td className="px-4 py-3 text-sm">
                  {row.hall}
                </td>
                <td className="px-4 py-3 text-sm">
                  {row.allocated_capacity}
                </td>
                <td className="px-4 py-3 text-sm">
                  {row.seats_used}
                </td>
                <td className="px-4 py-3 text-sm font-bold text-primary">
                  {row.utilization_percent}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Shell>
    );
  }

  if (tab === "invigilators") {
    return (
      <Shell title="Invigilator Workload Report">
        <table className="w-full min-w-[800px]">
          <thead>
            <tr className="border-b border-border bg-surface-muted">
              {[
                "Staff ID",
                "Name",
                "Email",
                "Duties",
                "Sessions",
              ].map((h) => (
                <th
                  key={h}
                  className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={row.staff_id}
                className="border-b border-border last:border-0 hover:bg-surface-muted"
              >
                <td className="px-4 py-3 text-sm font-semibold text-sidebar">
                  #{row.staff_id}
                </td>
                <td className="px-4 py-3 text-sm">
                  {row.staff_name}
                </td>
                <td className="px-4 py-3 text-sm text-text-muted">
                  {row.email}
                </td>
                <td className="px-4 py-3 text-sm font-bold text-primary">
                  {row.duties}
                </td>
                <td className="px-4 py-3 text-xs text-text-muted">
                  {(row.sessions || [])
                    .map(
                      (s) =>
                        `${s.exam_date} ${s.session} · ${s.hall}`
                    )
                    .join(" | ")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Shell>
    );
  }

  return null;
}


function Shell({ title, children }) {
  return (
    <section className="rounded-2xl border border-border bg-surface shadow-sm">

      <div className="border-b border-border p-5 md:p-6">
        <h2 className="font-bold text-text">{title}</h2>
      </div>

      <div className="overflow-x-auto">{children}</div>

    </section>
  );
}


export default Reports;