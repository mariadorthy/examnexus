import { useEffect, useState } from "react";
import {
  Plus,
  Search,
  Pencil,
  Eye,
  Power,
  Building2,
  CheckCircle2,
  Wrench,
  RefreshCw,
  Loader2,
  X,
} from "lucide-react";

import { get, patch } from "../../../services/api";

import HallForm from "./HallForm";
import AdminSidebar from "../../../components/AdminSidebar";
import AdminTopbar from "../../../components/AdminTopbar";
import CsvImport from "../../../components/admin/CsvImport/CsvImport";
function Halls({
  user,
  onLogout,
  onNavigate,
}) {
  const [sidebarOpen, setSidebarOpen] =
    useState(false);
  const [halls, setHalls] = useState([]);
  const [courses, setCourses] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editingHall, setEditingHall] = useState(null);
  const [showCsvImport, setShowCsvImport] = useState(false);
const [viewingHall, setViewingHall] = useState(null);
const [statusLoading, setStatusLoading] = useState(null);
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError("");

      const [hallsData, coursesData] =
  await Promise.all([
    get("/halls/"),
    get("/courses/"),
  ]);

setHalls(hallsData);
setCourses(coursesData);
    } catch (err) {
      console.error("Hall loading error:", err);

      setError(
        "Unable to load hall data. Please make sure the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  const getCourseName = (courseId) => {
    if (!courseId) {
      return "Not assigned";
    }

    const course = courses.find(
      (item) => item.id === courseId
    );

    return course
      ? `${course.course_code} - ${course.course_name}`
      : "Unknown Course";
  };

  const handleAdd = () => {
    setEditingHall(null);
    setShowForm(true);
  };

  const handleEdit = (hall) => {
    setEditingHall(hall);
    setShowForm(true);
  };
const handleView = async (hall) => {
  try {
    const response = await get(`/halls/${hall.id}`);
    setViewingHall(response.hall);
  } catch (err) {
    console.error("Hall details error:", err);

    setError(
      err.message ||
      "Unable to load hall details."
    );
  }
};

const handleToggleStatus = async (hall) => {
  try {
    setStatusLoading(hall.id);

    await patch(
      `/halls/${hall.id}/status`,
      {
        is_active: !hall.is_active,
      }
    );

    await loadData();
  } catch (err) {
    console.error("Hall status error:", err);

    setError(
      err.message ||
      "Unable to update hall status."
    );
  } finally {
    setStatusLoading(null);
  }
};
  const handleFormSuccess = () => {
    setShowForm(false);
    setEditingHall(null);
    loadData();
  };

  const filteredHalls = halls.filter((hall) => {
  const searchValue = search.toLowerCase();

  return (
    hall.name?.toLowerCase().includes(searchValue) ||
    hall.building_name
      ?.toLowerCase()
      .includes(searchValue) ||
    hall.room_type
      ?.toLowerCase()
      .includes(searchValue) ||
    getCourseName(hall.assigned_course_id)
      .toLowerCase()
      .includes(searchValue)
  );
});

const usableHalls = halls.filter(
  (hall) =>
    hall.is_active &&
    hall.is_available &&
    !hall.is_under_maintenance &&
    Number(hall.examination_capacity) > 0
);

const totalUsableCapacity = usableHalls.reduce(
  (total, hall) =>
    total + Number(hall.examination_capacity || 0),
  0
);

const accessibleUsableHalls = usableHalls.filter(
  (hall) => hall.is_accessible
);

  return (
    <div className="min-h-screen bg-background">

      
    <AdminSidebar
      user={user}
      onLogout={onLogout}
      sidebarOpen={sidebarOpen}
      setSidebarOpen={setSidebarOpen}
      activePage="Halls"
      onNavigate={onNavigate}
    />

    <main className="lg:ml-72">

      <AdminTopbar
        user={user}
        title="Examination Halls"
        section="Administration"
        onOpenSidebar={() =>
          setSidebarOpen(true)
        }
      />

      <div className="p-5 md:p-8">
      {/* Header */}

      <div className="border-b border-border bg-surface">
        <div className="flex flex-col gap-4 px-5 py-6 md:px-8 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-widest text-accent">
              Administration
            </p>

            <h1 className="mt-1 text-2xl font-bold text-text md:text-3xl">
              Examination Halls
            </h1>

            <p className="mt-2 text-sm text-text-muted">
              Manage halls, capacities and examination assignments.
            </p>
          </div>

<button
  type="button"
  onClick={() => setShowCsvImport(true)}
  className="flex w-fit items-center gap-2 rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold text-sidebar transition hover:bg-surface-muted"
>
  Import CSV
</button>
          <button
            type="button"
            onClick={handleAdd}
            className="flex w-fit items-center gap-2 rounded-xl bg-sidebar px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-sidebar/10 transition hover:bg-primary"
          >
            <Plus size={18} />
            Add Hall
          </button>
        </div>
      </div>

      <div className="p-5 md:p-8">
        {/* Error */}

        {error && (
          <div className="mb-6 flex items-center justify-between gap-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            <span>{error}</span>

            <button
              type="button"
              onClick={loadData}
              className="flex items-center gap-1 font-semibold"
            >
              <RefreshCw size={15} />
              Retry
            </button>
          </div>
        )}

    {/* Statistics */}

<div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">

  {/* Total Halls */}
  <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-text-muted">
          Total Halls
        </p>

        <p className="mt-2 text-3xl font-bold text-text">
          {loading ? "..." : halls.length}
        </p>
      </div>

      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-light text-primary">
        <Building2 size={21} />
      </div>
    </div>
  </div>

  {/* Usable Halls */}
  <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-text-muted">
          Usable Halls
        </p>

        <p className="mt-2 text-3xl font-bold text-text">
          {loading ? "..." : usableHalls.length}
        </p>
      </div>

      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-light text-success">
        <CheckCircle2 size={21} />
      </div>
    </div>
  </div>

  {/* Maintenance */}
  <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-text-muted">
          Maintenance
        </p>

        <p className="mt-2 text-3xl font-bold text-text">
          {loading
            ? "..."
            : halls.filter(
                (hall) => hall.is_under_maintenance
              ).length}
        </p>
      </div>

      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-light text-warning">
        <Wrench size={21} />
      </div>
    </div>
  </div>

  {/* Exam Capacity */}
  <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-text-muted">
          Exam Capacity
        </p>

        <p className="mt-2 text-3xl font-bold text-text">
          {loading ? "..." : totalUsableCapacity}
        </p>

        <p className="mt-1 text-xs text-text-muted">
          Usable seats
        </p>
      </div>

      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-light text-primary">
        <Building2 size={21} />
      </div>
    </div>
  </div>

  {/* Accessible Halls */}
  <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-text-muted">
          Accessible Halls
        </p>

        <p className="mt-2 text-3xl font-bold text-text">
          {loading ? "..." : accessibleUsableHalls.length}
        </p>

        <p className="mt-1 text-xs text-text-muted">
          Among usable halls
        </p>
      </div>

      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-light text-success">
        <CheckCircle2 size={21} />
      </div>
    </div>
  </div>

</div>

        {/* Search */}

        <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="relative w-full max-w-md">
            <Search
              size={18}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-text-light"
            />

            <input
              type="text"
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
              placeholder="Search halls..."
              className="w-full rounded-xl border border-border bg-surface py-3 pl-10 pr-4 text-sm text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
            />
          </div>

          <button
            type="button"
            onClick={loadData}
            className="flex w-fit items-center gap-2 rounded-xl border border-border bg-surface px-4 py-3 text-sm font-semibold text-sidebar transition hover:border-accent"
          >
            <RefreshCw size={16} />
            Refresh
          </button>
        </div>

        {/* Hall Cards */}

        {loading ? (
          <div className="rounded-2xl border border-border bg-surface px-5 py-12 text-center text-sm text-text-muted shadow-sm">
            Loading halls...
          </div>
        ) : filteredHalls.length === 0 ? (
          <div className="rounded-2xl border border-border bg-surface px-5 py-12 text-center shadow-sm">
            <Building2
              size={34}
              className="mx-auto text-text-light"
            />

            <p className="mt-3 text-sm font-semibold text-text">
              No halls found
            </p>

            <p className="mt-1 text-sm text-text-muted">
              Add an examination hall to get started.
            </p>
          </div>
        ) : (
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {filteredHalls.map((hall) => {
              const available =
  hall.is_available &&
  hall.is_active &&
  !hall.is_under_maintenance &&
  Number(hall.examination_capacity) > 0;

              return (
                <div
                  key={hall.id}
                  className="rounded-2xl border border-border bg-surface p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
                >
                  {/* Card Header */}

                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-center gap-3">
                      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-light text-primary">
                        <Building2 size={21} />
                      </div>

                      <div>
                        <h2 className="font-bold text-text">
                          {hall.name}
                        </h2>

                        <p className="text-xs text-text-muted">
                          {hall.building_name}
                        </p>
                      </div>
                    </div>

                    <span
                      className={`rounded-full px-3 py-1 text-xs font-semibold ${
                        available
                          ? "bg-accent-light text-success"
                          : hall.is_under_maintenance
                            ? "bg-yellow-50 text-warning"
                            : "bg-red-50 text-danger"
                      }`}
                    >
                      {hall.is_under_maintenance
                        ? "Maintenance"
                        : available
                          ? "Available"
                          : "Unavailable"}
                    </span>
                  </div>
<div className="mt-3">
  <span
    className={`rounded-full px-3 py-1 text-xs font-semibold ${
      hall.is_active
        ? "bg-accent-light text-success"
        : "bg-danger/10 text-danger"
    }`}
  >
    {hall.is_active ? "Active" : "Inactive"}
  </span>
</div>
                  {/* Details */}

                  <div className="mt-5 grid grid-cols-2 gap-3">
                    <InfoItem
                      label="Floor"
                      value={`Floor ${hall.floor_no}`}
                    />

                    <InfoItem
                      label="Room Type"
                      value={hall.room_type}
                    />

                    <InfoItem
                      label="Capacity"
                      value={hall.capacity}
                    />

                    <InfoItem
                      label="Exam Capacity"
                      value={hall.examination_capacity}
                    />
                  </div>

                  {/* Assignment */}

                  <div className="mt-4 rounded-xl bg-surface-muted p-4">
                    <p className="text-xs font-semibold uppercase tracking-wider text-text-light">
                      Assigned Course
                    </p>

                    <p className="mt-1 text-sm font-medium text-text">
                      {getCourseName(
                        hall.assigned_course_id
                      )}
                    </p>

                    {hall.assigned_batch && (
                      <p className="mt-1 text-xs text-text-muted">
                        Batch: {hall.assigned_batch}
                      </p>
                    )}
                  </div>

                  {/* Amenities */}

                  {hall.amenities && (
                    <div className="mt-4">
                      <p className="text-xs font-semibold uppercase tracking-wider text-text-light">
                        Amenities
                      </p>

                      <p className="mt-1 line-clamp-2 text-sm text-text-muted">
                        {hall.amenities}
                      </p>
                    </div>
                  )}

                  {/* Actions */}
<div className="mt-5 flex justify-end gap-2 border-t border-border pt-4">
  <button
    type="button"
    onClick={() => handleView(hall)}
    className="rounded-lg p-2 text-sidebar transition hover:bg-surface-muted"
    aria-label={`View ${hall.name}`}
    title="View hall"
  >
    <Eye size={17} />
  </button>

  <button
    type="button"
    onClick={() => handleEdit(hall)}
    className="rounded-lg p-2 text-primary transition hover:bg-accent-light"
    aria-label={`Edit ${hall.name}`}
    title="Edit hall"
  >
    <Pencil size={17} />
  </button>

  <button
    type="button"
    onClick={() => handleToggleStatus(hall)}
    disabled={statusLoading === hall.id}
    className={`rounded-lg p-2 transition ${
      hall.is_active
        ? "text-danger hover:bg-danger/10"
        : "text-success hover:bg-accent-light"
    }`}
    title={
      hall.is_active
        ? "Deactivate hall"
        : "Activate hall"
    }
  >
    {statusLoading === hall.id ? (
      <Loader2
        size={17}
        className="animate-spin"
      />
    ) : (
      <Power size={17} />
    )}
  </button>
</div>
              
                </div>
              );
            })}
          </div>
        )}
      </div>
            </div>
        </main>

    {/* Hall Details Modal */}
    {viewingHall && (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm">
        <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl border border-border bg-surface shadow-2xl">

          <div className="flex items-center justify-between border-b border-border px-6 py-5">
            <div>
              <p className="text-sm font-semibold uppercase tracking-widest text-accent">
                Hall Management
              </p>

              <h2 className="mt-1 text-xl font-bold text-text">
                Hall Details
              </h2>
            </div>

            <button
              type="button"
              onClick={() => setViewingHall(null)}
              className="rounded-lg p-2 text-text-muted transition hover:bg-surface-muted hover:text-text"
              aria-label="Close hall details"
            >
              <X size={20} />
            </button>
                   </div>

          {/* Hall Details Content */}
          <div className="p-6">
            {error && (
              <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <div className="grid gap-4 md:grid-cols-2">
              <InfoItem
                label="Hall Name"
                value={viewingHall.name}
              />

              <InfoItem
                label="Building"
                value={viewingHall.building_name}
              />

              <InfoItem
                label="Floor"
                value={`Floor ${viewingHall.floor_no}`}
              />

              <InfoItem
                label="Room Type"
                value={viewingHall.room_type}
              />

              <InfoItem
                label="Total Capacity"
                value={viewingHall.capacity}
              />

              <InfoItem
                label="Examination Capacity"
                value={viewingHall.examination_capacity}
              />

              <InfoItem
                label="Availability"
                value={
  viewingHall.is_active &&
  viewingHall.is_available &&
  !viewingHall.is_under_maintenance &&
  Number(viewingHall.examination_capacity) > 0
    ? "Usable for Examination"
    : "Not Usable"
}
              />

              <InfoItem
                label="Account Status"
                value={
                  viewingHall.is_active
                    ? "Active"
                    : "Inactive"
                }
              />

              <InfoItem
                label="Maintenance"
                value={
                  viewingHall.is_under_maintenance
                    ? "Under Maintenance"
                    : "Normal"
                }
              />

              <InfoItem
                label="Accessibility"
                value={
                  viewingHall.is_accessible
                    ? "Accessible"
                    : "Not Accessible"
                }
              />

              <InfoItem
                label="Assigned Course"
                value={getCourseName(
                  viewingHall.assigned_course_id
                )}
              />

              <InfoItem
                label="Assigned Batch"
                value={
                  viewingHall.assigned_batch ||
                  "Not assigned"
                }
              />
            </div>

            {viewingHall.amenities && (
              <div className="mt-5 rounded-xl border border-border bg-surface-muted p-4">
                <p className="text-xs font-semibold uppercase tracking-wider text-text-light">
                  Amenities
                </p>

                <p className="mt-2 text-sm text-text">
                  {viewingHall.amenities}
                </p>
              </div>
            )}

            <div className="mt-6 flex justify-end border-t border-border pt-5">
              <button
                type="button"
                onClick={() => setViewingHall(null)}
                className="flex items-center gap-2 rounded-xl bg-sidebar px-5 py-3 text-sm font-semibold text-white transition hover:bg-primary"
              >
                <X size={17} />
                Close
              </button>
            </div>
          </div>

        </div>
      </div>
    )}

    {/* Hall Add/Edit Modal */}
    <CsvImport
  entity="halls"
  isOpen={showCsvImport}
  onClose={() => setShowCsvImport(false)}
/>
    {showForm && (
      <HallForm
        hall={editingHall}
        courses={courses}
        onCancel={() => {
          setShowForm(false);
          setEditingHall(null);
        }}
        onSuccess={handleFormSuccess}
      />

      
    )}

    </div>
  );
}

function InfoItem({ label, value }) {
  return (
    <div className="rounded-xl border border-border bg-surface-muted p-3">
      <p className="text-xs text-text-light">
        {label}
      </p>

      <p className="mt-1 text-sm font-semibold text-text">
        {value}
      </p>
    </div>
  );
}

export default Halls;
