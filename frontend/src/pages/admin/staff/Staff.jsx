import { useEffect, useState } from "react";
import {
  Plus,
  Search,
  Pencil,
  Trash2,
  Users,
  Mail,
  Phone,
  Briefcase,
  RefreshCw,
} from "lucide-react";

import StaffForm from "./StaffForm";
import { get } from "../../services/api";
const API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";

function Staff() {
  const [staffMembers, setStaffMembers] = useState([]);
  const [departments, setDepartments] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editingStaff, setEditingStaff] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError("");

      const [staffData, departmentsData] =
  await Promise.all([
    get("/staff/"),
    get("/departments/"),
  ]);

setStaffMembers(staffData);
setDepartments(departmentsData);
} catch (err) {
      console.error("Staff loading error:", err);

      setError(
        "Unable to load staff data. Please make sure the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  const getDepartmentName = (departmentId) => {
    const department = departments.find(
      (item) => item.id === departmentId
    );

    return department
      ? department.department_name
      : "Unknown Department";
  };

  const handleAdd = () => {
    setEditingStaff(null);
    setShowForm(true);
  };

  const handleEdit = (staff) => {
    setEditingStaff(staff);
    setShowForm(true);
  };

  const handleFormSuccess = () => {
    setShowForm(false);
    setEditingStaff(null);
    loadData();
  };

  const handleDelete = async (staff) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete ${staff.name}?`
    );

    if (!confirmed) {
      return;
    }

    /*
     * NOTE:
     * Your current Flask backend does not yet have
     * a DELETE /api/staff/<id> route.
     *
     * This is intentionally disabled until that route
     * is added.
     */

    window.alert(
      "Delete functionality will be connected after the DELETE staff API is added."
    );
  };

  const filteredStaff = staffMembers.filter((staff) => {
    const searchValue = search.toLowerCase();

    return (
      staff.name?.toLowerCase().includes(searchValue) ||
      staff.email?.toLowerCase().includes(searchValue) ||
      staff.designation?.toLowerCase().includes(searchValue) ||
      getDepartmentName(staff.department_id)
        .toLowerCase()
        .includes(searchValue)
    );
  });

  if (showForm) {
    return (
      <StaffForm
        staff={editingStaff}
        departments={departments}
        onCancel={() => {
          setShowForm(false);
          setEditingStaff(null);
        }}
        onSuccess={handleFormSuccess}
      />
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}

      <div className="border-b border-border bg-surface">
        <div className="flex flex-col gap-4 px-5 py-6 md:px-8 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-widest text-accent">
              Administration
            </p>

            <h1 className="mt-1 text-2xl font-bold text-text md:text-3xl">
              Staff
            </h1>

            <p className="mt-2 text-sm text-text-muted">
              Manage examination staff and their assignments.
            </p>
          </div>

          <button
            type="button"
            onClick={handleAdd}
            className="flex w-fit items-center gap-2 rounded-xl bg-sidebar px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-sidebar/10 transition hover:bg-primary"
          >
            <Plus size={18} />
            Add Staff
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

        {/* Summary */}

        <div className="mb-6 grid gap-4 sm:grid-cols-2">
          <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-muted">
                  Total Staff
                </p>

                <p className="mt-2 text-3xl font-bold text-text">
                  {loading ? "..." : staffMembers.length}
                </p>
              </div>

              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-light text-primary">
                <Users size={21} />
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-muted">
                  Available Staff
                </p>

                <p className="mt-2 text-3xl font-bold text-text">
                  {loading
                    ? "..."
                    : staffMembers.filter(
                        (staff) =>
                          staff.availability &&
                          staff.is_active
                      ).length}
                </p>
              </div>

              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-light text-primary">
                <Briefcase size={21} />
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
              placeholder="Search staff..."
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

        {/* Table */}

        <div className="overflow-hidden rounded-2xl border border-border bg-surface shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px]">
              <thead className="border-b border-border bg-surface-muted">
                <tr>
                  <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Staff
                  </th>

                  <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Department
                  </th>

                  <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Contact
                  </th>

                  <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Designation
                  </th>

                  <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Availability
                  </th>

                  <th className="px-5 py-4 text-right text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Actions
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-border">
                {loading ? (
                  <tr>
                    <td
                      colSpan="6"
                      className="px-5 py-12 text-center text-sm text-text-muted"
                    >
                      Loading staff...
                    </td>
                  </tr>
                ) : filteredStaff.length === 0 ? (
                  <tr>
                    <td
                      colSpan="6"
                      className="px-5 py-12 text-center"
                    >
                      <Users
                        size={32}
                        className="mx-auto text-text-light"
                      />

                      <p className="mt-3 text-sm font-semibold text-text">
                        No staff found
                      </p>

                      <p className="mt-1 text-sm text-text-muted">
                        Add a staff member to get started.
                      </p>
                    </td>
                  </tr>
                ) : (
                  filteredStaff.map((staff) => (
                    <tr
                      key={staff.id}
                      className="transition hover:bg-surface-muted"
                    >
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                          <div className="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-full bg-accent-light font-bold text-primary">
                            {staff.image ? (
                              <img
                                src={staff.image}
                                alt={staff.name}
                                className="h-full w-full object-cover"
                              />
                            ) : (
                              staff.name
                                ?.charAt(0)
                                .toUpperCase()
                            )}
                          </div>

                          <div>
                            <p className="font-semibold text-text">
                              {staff.name}
                            </p>

                            <p className="text-xs text-text-muted">
                              {staff.email}
                            </p>
                          </div>
                        </div>
                      </td>

                      <td className="px-5 py-4 text-sm text-text">
                        {getDepartmentName(
                          staff.department_id
                        )}
                      </td>

                      <td className="px-5 py-4">
                        <div className="space-y-1 text-sm">
                          <div className="flex items-center gap-2 text-text-muted">
                            <Mail size={14} />
                            {staff.email}
                          </div>

                          {staff.contact_no && (
                            <div className="flex items-center gap-2 text-text-muted">
                              <Phone size={14} />
                              {staff.contact_no}
                            </div>
                          )}
                        </div>
                      </td>

                      <td className="px-5 py-4 text-sm text-text">
                        {staff.designation}
                      </td>

                      <td className="px-5 py-4">
                        <span
                          className={`rounded-full px-3 py-1 text-xs font-semibold ${
                            staff.availability &&
                            staff.is_active
                              ? "bg-accent-light text-success"
                              : "bg-red-50 text-danger"
                          }`}
                        >
                          {staff.availability &&
                          staff.is_active
                            ? "Available"
                            : "Unavailable"}
                        </span>
                      </td>

                      <td className="px-5 py-4">
                        <div className="flex justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => handleEdit(staff)}
                            className="rounded-lg p-2 text-primary transition hover:bg-accent-light"
                            aria-label={`Edit ${staff.name}`}
                          >
                            <Pencil size={17} />
                          </button>

                          <button
                            type="button"
                            onClick={() => handleDelete(staff)}
                            className="rounded-lg p-2 text-danger transition hover:bg-red-50"
                            aria-label={`Delete ${staff.name}`}
                          >
                            <Trash2 size={17} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Staff;
