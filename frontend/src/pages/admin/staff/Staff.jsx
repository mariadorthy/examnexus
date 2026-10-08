import { useEffect, useState } from "react";
import {
  Plus,
  Search,
  Eye,
  Pencil,
  Power,
  Users,
  Mail,
  Phone,
  Briefcase,
  RefreshCw,
  Loader2,
} from "lucide-react";

import StaffForm from "./StaffForm";
import { get, patch } from "../../../services/api";
import AdminSidebar from "../../../components/AdminSidebar";
import AdminTopbar from "../../../components/AdminTopbar";
import {
  validateCsv,
  importCsv,
} from "../../../services/api";
import CsvImport from "../../../components/admin/CsvImport/CsvImport";
function Staff({
  user,
  onLogout,
  onNavigate,
}) {
  const [sidebarOpen, setSidebarOpen] =
    useState(false);

  const [staffMembers, setStaffMembers] = useState([]);
  const [departments, setDepartments] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editingStaff, setEditingStaff] = useState(null);
  const [showCsvImport, setShowCsvImport] = useState(false);
  const [viewingStaff, setViewingStaff] = useState(null);
 useEffect(() => {
  loadData();
  loadDepartments();
}, []);
const loadDepartments = async () => {
  try {
    const data = await get("/departments");
    setDepartments(data);
  } catch (err) {
    console.error("Department loading error:", err);
  }
};
 const loadData = async () => {
  try {
    setLoading(true);
    setError("");

   const data = await get("/staff");

console.log("STAFF LIST RESPONSE:", data);

console.log(
  "STAFF STATUS VALUES:",
  data.map((staff) => ({
    id: staff.id,
    name: staff.name,
    is_active: staff.is_active,
    type: typeof staff.is_active,
  }))
);

const updatedStaff = data.find((staff) => staff.id === 7);

console.log(
  "STAFF ID 7 AFTER RELOAD:",
  updatedStaff
);

setStaffMembers(data);

  } catch (err) {

    console.error("Staff error:", err);

    setError(
      err.message ||
      "Unable to load staff."
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
  const handleView = (staff) => {
    setViewingStaff(staff);
  };

  const [statusLoading, setStatusLoading] =
    useState(null);
const handleToggleStatus = async (staff) => {

  try {

    setStatusLoading(staff.id);

    await patch(
      `/staff/${staff.id}/status`,
      {
        is_active: !staff.is_active,
      }
    );

    await loadData();

  } catch (err) {

    console.error(
      "Staff status error:",
      err
    );

    setError(
      err.message ||
      "Unable to update staff status."
    );

  } finally {

    setStatusLoading(null);

  }
};
  const handleFormSuccess = () => {
    setShowForm(false);
    setEditingStaff(null);
    loadData();
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

  return (
    <div className="min-h-screen bg-background">


      <AdminSidebar
        user={user}
        onLogout={onLogout}
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        activePage="Staff"
        onNavigate={onNavigate}
      />

      <main className="lg:ml-72">

        <AdminTopbar
          user={user}
          title="Staff"
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
                  Staff
                </h1>

                <p className="mt-2 text-sm text-text-muted">
                  Manage examination staff and their assignments.
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
<th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
  Status
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
                          colSpan="7"
                          className="px-5 py-12 text-center text-sm text-text-muted"
                        >
                          Loading staff...
                        </td>
                      </tr>
                    ) : filteredStaff.length === 0 ? (
                      <tr>
                        <td
                          colSpan="7"
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
      staff.availability
        ? "bg-accent-light text-success"
        : "bg-danger/10 text-danger"
    }`}
  >
    {staff.availability
      ? "Available"
      : "Unavailable"}
  </span>
</td>

<td className="px-5 py-4">
  <span
    className={`rounded-full px-3 py-1 text-xs font-semibold ${
      staff.is_active
        ? "bg-accent-light text-success"
        : "bg-danger/10 text-danger"
    }`}
  >
    {staff.is_active
      ? "Active"
      : "Inactive"}
  </span>
</td>

                          <td className="px-5 py-4">
                            <div className="flex justify-end gap-2">
                              <button
                                type="button"
                                onClick={() => handleView(staff)}
                                className="rounded-lg p-2 text-sidebar transition hover:bg-surface-muted"
                                aria-label={`View ${staff.name}`}
                              >
                                <Eye size={17} />
                              </button>

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
                                onClick={() =>
                                  handleToggleStatus(staff)
                                }
                                disabled={statusLoading === staff.id}
                                className={`rounded-lg p-2 transition ${staff.is_active
                                    ? "text-danger hover:bg-danger/10"
                                    : "text-success hover:bg-accent-light"
                                  }`}
                                title={
                                  staff.is_active
                                    ? "Deactivate staff"
                                    : "Activate staff"
                                }
                              >
                                {statusLoading === staff.id ? (
                                  <Loader2
                                    size={17}
                                    className="animate-spin"
                                  />
                                ) : (
                                  <Power size={17} />
                                )}
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
      </main>
      {viewingStaff && (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm">
    <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl border border-border bg-surface shadow-2xl">
      <div className="flex items-center justify-between border-b border-border px-6 py-5">
        <div>
          <p className="text-sm font-semibold uppercase tracking-widest text-accent">
            Staff Management
          </p>

          <h2 className="mt-1 text-xl font-bold text-text">
            Staff Details
          </h2>
        </div>

        <button
          type="button"
          onClick={() => setViewingStaff(null)}
          className="rounded-lg p-2 text-text-muted transition hover:bg-surface-muted hover:text-text"
          aria-label="Close staff details"
        >
          ✕
        </button>
      </div>

      <div className="p-6">
        <div className="mb-6 flex items-center gap-4">
          <div className="flex h-16 w-16 items-center justify-center overflow-hidden rounded-full bg-accent-light text-xl font-bold text-primary">
            {viewingStaff.image ? (
              <img
                src={viewingStaff.image}
                alt={viewingStaff.name}
                className="h-full w-full object-cover"
              />
            ) : (
              viewingStaff.name
                ?.charAt(0)
                .toUpperCase()
            )}
          </div>

          <div>
            <h3 className="text-xl font-bold text-text">
              {viewingStaff.name}
            </h3>

            <p className="text-sm text-text-muted">
              {viewingStaff.email}
            </p>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <DetailItem
            label="Department"
            value={getDepartmentName(
              viewingStaff.department_id
            )}
          />

          <DetailItem
            label="Designation"
            value={viewingStaff.designation}
          />

          <DetailItem
            label="Contact Number"
            value={
              viewingStaff.contact_no ||
              "Not provided"
            }
          />

          <DetailItem
            label="Date of Birth"
            value={
              viewingStaff.dob ||
              "Not provided"
            }
          />

          <DetailItem
            label="Gender"
            value={
              viewingStaff.gender ||
              "Not provided"
            }
          />

          <DetailItem
            label="Assigned Batch"
            value={
              viewingStaff.assigned_batch ||
              "Not provided"
            }
          />

          <DetailItem
            label="Assigned Courses"
            value={
              viewingStaff.assigned_courses ||
              "Not provided"
            }
          />

          <DetailItem
            label="Availability"
            value={
              viewingStaff.availability
                ? "Available"
                : "Unavailable"
            }
          />

          <DetailItem
            label="Account Status"
            value={
              viewingStaff.is_active
                ? "Active"
                : "Inactive"
            }
          />

        </div>
      </div>
    </div>
  </div>
)}

<CsvImport
  entity="staff"
  isOpen={showCsvImport}
  onClose={() => setShowCsvImport(false)}
  onValidate={validateCsv}
  onImport={importCsv}
/>

{showForm && (
  <StaffForm
    staff={editingStaff}
    departments={departments}
    onCancel={() => {
      setShowForm(false);
      setEditingStaff(null);
    }}
    onSuccess={handleFormSuccess}
  />
)}
    </div>
  );
}
function DetailItem({ label, value }) {
  return (
    <div className="rounded-xl border border-border bg-surface-muted p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
        {label}
      </p>

      <p className="mt-1 text-sm font-semibold text-text">
        {value}
      </p>
    </div>
  );
}
export default Staff;
