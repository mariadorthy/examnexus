import { useState } from "react";
import {
  X,
  BookOpen,
  Loader2,
} from "lucide-react";
import {
  post,
  put,
} from "../../../services/api";

function CourseForm({
  course,  
  departments,
  onClose,
  onSuccess,
}) {

  const [formData, setFormData] = useState({
  course_code: course?.course_code || "",
  course_name: course?.course_name || "",
  course_abbreviation: course?.course_abbreviation || "",
  program_level: course?.program_level || "",
  department_id: course?.department_id || "",
  study_shift: course?.study_shift || "",
  session: course?.session || "",
  total_semesters: course?.total_semesters || "",
});


  const [error, setError] = useState("");

  const [loading, setLoading] = useState(false);


  // =====================================================
  // INPUT CHANGE
  // =====================================================

  const handleChange = (event) => {

    const {
      name,
      value,
    } = event.target;


    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));

  };


  // =====================================================
  // SUBMIT
  // =====================================================

  const handleSubmit = async (event) => {

    event.preventDefault();

    setError("");


    // -----------------------------------------------------
    // VALIDATION
    // -----------------------------------------------------

    if (!formData.course_code.trim()) {

      setError(
        "Please enter the course code."
      );

      return;
    }


    if (!formData.course_name.trim()) {

      setError(
        "Please enter the course name."
      );

      return;
    }


    if (!formData.course_abbreviation.trim()) {

      setError(
        "Please enter the course abbreviation."
      );

      return;
    }


    if (!formData.program_level.trim()) {

      setError(
        "Please select the program level."
      );

      return;
    }


    if (!formData.department_id) {

      setError(
        "Please select a department."
      );

      return;
    }


    if (!formData.study_shift) {

      setError(
        "Please select a study shift."
      );

      return;
    }


    if (!formData.session.trim()) {

      setError(
        "Please enter the session."
      );

      return;
    }


    if (!formData.total_semesters) {

      setError(
        "Please enter the total number of semesters."
      );

      return;
    }


    const totalSemesters =
      Number(formData.total_semesters);


    if (
      !Number.isInteger(totalSemesters) ||
      totalSemesters <= 0
    ) {

      setError(
        "Total semesters must be a positive whole number."
      );

      return;
    }


    // -----------------------------------------------------
    // API
    // -----------------------------------------------------

    try {

      setLoading(true);

const payload = {
  course_code: formData.course_code.trim().toUpperCase(),
  course_name: formData.course_name.trim(),
  course_abbreviation:
    formData.course_abbreviation.trim().toUpperCase(),
  program_level: formData.program_level.trim(),
  department_id: Number(formData.department_id),
  study_shift: formData.study_shift,
  session: formData.session.trim(),
  total_semesters: totalSemesters,
};

if (course) {
  await put(`/courses/${course.id}`, payload);
} else {
  await post("/courses/", payload);
}

onSuccess();

    } catch (err) {

      console.error(
        "Create course error:",
        err
      );

      setError(
        err.message ||
        "Unable to create course."
      );

    } finally {

      setLoading(false);

    }
  };


  return (
    <div
      className="
        fixed
        inset-0
        z-[60]
        flex
        items-center
        justify-center
        overflow-y-auto
        bg-black/40
        p-4
        backdrop-blur-sm
      "
      onMouseDown={(event) => {

        if (event.target === event.currentTarget) {
          onClose();
        }

      }}
    >

      <div
        className="
          my-8
          w-full
          max-w-2xl
          overflow-hidden
          rounded-2xl
          bg-surface
          shadow-2xl
        "
      >

        {/* ================================================= */}
        {/* HEADER */}
        {/* ================================================= */}

        <div className="flex items-center justify-between border-b border-border px-6 py-5">

          <div className="flex items-center gap-3">

            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-light text-primary">
              <BookOpen size={21} />
            </div>

            <div>

              <h2 className="text-lg font-bold text-text">
  {course ? "Edit Course" : "Add Course"}
</h2>

<p className="text-sm text-text-muted">
  {course
    ? "Update course details."
    : "Create a new academic course."}
</p>
            </div>

          </div>


          <button
            type="button"
            onClick={onClose}
            className="
              rounded-lg
              p-2
              text-text-muted
              transition
              hover:bg-surface-muted
              hover:text-text
            "
            aria-label="Close"
          >
            <X size={20} />
          </button>

        </div>


        {/* ================================================= */}
        {/* FORM */}
        {/* ================================================= */}

        <form
          onSubmit={handleSubmit}
          className="p-6"
        >

          {/* ERROR */}

          {error && (

            <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>

          )}


          {/* ================================================= */}
          {/* COURSE CODE + ABBREVIATION */}
          {/* ================================================= */}

          <div className="grid gap-5 sm:grid-cols-2">

            <div>

              <label className="mb-2 block text-sm font-semibold text-sidebar">
                Course Code
              </label>

              <input
                type="text"
                name="course_code"
                value={formData.course_code}
                onChange={handleChange}
                placeholder="e.g. BTECH-CSE"
                maxLength={30}
                autoFocus
                className="
                  w-full
                  rounded-xl
                  border
                  border-border
                  bg-surface
                  px-4
                  py-3
                  text-text
                  outline-none
                  transition
                  placeholder:text-text-light
                  focus:border-primary
                  focus:ring-4
                  focus:ring-primary/10
                "
              />

            </div>


            <div>

              <label className="mb-2 block text-sm font-semibold text-sidebar">
                Abbreviation
              </label>

              <input
                type="text"
                name="course_abbreviation"
                value={
                  formData.course_abbreviation
                }
                onChange={handleChange}
                placeholder="e.g. CSE"
                maxLength={20}
                className="
                  w-full
                  rounded-xl
                  border
                  border-border
                  bg-surface
                  px-4
                  py-3
                  text-text
                  outline-none
                  transition
                  placeholder:text-text-light
                  focus:border-primary
                  focus:ring-4
                  focus:ring-primary/10
                "
              />

            </div>

          </div>


          {/* ================================================= */}
          {/* COURSE NAME */}
          {/* ================================================= */}

          <div className="mt-5">

            <label className="mb-2 block text-sm font-semibold text-sidebar">
              Course Name
            </label>

            <input
              type="text"
              name="course_name"
              value={formData.course_name}
              onChange={handleChange}
              placeholder="e.g. Bachelor of Technology in Computer Science"
              maxLength={150}
              className="
                w-full
                rounded-xl
                border
                border-border
                bg-surface
                px-4
                py-3
                text-text
                outline-none
                transition
                placeholder:text-text-light
                focus:border-primary
                focus:ring-4
                focus:ring-primary/10
              "
            />

          </div>


          {/* ================================================= */}
          {/* DEPARTMENT + PROGRAM LEVEL */}
          {/* ================================================= */}

          <div className="mt-5 grid gap-5 sm:grid-cols-2">

            {/* Department */}

            <div>

              <label className="mb-2 block text-sm font-semibold text-sidebar">
                Department
              </label>

              <select
                name="department_id"
                value={formData.department_id}
                onChange={handleChange}
                className="
                  w-full
                  rounded-xl
                  border
                  border-border
                  bg-surface
                  px-4
                  py-3
                  text-text
                  outline-none
                  transition
                  focus:border-primary
                  focus:ring-4
                  focus:ring-primary/10
                "
              >

                <option value="">
                  Select department
                </option>

                {departments.map(
                  (department) => (

                    <option
                      key={department.id}
                      value={department.id}
                    >
                      {department.department_code} —{" "}
                      {department.department_name}
                    </option>

                  )
                )}

              </select>

            </div>


            {/* Program Level */}

            <div>

              <label className="mb-2 block text-sm font-semibold text-sidebar">
                Program Level
              </label>

              <select
                name="program_level"
                value={formData.program_level}
                onChange={handleChange}
                className="
                  w-full
                  rounded-xl
                  border
                  border-border
                  bg-surface
                  px-4
                  py-3
                  text-text
                  outline-none
                  transition
                  focus:border-primary
                  focus:ring-4
                  focus:ring-primary/10
                "
              >

                <option value="">
                  Select level
                </option>

              <option value="UG">
  UG
</option>

<option value="PG">
  PG
</option>
              </select>

            </div>

          </div>


          {/* ================================================= */}
          {/* STUDY SHIFT + SESSION */}
          {/* ================================================= */}

          <div className="mt-5 grid gap-5 sm:grid-cols-2">

            {/* Study Shift */}

            <div>

              <label className="mb-2 block text-sm font-semibold text-sidebar">
                Study Shift
              </label>

              <select
                name="study_shift"
                value={formData.study_shift}
                onChange={handleChange}
                className="
                  w-full
                  rounded-xl
                  border
                  border-border
                  bg-surface
                  px-4
                  py-3
                  text-text
                  outline-none
                  transition
                  focus:border-primary
                  focus:ring-4
                  focus:ring-primary/10
                "
              >

                <option value="">
                  Select shift
                </option>
<option value="Morning">
  Morning
</option>

<option value="Afternoon">
  Afternoon
</option>
              </select>

            </div>


            {/* Session */}

            <div>

              <label className="mb-2 block text-sm font-semibold text-sidebar">
                Session
              </label>

             <select
                
                name="session"
                value={formData.session}
                onChange={handleChange}
                placeholder="e.g. 24"
                maxLength={2}
                className="
                  w-full
                  rounded-xl
                  border
                  border-border
                  bg-surface
                  px-4
                  py-3
                  text-text
                  outline-none
                  transition
                  placeholder:text-text-light
                  focus:border-primary
                  focus:ring-4
                  focus:ring-primary/10
           "
>
  <option value="">
    Select session
  </option>

  <option value="FN">
    FN
  </option>

  <option value="AN">
    AN
  </option>
</select>
            </div>

          </div>


          {/* ================================================= */}
          {/* TOTAL SEMESTERS */}
          {/* ================================================= */}

          <div className="mt-5">

            <label className="mb-2 block text-sm font-semibold text-sidebar">
              Total Semesters
            </label>

            <input
              type="number"
              name="total_semesters"
              value={formData.total_semesters}
              onChange={handleChange}
              placeholder="e.g. 8"
              min="1"
              max="20"
              className="
                w-full
                rounded-xl
                border
                border-border
                bg-surface
                px-4
                py-3
                text-text
                outline-none
                transition
                placeholder:text-text-light
                focus:border-primary
                focus:ring-4
                focus:ring-primary/10
              "
            />

          </div>


          {/* ================================================= */}
          {/* BUTTONS */}
          {/* ================================================= */}

          <div className="mt-7 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">

            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="
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
                disabled:opacity-50
              "
            >
              Cancel
            </button>


            <button
              type="submit"
              disabled={loading}
              className="
                flex
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
                disabled:cursor-not-allowed
                disabled:opacity-60
              "
            >

              {loading && (
                <Loader2
                  size={17}
                  className="animate-spin"
                />
              )}

             {loading
  ? course
    ? "Updating..."
    : "Creating..."
  : course
    ? "Update Course"
    : "Create Course"}

            </button>

          </div>

        </form>

      </div>

    </div>
  );
}


export default CourseForm;
