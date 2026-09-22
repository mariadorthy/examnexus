import { useEffect, useState } from "react";
import {
  BookOpen,
  Plus,
  Search,
  RefreshCw,
  X,
} from "lucide-react";
import { get } from "../../../services/api";
import AdminSidebar from "../../../components/AdminSidebar";
import AdminTopbar from "../../../components/AdminTopbar";
import CourseForm from "./CourseForm";


const API_URL = "http://127.0.0.1:5000/api/courses";


function Courses({ user, onLogout }) {

  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [courses, setCourses] = useState([]);

  const [departments, setDepartments] =
    useState([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  const [search, setSearch] = useState("");

  const [showForm, setShowForm] = useState(false);


  // =====================================================
  // LOAD COURSES + DEPARTMENTS
  // =====================================================

  const loadCourses = async () => {

    try {

      setLoading(true);
      setError("");


      const [
        coursesResponse,
        departmentsResponse,
      ] = await Promise.all([

        fetch(
          "http://127.0.0.1:5000/api/courses/"
        ),

        fetch(
          "http://127.0.0.1:5000/api/departments/"
        ),

      ]);


      if (
        !coursesResponse.ok ||
        !departmentsResponse.ok
      ) {
        throw new Error(
          "Failed to load course data."
        );
      }


      const [coursesData, departmentsData] =
  await Promise.all([
    get("/courses/"),
    get("/departments/"),
  ]);

setCourses(coursesData);
setDepartments(departmentsData);

    } catch (err) {

      console.error(
        "Courses error:",
        err
      );

      setError(
        "Unable to load courses. Please make sure the backend is running."
      );

    } finally {

      setLoading(false);

    }
  };


  useEffect(() => {

    loadCourses();

  }, []);


  // =====================================================
  // DEPARTMENT NAME
  // =====================================================

  const getDepartmentName = (
    departmentId
  ) => {

    const department =
      departments.find(
        (item) =>
          item.id === departmentId
      );

    return (
      department?.department_name ||
      "Unknown Department"
    );
  };


  // =====================================================
  // SEARCH
  // =====================================================

  const filteredCourses = courses.filter(
    (course) => {

      const searchText =
        search.trim().toLowerCase();


      if (!searchText) {
        return true;
      }


      return (

        course.course_code
          ?.toLowerCase()
          .includes(searchText) ||

        course.course_name
          ?.toLowerCase()
          .includes(searchText) ||

        course.course_abbreviation
          ?.toLowerCase()
          .includes(searchText) ||

        course.program_level
          ?.toLowerCase()
          .includes(searchText) ||

        getDepartmentName(
          course.department_id
        )
          .toLowerCase()
          .includes(searchText)

      );

    }
  );


  // =====================================================
  // CREATE SUCCESS
  // =====================================================

  const handleFormSuccess = () => {

    setShowForm(false);

    loadCourses();

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
        activePage="Courses"
      />


      {/* ================================================= */}
      {/* MAIN */}
      {/* ================================================= */}

      <main className="lg:ml-72">

        {/* TOPBAR */}

        <AdminTopbar
          user={user}
          title="Courses"
          section="Administration"
          onOpenSidebar={() =>
            setSidebarOpen(true)
          }
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
                  Courses
                </h2>

                <p className="mt-2 max-w-2xl text-sm leading-6 text-text-muted">
                  Manage programs and courses offered
                  by each academic department.
                </p>

              </div>


              {/* ADD COURSE */}

              <button
                type="button"
                onClick={() => setShowForm(true)}
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

                Add Course

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
                onClick={loadCourses}
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
                placeholder="Search courses..."
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


            <button
              type="button"
              onClick={loadCourses}
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
                className={
                  loading
                    ? "animate-spin"
                    : ""
                }
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

              <table className="w-full min-w-[1000px]">

                <thead>

                  <tr className="border-b border-border bg-surface-muted">

                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                      #
                    </th>

                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                      Course
                    </th>

                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                      Abbreviation
                    </th>

                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                      Program Level
                    </th>

                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                      Department
                    </th>

                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                      Semesters
                    </th>

                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                      Status
                    </th>

                  </tr>

                </thead>


                <tbody>

                  {loading ? (

                    <tr>

                      <td
                        colSpan="7"
                        className="px-6 py-12 text-center text-sm text-text-muted"
                      >
                        Loading courses...
                      </td>

                    </tr>

                  ) : filteredCourses.length === 0 ? (

                    <tr>

                      <td
                        colSpan="7"
                        className="px-6 py-12 text-center"
                      >

                        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-accent-light text-primary">
                          <BookOpen size={22} />
                        </div>

                        <p className="mt-4 text-sm font-semibold text-text">
                          {search
                            ? "No courses found"
                            : "No courses yet"}
                        </p>

                        <p className="mt-1 text-sm text-text-muted">
                          {search
                            ? "Try a different search term."
                            : "Create your first course to get started."}
                        </p>

                      </td>

                    </tr>

                  ) : (

                    filteredCourses.map(
                      (course, index) => (

                        <tr
                          key={course.id}
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

                            <div>

                              <p className="text-sm font-semibold text-text">
                                {course.course_name}
                              </p>

                              <p className="mt-1 text-xs font-medium text-accent">
                                {course.course_code}
                              </p>

                            </div>

                          </td>


                          <td className="px-6 py-4">

                            <span className="rounded-lg bg-accent-light px-3 py-1.5 text-xs font-bold text-primary">
                              {course.course_abbreviation}
                            </span>

                          </td>


                          <td className="px-6 py-4">

                            <span className="text-sm text-text">
                              {course.program_level}
                            </span>

                          </td>


                          <td className="px-6 py-4">

                            <span className="text-sm text-text">
                              {getDepartmentName(
                                course.department_id
                              )}
                            </span>

                          </td>


                          <td className="px-6 py-4">

                            <span className="text-sm font-medium text-text">
                              {course.total_semesters}
                            </span>

                          </td>


                          <td className="px-6 py-4">

                            <span
                              className={`
                                rounded-full
                                px-3
                                py-1
                                text-xs
                                font-semibold
                                ${
                                  course.is_active
                                    ? "bg-accent-light text-success"
                                    : "bg-danger/10 text-danger"
                                }
                              `}
                            >
                              {course.is_active
                                ? "Active"
                                : "Inactive"}
                            </span>

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
                {filteredCourses.length}
              </span>{" "}
              of{" "}
              <span className="font-semibold text-text">
                {courses.length}
              </span>{" "}
              courses

            </p>

          )}

        </div>

      </main>


      {/* ================================================= */}
      {/* COURSE FORM */}
      {/* ================================================= */}

      {showForm && (

        <CourseForm
          departments={departments}
          onClose={() => setShowForm(false)}
          onSuccess={handleFormSuccess}
        />

      )}

    </div>
  );
}


export default Courses;
