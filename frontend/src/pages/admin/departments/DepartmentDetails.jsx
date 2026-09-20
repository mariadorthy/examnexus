import { useEffect, useState } from "react";

import {
  X,
  Building2,
  BookOpen,
  Loader2,
} from "lucide-react";


const API_URL =
  "http://127.0.0.1:5000/api/departments";


function DepartmentDetails({
  departmentId,
  onClose,
}) {

  const [department, setDepartment] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  // =====================================================
  // LOAD DETAILS
  // =====================================================

  useEffect(() => {

    loadDepartment();

  }, [departmentId]);


  const loadDepartment = async () => {

    try {

      setLoading(true);
      setError("");


      const response = await fetch(
        `${API_URL}/${departmentId}`
      );


      const data = await response.json();


      if (!response.ok) {

        throw new Error(
          data.message ||
          "Failed to load department."
        );

      }


      setDepartment(data);

    } catch (err) {

      console.error(
        "Department details error:",
        err
      );

      setError(
        err.message ||
        "Unable to load department."
      );

    } finally {

      setLoading(false);

    }

  };


  return (
    <div
      className="
        fixed inset-0 z-[60]
        flex items-center justify-center
        bg-black/40 p-4
        backdrop-blur-sm
      "
      onMouseDown={(event) => {

        if (
          event.target === event.currentTarget
        ) {
          onClose();
        }

      }}
    >

      <div
        className="
          flex max-h-[90vh]
          w-full max-w-2xl
          flex-col overflow-hidden
          rounded-2xl bg-surface
          shadow-2xl
        "
      >

        {/* HEADER */}

        <div className="flex shrink-0 items-center justify-between border-b border-border px-6 py-5">

          <div className="flex items-center gap-3">

            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-light text-primary">
              <Building2 size={21} />
            </div>

            <div>

              <h2 className="text-lg font-bold text-text">
                Department Details
              </h2>

              <p className="text-sm text-text-muted">
                Department information and courses.
              </p>

            </div>

          </div>


          <button
            type="button"
            onClick={onClose}
            className="
              rounded-lg p-2
              text-text-muted
              transition
              hover:bg-surface-muted
              hover:text-text
            "
          >
            <X size={20} />
          </button>

        </div>


        {/* CONTENT */}

        <div className="overflow-y-auto p-6">

          {loading && (

            <div className="flex items-center justify-center py-12">

              <Loader2
                size={24}
                className="animate-spin text-primary"
              />

              <span className="ml-3 text-sm text-text-muted">
                Loading department...
              </span>

            </div>

          )}


          {error && !loading && (

            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>

          )}


          {department && !loading && !error && (

            <>

              {/* DEPARTMENT INFO */}

              <div className="rounded-2xl border border-border bg-surface-muted p-5">

                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">

                  <div>

                    <span className="inline-flex rounded-lg bg-accent-light px-3 py-1.5 text-xs font-bold text-primary">
                      {department.department_code}
                    </span>

                    <h3 className="mt-3 text-xl font-bold text-text">
                      {department.department_name}
                    </h3>

                  </div>


                  <span
                    className={`
                      w-fit rounded-full
                      px-3 py-1 text-xs
                      font-semibold
                      ${
                        department.is_active
                          ? "bg-accent-light text-success"
                          : "bg-danger/10 text-danger"
                      }
                    `}
                  >
                    {department.is_active
                      ? "Active"
                      : "Inactive"}
                  </span>

                </div>

              </div>


              {/* COURSES */}

              <div className="mt-6">

                <div className="mb-4 flex items-center justify-between">

                  <div className="flex items-center gap-3">

                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-light text-primary">
                      <BookOpen size={19} />
                    </div>

                    <div>

                      <h3 className="font-bold text-text">
                        Courses
                      </h3>

                      <p className="text-xs text-text-muted">
                        Courses belonging to this department
                      </p>

                    </div>

                  </div>


                  <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
                    {department.courses?.length || 0}
                  </span>

                </div>


                {!department.courses ||
                department.courses.length === 0 ? (

                  <div className="rounded-xl border border-border bg-surface-muted p-6 text-center">

                    <BookOpen
                      size={24}
                      className="mx-auto text-text-light"
                    />

                    <p className="mt-3 text-sm font-semibold text-text">
                      No courses assigned
                    </p>

                    <p className="mt-1 text-xs text-text-muted">
                      This department does not have any courses yet.
                    </p>

                  </div>

                ) : (

                  <div className="overflow-hidden rounded-xl border border-border">

                    <div className="overflow-x-auto">

                      <table className="w-full">

                        <thead>

                          <tr className="border-b border-border bg-surface-muted">

                            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                              Code
                            </th>

                            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                              Course
                            </th>

                            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                              Status
                            </th>

                          </tr>

                        </thead>


                        <tbody>

                          {department.courses.map(
                            (course) => (

                              <tr
                                key={course.id}
                                className="border-b border-border last:border-b-0"
                              >

                                <td className="px-4 py-3">

                                  <span className="rounded-lg bg-accent-light px-2.5 py-1 text-xs font-bold text-primary">
                                    {course.course_code}
                                  </span>

                                </td>


                                <td className="px-4 py-3 text-sm font-medium text-text">
                                  {course.course_name}
                                </td>


                                <td className="px-4 py-3">

                                  <span
                                    className={
                                      course.is_active
                                        ? "text-xs font-semibold text-success"
                                        : "text-xs font-semibold text-danger"
                                    }
                                  >
                                    {course.is_active
                                      ? "Active"
                                      : "Inactive"}
                                  </span>

                                </td>

                              </tr>

                            )
                          )}

                        </tbody>

                      </table>

                    </div>

                  </div>

                )}

              </div>

            </>

          )}

        </div>


        {/* FOOTER */}

        <div className="flex shrink-0 justify-end border-t border-border px-6 py-4">

          <button
            type="button"
            onClick={onClose}
            className="
              rounded-xl bg-sidebar
              px-5 py-2.5
              text-sm font-semibold
              text-white
              transition hover:bg-primary
            "
          >
            Close
          </button>

        </div>

      </div>

    </div>
  );
}


export default DepartmentDetails;
