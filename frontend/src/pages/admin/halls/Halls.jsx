import { useEffect, useState } from "react";
import {
  Plus,
  Search,
  Pencil,
  Trash2,
  Building2,
  CheckCircle2,
  Wrench,
  RefreshCw,
} from "lucide-react";

import HallForm from "./HallForm";
import { get } from "../../../services/api";
import AdminSidebar from "../../../components/AdminSidebar";
import AdminTopbar from "../../../components/AdminTopbar";

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

  const handleFormSuccess = () => {
    setShowForm(false);
    setEditingHall(null);
    loadData();
  };

  const handleDelete = async (hall) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete ${hall.name}?`
    );

    if (!confirmed) {
      return;
    }

    /*
     * Current Flask backend does not have:
     * DELETE /api/halls/<id>
     */

    window.alert(
      "Delete functionality will be connected after the DELETE hall API is added."
    );
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

  if (showForm) {
    return (
      <HallForm
        hall={editingHall}
        courses={courses}
        onCancel={() => {
          setShowForm(false);
          setEditingHall(null);
        }}
        onSuccess={handleFormSuccess}
      />
    );
  }

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

        <div className="mb-6 grid gap-4 sm:grid-cols-3">
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

          <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-muted">
                  Available
                </p>

                <p className="mt-2 text-3xl font-bold text-text">
                  {loading
                    ? "..."
                    : halls.filter(
                        (hall) =>
                          hall.is_available &&
                          hall.is_active &&
                          !hall.is_under_maintenance
                      ).length}
                </p>
              </div>

              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-light text-success">
                <CheckCircle2 size={21} />
              </div>
            </div>
          </div>

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
                        (hall) =>
                          hall.is_under_maintenance
                      ).length}
                </p>
              </div>

              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-light text-warning">
                <Wrench size={21} />
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
                !hall.is_under_maintenance;

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
                      onClick={() => handleEdit(hall)}
                      className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-primary transition hover:bg-accent-light"
                    >
                      <Pencil size={16} />
                      Edit
                    </button>

                    <button
                      type="button"
                      onClick={() => handleDelete(hall)}
                      className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-danger transition hover:bg-red-50"
                    >
                      <Trash2 size={16} />
                      Delete
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
