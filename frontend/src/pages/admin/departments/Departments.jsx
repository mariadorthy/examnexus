import { useEffect, useState } from "react";
import {
  Building2,
  Plus,
  Search,
  RefreshCw,
  X,
  Pencil,
  Power,
  Eye,
  Loader2,
} from "lucide-react";

import AdminSidebar from "../../../components/AdminSidebar";
import AdminTopbar from "../../../components/AdminTopbar";
import DepartmentForm from "./DepartmentForm";
import { get, patch } from "../../../services/api";
import {
  validateCsv,
  importCsv,
} from "../../../services/api";
import CsvImport from "../../../components/admin/CsvImport/CsvImport";
const API_URL = "http://127.0.0.1:5000/api/departments";


function Departments({
  user,
  onLogout,
  onNavigate,
}) {

  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [departments, setDepartments] = useState([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  const [search, setSearch] = useState("");

  const [showForm, setShowForm] = useState(false);
const [showCsvImport, setShowCsvImport] = useState(false);
  const [editingDepartment, setEditingDepartment] =
    useState(null);

  const [viewingDepartment, setViewingDepartment] =
    useState(null);

  const [detailsLoading, setDetailsLoading] =
    useState(false);

  const [statusLoading, setStatusLoading] =
    useState(null);

  // =====================================================
  // LOAD DEPARTMENTS
  // =====================================================

  const loadDepartments = async () => {

    try {

      setLoading(true);
      setError("");

      const data = await get("/departments");

      setDepartments(data);

    } catch (err) {

      console.error("Departments error:", err);

      setError(
        "Unable to load departments. Please make sure the backend is running."
      );

    } finally {

      setLoading(false);

    }
  };


  useEffect(() => {

    loadDepartments();

  }, []);


  // =====================================================
  // SEARCH
  // =====================================================

  const filteredDepartments = departments.filter(
    (department) => {

      const searchText = search
        .trim()
        .toLowerCase();

      if (!searchText) {
        return true;
      }

      return (
        department.department_code
          ?.toLowerCase()
          .includes(searchText) ||

        department.department_name
          ?.toLowerCase()
          .includes(searchText)
      );

    }
  );

  const handleEdit = (department) => {

    setEditingDepartment(department);

  };
  const handleToggleStatus = async (department) => {

    try {

      setStatusLoading(department.id);

      await patch(
        `/departments/${department.id}/status`,
        {
          is_active: !department.is_active,
        }
      );

      await loadDepartments();

    } catch (err) {

      console.error(
        "Department status error:",
        err
      );

      setError(
        err.message ||
        "Unable to update department status."
      );

    } finally {

      setStatusLoading(null);

    }
  };
  const handleViewDetails = async (department) => {

    try {

      setDetailsLoading(true);


      const data = await get(
        `/departments/${department.id}`
      );

      setViewingDepartment(data);

    } catch (err) {

      console.error(
        "Department details error:",
        err
      );

      setError(
        err.message ||
        "Unable to load department details."
      );

    } finally {

      setDetailsLoading(false);

    }
  };

  // =====================================================
  // CREATE SUCCESS
  // =====================================================

  const handleFormSuccess = () => {

    setShowForm(false);
    setEditingDepartment(null);

    loadDepartments();

  };


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
        activePage="Departments"
        onNavigate={onNavigate}
      />


      {/* ================================================= */}
      {/* MAIN */}
      {/* ================================================= */}

      <main className="lg:ml-72">

        {/* TOPBAR */}

        <AdminTopbar
          user={user}
          title="Departments"
          section="Administration"
          onOpenSidebar={() => setSidebarOpen(true)}
        />


        {/* ================================================= */}
        {/* CONTENT */}
        {/* ================================================= */}

        <div className="p-5 md:p-8">

          {/* ================================================= */}
          {/* PAGE HEADER */}
          {/* ================================================= */}

          <section className="mb-7">

            <div className="flex flex-col justify-between gap-5 md:flex-row md:items-end">

              <div>

                <p className="text-sm font-medium text-accent">
                  Academic Management
                </p>

                <h2 className="mt-1 text-2xl font-bold text-text md:text-3xl">
                  Departments
                </h2>

                <p className="mt-2 max-w-2xl text-sm leading-6 text-text-muted">
                  Manage the academic departments available
                  in the examination management system.
                </p>

              </div>


<button
  type="button"
  onClick={() => setShowCsvImport(true)}
  className="
    flex
    w-full
    items-center
    justify-center
    gap-2
    rounded-xl
    border
    border-border
    bg-surface
    px-5
    py-3
    text-sm
    font-semibold
    text-sidebar
    transition
    hover:bg-surface-muted
    md:w-auto
  "
>
  Import CSV
</button>

              {/* Add button */}

              <button
                type="button"
                onClick={() => {

                  setEditingDepartment(null);
                  setShowForm(true);

                }}
                className="
                  flex
                  w-full
                  items-center
                  justify-center
                  gap-2
                  rounded-xl
                  bg-sidebar
                  px-5
                  py-3
                  text-sm
                  font-semibold
                  text-white
                  shadow-lg
                  shadow-sidebar/10
                  transition
                  hover:bg-primary
                  md:w-auto
                "
              >
                <Plus size={18} />

                Add Department
              </button>

            </div>

          </section>


          {/* ================================================= */}
          {/* ERROR */}
          {/* ================================================= */}

          {error && (

            <div
              className="
                mb-6
                flex
                items-start
                justify-between
                gap-4
                rounded-xl
                border
                border-red-200
                bg-red-50
                px-4
                py-3
                text-sm
                text-red-700
              "
            >

              <p>{error}</p>

              <button
                type="button"
                onClick={loadDepartments}
                className="font-semibold underline"
              >
                Retry
              </button>

            </div>

          )}


          {/* ================================================= */}
          {/* TOOLBAR */}
          {/* ================================================= */}

          <div
            className="
              mb-5
              flex
              flex-col
              gap-3
              rounded-2xl
              border
              border-border
              bg-surface
              p-4
              shadow-sm
              sm:flex-row
              sm:items-center
              sm:justify-between
            "
          >

            {/* Search */}

            <div className="relative w-full sm:max-w-md">

              <Search
                size={18}
                className="
                  absolute
                  left-3
                  top-1/2
                  -translate-y-1/2
                  text-text-light
                "
              />

              <input
                type="text"
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
                placeholder="Search departments..."
                className="
                  w-full
                  rounded-xl
                  border
                  border-border
                  bg-surface-muted
                  py-2.5
                  pl-10
                  pr-10
                  text-sm
                  text-text
                  outline-none
                  transition
                  placeholder:text-text-light
                  focus:border-primary
                  focus:ring-4
                  focus:ring-primary/10
                "
              />

              {search && (

                <button
                  type="button"
                  onClick={() => setSearch("")}
                  className="
                    absolute
                    right-3
                    top-1/2
                    -translate-y-1/2
                    text-text-light
                    hover:text-text
                  "
                  aria-label="Clear search"
                >
                  <X size={17} />
                </button>

              )}

            </div>


            {/* Refresh */}

            <button
              type="button"
              onClick={loadDepartments}
              disabled={loading}
              className="
                flex
                items-center
                justify-center
                gap-2
                rounded-xl
                border
                border-border
                bg-surface
                px-4
                py-2.5
                text-sm
                font-medium
                text-sidebar
                transition
                hover:bg-surface-muted
                disabled:cursor-not-allowed
                disabled:opacity-50
              "
            >

              <RefreshCw
                size={17}
                className={loading ? "animate-spin" : ""}
              />

              Refresh

            </button>

          </div>


          {/* ================================================= */}
          {/* TABLE */}
          {/* ================================================= */}

          <div
            className="
              overflow-hidden
              rounded-2xl
              border
              border-border
              bg-surface
              shadow-sm
            "
          >

            <div className="overflow-x-auto">

              <table className="w-full min-w-[650px]">

                <thead>

                  <tr className="border-b border-border bg-surface-muted">

                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                      #
                    </th>

                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                      Department Code
                    </th>

                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                      Department Name
                    </th>

                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                      Status
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                      Actions
                    </th>
                  </tr>

                </thead>


                <tbody>

                  {loading ? (

                    <tr>

                      <td
                        colSpan="5"
                        className="px-6 py-12 text-center text-sm text-text-muted"
                      >
                        Loading departments...
                      </td>

                    </tr>

                  ) : filteredDepartments.length === 0 ? (

                    <tr>

                      <td
                        colSpan="5"
                        className="px-6 py-12 text-center"
                      >

                        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-accent-light text-primary">
                          <Building2 size={22} />
                        </div>

                        <p className="mt-4 text-sm font-semibold text-text">
                          {search
                            ? "No departments found"
                            : "No departments yet"}
                        </p>

                        <p className="mt-1 text-sm text-text-muted">
                          {search
                            ? "Try a different search term."
                            : "Create your first department to get started."}
                        </p>

                      </td>

                    </tr>

                  ) : (

                    filteredDepartments.map(
                      (department, index) => (

                        <tr
                          key={department.id}
                          className="
                            border-b
                            border-border
                            last:border-b-0
                            transition
                            hover:bg-surface-muted
                          "
                        >

                          <td className="px-6 py-4 text-sm text-text-muted">
                            {index + 1}
                          </td>

                          <td className="px-6 py-4">

                            <span className="rounded-lg bg-accent-light px-3 py-1.5 text-xs font-bold text-primary">
                              {department.department_code}
                            </span>

                          </td>

                          <td className="px-6 py-4">

                            <p className="text-sm font-semibold text-text">
                              {department.department_name}
                            </p>

                          </td>

                          <td className="px-6 py-4">

                            <span
                              className={`
                                rounded-full
                                px-3
                                py-1
                                text-xs
                                font-semibold
                                ${department.is_active
                                  ? "bg-accent-light text-success"
                                  : "bg-danger/10 text-danger"
                                }
                              `}
                            >
                              {department.is_active
                                ? "Active"
                                : "Inactive"}
                            </span>

                          </td>

                          <td className="px-6 py-4">

                            <div className="flex items-center gap-2">

                              {/* VIEW */}

                              <button
                                type="button"
                                onClick={() =>
                                  handleViewDetails(department)
                                }
                                disabled={detailsLoading}
                                className="
        rounded-lg
        p-2
        text-text-muted
        transition
        hover:bg-accent-light
        hover:text-primary
      "
                                title="View details"
                              >
                                <Eye size={17} />
                              </button>


                              {/* EDIT */}

                              <button
                                type="button"
                                onClick={() =>
                                  handleEdit(department)
                                }
                                className="
        rounded-lg
        p-2
        text-text-muted
        transition
        hover:bg-accent-light
        hover:text-primary
      "
                                title="Edit department"
                              >
                                <Pencil size={17} />
                              </button>


                              {/* ACTIVATE / DEACTIVATE */}

                              <button
                                type="button"
                                onClick={() =>
                                  handleToggleStatus(department)
                                }
                                disabled={
                                  statusLoading === department.id
                                }
                                className={`
        rounded-lg
        p-2
        transition
        ${department.is_active
                                    ? "text-danger hover:bg-danger/10"
                                    : "text-success hover:bg-accent-light"
                                  }
      `}
                                title={
                                  department.is_active
                                    ? "Deactivate department"
                                    : "Activate department"
                                }
                              >

                                {statusLoading === department.id ? (

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

                      )
                    )

                  )}

                </tbody>

              </table>

            </div>

          </div>


          {/* ================================================= */}
          {/* COUNT */}
          {/* ================================================= */}

          {!loading && (

            <p className="mt-4 text-xs text-text-muted">

              Showing{" "}
              <span className="font-semibold text-text">
                {filteredDepartments.length}
              </span>{" "}
              of{" "}
              <span className="font-semibold text-text">
                {departments.length}
              </span>{" "}
              departments

            </p>

          )}

        </div>

      </main>


      {/* ================================================= */}
      {/* FORM MODAL */}
      {/* ================================================= */}
<CsvImport
  entity="departments"
  isOpen={showCsvImport}
  onClose={() => setShowCsvImport(false)}
  onValidate={validateCsv}
  onImport={importCsv}
/>
      {showForm && (

        <DepartmentForm
          department={null}
          onClose={() => setShowForm(false)}
          onSuccess={handleFormSuccess}
        />

      )}


      {editingDepartment && (

        <DepartmentForm
          department={editingDepartment}
          onClose={() =>
            setEditingDepartment(null)
          }
          onSuccess={handleFormSuccess}
        />

      )}

      {viewingDepartment && (

        <div
          className="
      fixed
      inset-0
      z-[60]
      flex
      items-center
      justify-center
      bg-black/40
      p-4
      backdrop-blur-sm
    "
          onMouseDown={(event) => {

            if (
              event.target === event.currentTarget
            ) {
              setViewingDepartment(null);
            }

          }}
        >

          <div
            className="
        w-full
        max-w-2xl
        overflow-hidden
        rounded-2xl
        bg-surface
        shadow-2xl
      "
          >

            {/* HEADER */}

            <div className="
        flex
        items-center
        justify-between
        border-b
        border-border
        px-6
        py-5
      ">

              <div className="flex items-center gap-3">

                <div className="
            flex
            h-11
            w-11
            items-center
            justify-center
            rounded-xl
            bg-accent-light
            text-primary
          ">
                  <Building2 size={21} />
                </div>

                <div>

                  <h2 className="
              text-lg
              font-bold
              text-text
            ">
                    Department Details
                  </h2>

                  <p className="
              text-sm
              text-text-muted
            ">
                    Department information and courses.
                  </p>

                </div>

              </div>


              <button
                type="button"
                onClick={() =>
                  setViewingDepartment(null)
                }
                className="
            rounded-lg
            p-2
            text-text-muted
            transition
            hover:bg-surface-muted
            hover:text-text
          "
              >
                <X size={20} />
              </button>

            </div>


            {/* DETAILS */}

            <div className="p-6">

              <div className="
          grid
          gap-4
          sm:grid-cols-2
        ">

                <div className="
            rounded-xl
            border
            border-border
            bg-surface-muted
            p-4
          ">

                  <p className="
              text-xs
              font-semibold
              uppercase
              tracking-wider
              text-text-muted
            ">
                    Department Code
                  </p>

                  <p className="
              mt-2
              text-lg
              font-bold
              text-primary
            ">
                    {viewingDepartment.department_code}
                  </p>

                </div>


                <div className="
            rounded-xl
            border
            border-border
            bg-surface-muted
            p-4
          ">

                  <p className="
              text-xs
              font-semibold
              uppercase
              tracking-wider
              text-text-muted
            ">
                    Status
                  </p>

                  <p className="
              mt-2
              text-lg
              font-bold
              text-text
            ">
                    {viewingDepartment.is_active
                      ? "Active"
                      : "Inactive"}
                  </p>

                </div>

              </div>


              <div className="
          mt-4
          rounded-xl
          border
          border-border
          bg-surface-muted
          p-4
        ">

                <p className="
            text-xs
            font-semibold
            uppercase
            tracking-wider
            text-text-muted
          ">
                  Department Name
                </p>

                <p className="
            mt-2
            text-lg
            font-bold
            text-text
          ">
                  {viewingDepartment.department_name}
                </p>

              </div>


              {/* COURSES */}

              <div className="mt-6">

                <div className="
            flex
            items-center
            justify-between
            mb-3
          ">

                  <h3 className="
              text-base
              font-bold
              text-text
            ">
                    Courses
                  </h3>

                  <span className="
              rounded-full
              bg-accent-light
              px-3
              py-1
              text-xs
              font-semibold
              text-primary
            ">
                    {viewingDepartment.course_count || 0}
                  </span>

                </div>


                {viewingDepartment.courses?.length ? (

                  <div className="
              overflow-hidden
              rounded-xl
              border
              border-border
            ">

                    {viewingDepartment.courses.map(
                      (course) => (

                        <div
                          key={course.id}
                          className="
                      flex
                      items-center
                      justify-between
                      gap-4
                      border-b
                      border-border
                      p-4
                      last:border-b-0
                    "
                        >

                          <div>

                            <p className="
                        text-sm
                        font-semibold
                        text-text
                      ">
                              {course.course_name}
                            </p>

                            <p className="
                        mt-1
                        text-xs
                        text-text-muted
                      ">
                              {course.course_code}
                              {" • "}
                              {course.course_abbreviation}
                            </p>

                          </div>


                          <span className={`
                      rounded-full
                      px-3
                      py-1
                      text-xs
                      font-semibold
                      ${course.is_active
                              ? "bg-accent-light text-success"
                              : "bg-danger/10 text-danger"
                            }
                    `}>
                            {course.is_active
                              ? "Active"
                              : "Inactive"}
                          </span>

                        </div>

                      )
                    )}

                  </div>

                ) : (

                  <div className="
              rounded-xl
              border
              border-dashed
              border-border
              p-6
              text-center
            ">

                    <p className="
                text-sm
                font-semibold
                text-text
              ">
                      No courses assigned
                    </p>

                    <p className="
                mt-1
                text-xs
                text-text-muted
              ">
                      Courses belonging to this department
                      will appear here.
                    </p>

                  </div>

                )}

              </div>

            </div>

          </div>

        </div>

      )}

    </div>
  );
}


export default Departments;
