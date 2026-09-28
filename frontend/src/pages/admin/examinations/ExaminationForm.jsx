import { useEffect, useState } from "react";
import { Save, X } from "lucide-react";
import {
  get,
  post,
  put,
} from "../../../services/api";
function ExaminationForm({
  examination,
  onSuccess,
  onCancel,
}) {
 const [formData, setFormData] = useState({
  name: "",
  exam_type: "REGULAR",
  course_selections: [],
  start_date: "",
  end_date: "",
  duration_minutes: "",
  session_config: [
    {
      session: "FN",
      start_time: "10:00",
      end_time: "13:00",
    },
    {
      session: "AN",
      start_time: "14:00",
      end_time: "17:00",
    },
  ],
  excluded_dates: [],
});

  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
const [courses, setCourses] = useState([]);
const [coursesLoading, setCoursesLoading] = useState(true);
  const isEditing = Boolean(examination);
  useEffect(() => {
  async function loadCourses() {
    try {
      setCoursesLoading(true);

      const data = await get("/courses/");

      setCourses(data);
    } catch (err) {
      console.error("Course loading error:", err);

      setError(
        "Unable to load courses."
      );
    } finally {
      setCoursesLoading(false);
    }
  }

  loadCourses();
}, []);
useEffect(() => {
  if (examination) {
    setFormData({
      name: examination.name || "",
      exam_type: examination.exam_type || "REGULAR",
      course_selections: [
  {
    course_id: examination.course_id,
    semesters: [examination.semester],
  },
],
      start_date: examination.start_date || "",
      end_date: examination.end_date || "",
      duration_minutes:
        examination.duration_minutes || "",
      session_config:
        examination.session_config || [
          {
            session: "FN",
            start_time: "10:00",
            end_time: "13:00",
          },
          {
            session: "AN",
            start_time: "14:00",
            end_time: "17:00",
          },
        ],
      excluded_dates:
        examination.excluded_dates || [],
    });
  } else {
  setFormData({
    name: "",
    exam_type: "REGULAR",
    course_selections: [],
    start_date: "",
    end_date: "",
    duration_minutes: "",
    session_config: [
      {
        session: "FN",
        start_time: "10:00",
        end_time: "13:00",
      },
      {
        session: "AN",
        start_time: "14:00",
        end_time: "17:00",
      },
    ],
    excluded_dates: [],
  });
}

  setError("");
}, [examination]);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const addCourseSelection = (courseId) => {
  const id = Number(courseId);

  if (!id) {
    return;
  }

  const course = courses.find(
    (item) => item.id === id
  );

  if (!course) {
    return;
  }

  const alreadySelected =
    formData.course_selections.some(
      (item) => item.course_id === id
    );

  if (alreadySelected) {
    return;
  }

  setFormData((previous) => ({
    ...previous,
    course_selections: [
      ...previous.course_selections,
      {
        course_id: id,
        semesters: [],
      },
    ],
  }));
};

const removeCourseSelection = (courseId) => {
  setFormData((previous) => ({
    ...previous,
    course_selections:
      previous.course_selections.filter(
        (item) => item.course_id !== courseId
      ),
  }));
};

const toggleSemester = (
  courseId,
  semester
) => {
  setFormData((previous) => ({
    ...previous,
    course_selections:
      previous.course_selections.map(
        (item) => {
          if (item.course_id !== courseId) {
            return item;
          }

          const exists =
            item.semesters.includes(semester);

          return {
            ...item,
            semesters: exists
              ? item.semesters.filter(
                  (value) => value !== semester
                )
              : [
                  ...item.semesters,
                  semester,
                ],
          };
        }
      ),
  }));
};

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    if (!formData.name.trim()) {
  setError("Examination name is required.");
  return;
}

if (formData.course_selections.length === 0) {
  setError("At least one course is required.");
  return;
}

const invalidSelection =
  formData.course_selections.find(
    (item) => item.semesters.length === 0
  );

if (invalidSelection) {
  setError(
    "Select at least one semester for every course."
  );
  return;
}

if (!formData.start_date) {
  setError("Start date is required.");
  return;
}

if (!formData.end_date) {
  setError("End date is required.");
  return;
}

if (
  formData.start_date >
  formData.end_date
) {
  setError(
    "Start date cannot be after end date."
  );
  return;
}

if (!formData.duration_minutes) {
  setError("Exam duration is required.");
  return;
}

    if (
      !formData.duration_minutes ||
      Number(formData.duration_minutes) <= 0
    ) {
      setError("Please enter a valid duration.");
      return;
    }

    if (!formData.exam_type.trim()) {
      setError("Please enter the examination type.");
      return;
    }

    try {
      setSaving(true);

      /*
 * Create mode uses the bulk examination endpoint.
 * Edit mode updates one existing examination.
 */

      const payload = {
  name: formData.name.trim(),
  exam_type: formData.exam_type,
  start_date: formData.start_date,
  end_date: formData.end_date,
  duration_minutes: Number(
    formData.duration_minutes
  ),
  session_config: formData.session_config,
  excluded_dates: formData.excluded_dates,
  selections:
    formData.course_selections.map(
      (selection) => ({
        course_id: Number(
          selection.course_id
        ),
        semesters:
          selection.semesters.map(Number),
      })
    ),
};

if (isEditing) {
  const editPayload = {
    name: payload.name,
    exam_type: payload.exam_type,
    course_id: Number(
      formData.course_selections[0].course_id
    ),
    semester: Number(
      formData.course_selections[0].semesters[0]
    ),
    start_date: payload.start_date,
    end_date: payload.end_date,
    duration_minutes: payload.duration_minutes,
    session_config: payload.session_config,
    excluded_dates: payload.excluded_dates,
  };

  await put(
    `/examinations/${examination.id}`,
    editPayload
  );
} else {
  await post(
    "/examinations/bulk",
    payload
  );
}

onSuccess();
    } catch (err) {
      console.error("Examination save error:", err);

      setError(
        err.message ||
          "Unable to create examination."
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-5"
    >

      {/* ================================================= */}
      {/* ERROR */}
      {/* ================================================= */}

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

{/* ================================================= */}
{/* EXAMINATION NAME */}
{/* ================================================= */}

<div>
  <label className="mb-2 block text-sm font-semibold text-sidebar">
    Examination Name
  </label>

  <input
    type="text"
    name="name"
    value={formData.name}
    onChange={handleChange}
    placeholder="e.g. End Semester Examination 2026"
    className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
  />
</div>


{/* ================================================= */}
{/* TYPE + COURSE */}
{/* ================================================= */}

<div className="grid gap-5 md:grid-cols-2">

  <div>
    <label className="mb-2 block text-sm font-semibold text-sidebar">
      Examination Type
    </label>

    <select
      name="exam_type"
      value={formData.exam_type}
      onChange={handleChange}
      className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
    >
      <option value="REGULAR">
        Regular
      </option>

      <option value="INTERNAL">
        Internal
      </option>

      <option value="MODEL">
        Model Examination
      </option>

      <option value="SUPPLEMENTARY">
        Supplementary
      </option>

      <option value="PRACTICAL">
        Practical
      </option>
    </select>
  </div>

<div>
  <label className="mb-2 block text-sm font-semibold text-sidebar">
    Courses
  </label>

  <p className="mb-3 text-xs text-text-muted">
    Select the courses that will be included in this examination.
    You can choose semesters separately for each course.
  </p>

  <select
    value=""
    onChange={(event) =>
      addCourseSelection(event.target.value)
    }
    disabled={coursesLoading || isEditing}
    className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
  >
    <option value="">
      {coursesLoading
        ? "Loading courses..."
        : "Add Course"}
    </option>

    {courses
      .filter(
        (course) =>
          !formData.course_selections.some(
            (item) =>
              item.course_id === course.id
          )
      )
      .map((course) => (
        <option
          key={course.id}
          value={course.id}
        >
          {course.course_code} — {course.course_name}
        </option>
      ))}
  </select>

  <div className="mt-4 space-y-4">
    {formData.course_selections.map(
      (selection) => {
        const course = courses.find(
          (item) =>
            item.id === selection.course_id
        );

        if (!course) {
          return null;
        }

        return (
          <div
            key={course.id}
            className="rounded-xl border border-border bg-background p-4"
          >
            <div className="mb-3 flex items-center justify-between">
              <div>
                <p className="font-semibold text-text">
                  {course.course_code}
                </p>

                <p className="text-sm text-text-muted">
                  {course.course_name}
                </p>

                <p className="mt-1 text-xs text-text-muted">
                  {course.program_level} ·{" "}
                  {course.total_semesters} semesters
                </p>
              </div>

              {!isEditing && (
                <button
                  type="button"
                  onClick={() =>
                    removeCourseSelection(
                      course.id
                    )
                  }
                  className="rounded-lg p-2 text-danger hover:bg-red-50"
                >
                  <X size={16} />
                </button>
              )}
            </div>

            <p className="mb-2 text-xs font-medium text-text-muted">
              Select semesters
            </p>

            <div className="flex flex-wrap gap-2">
              {Array.from(
                {
                  length: course.total_semesters,
                },
                (_, index) => index + 1
              ).map((semester) => {
                const selected =
                  selection.semesters.includes(
                    semester
                  );

                return (
                  <button
                    key={semester}
                    type="button"
                    onClick={() =>
                      toggleSemester(
                        course.id,
                        semester
                      )
                    }
                    className={`rounded-lg border px-3 py-2 text-sm font-medium transition ${
                      selected
                        ? "border-primary bg-primary text-white"
                        : "border-border bg-surface text-text hover:bg-surface-muted"
                    }`}
                  >
                    Sem {semester}
                  </button>
                );
              })}
            </div>
          </div>
        );
      }
    )}
  </div>
</div>
</div>

{/* ================================================= */}
{/* DATE RANGE */}
{/* ================================================= */}

<div className="grid gap-5 md:grid-cols-2">

  <div>
    <label className="mb-2 block text-sm font-semibold text-sidebar">
      Examination Start Date
    </label>

    <input
      type="date"
      name="start_date"
      value={formData.start_date}
      onChange={handleChange}
      className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
    />
  </div>


  <div>
    <label className="mb-2 block text-sm font-semibold text-sidebar">
      Examination End Date
    </label>

    <input
      type="date"
      name="end_date"
      value={formData.end_date}
      onChange={handleChange}
      className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
    />
  </div>

</div>

{/* ================================================= */}
{/* EXAM DURATION */}
{/* ================================================= */}

<div>
  <label className="mb-2 block text-sm font-semibold text-sidebar">
    Examination Duration
  </label>

  <p className="mb-3 text-xs text-text-muted">
    Enter the duration of each examination in minutes.
  </p>

  <input
    type="number"
    name="duration_minutes"
    value={formData.duration_minutes}
    onChange={handleChange}
    min="1"
    placeholder="e.g. 180"
    className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
  />
</div>


{/* ================================================= */}
{/* SESSION CONFIGURATION */}
{/* ================================================= */}

<div>

  <div className="mb-3">
    <label className="block text-sm font-semibold text-sidebar">
      Session Configuration
    </label>

    <p className="mt-1 text-xs text-text-muted">
      Configure the available examination sessions.
    </p>
  </div>


  <div className="space-y-3">

    {formData.session_config.map(
      (sessionConfig, index) => (
        <div
          key={index}
          className="grid gap-3 rounded-xl border border-border bg-background p-4 md:grid-cols-3"
        >

          <div>
            <label className="mb-1 block text-xs font-medium text-text-muted">
              Session
            </label>

            <select
              value={sessionConfig.session}
              onChange={(event) => {
                const updated =
                  [...formData.session_config];

                updated[index] = {
                  ...updated[index],
                  session: event.target.value,
                };

                setFormData((previous) => ({
                  ...previous,
                  session_config: updated,
                }));
              }}
              className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text outline-none focus:border-primary"
            >
              <option value="FN">
                FN
              </option>

              <option value="AN">
                AN
              </option>
            </select>
          </div>


          <div>
            <label className="mb-1 block text-xs font-medium text-text-muted">
              Start Time
            </label>

            <input
              type="time"
              value={sessionConfig.start_time}
              onChange={(event) => {
                const updated =
                  [...formData.session_config];

                updated[index] = {
                  ...updated[index],
                  start_time: event.target.value,
                };

                setFormData((previous) => ({
                  ...previous,
                  session_config: updated,
                }));
              }}
              className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text outline-none focus:border-primary"
            />
          </div>


          <div>
            <label className="mb-1 block text-xs font-medium text-text-muted">
              End Time
            </label>

            <input
              type="time"
              value={sessionConfig.end_time}
              onChange={(event) => {
                const updated =
                  [...formData.session_config];

                updated[index] = {
                  ...updated[index],
                  end_time: event.target.value,
                };

                setFormData((previous) => ({
                  ...previous,
                  session_config: updated,
                }));
              }}
              className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text outline-none focus:border-primary"
            />
          </div>

        </div>
      )
    )}

  </div>

</div>


{/* ================================================= */}
{/* EXCLUDED DATES */}
{/* ================================================= */}

<div>

  <label className="mb-2 block text-sm font-semibold text-sidebar">
    Excluded Dates
  </label>

  <p className="mb-3 text-xs text-text-muted">
    Select dates within the examination range on which no examination should be scheduled.
  </p>

  <input
    type="date"
    onChange={(event) => {
      const value = event.target.value;

      if (
        value &&
        !formData.excluded_dates.includes(value)
      ) {
        setFormData((previous) => ({
          ...previous,
          excluded_dates: [
            ...previous.excluded_dates,
            value,
          ],
        }));
      }
    }}
    className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
  />

  {formData.excluded_dates.length > 0 && (
    <div className="mt-3 flex flex-wrap gap-2">

      {formData.excluded_dates.map(
        (date) => (
          <div
            key={date}
            className="flex items-center gap-2 rounded-lg bg-surface-muted px-3 py-2 text-sm"
          >
            <span>
              {date}
            </span>

            <button
              type="button"
              onClick={() => {
                setFormData((previous) => ({
                  ...previous,
                  excluded_dates:
                    previous.excluded_dates.filter(
                      (item) => item !== date
                    ),
                }));
              }}
              className="text-text-muted hover:text-danger"
            >
              <X size={14} />
            </button>
          </div>
        )
      )}

    </div>
  )}

</div>

      {/* ================================================= */}
      {/* ACTIONS */}
      {/* ================================================= */}

      <div className="flex flex-col-reverse gap-3 border-t border-border pt-5 sm:flex-row sm:justify-end">

        <button
          type="button"
          onClick={onCancel}
          disabled={saving}
          className="flex items-center justify-center gap-2 rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold text-sidebar transition hover:bg-surface-muted disabled:opacity-50"
        >
          <X size={17} />

          Cancel
        </button>

        <button
          type="submit"
          disabled={saving}
          className="flex items-center justify-center gap-2 rounded-xl bg-sidebar px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-sidebar/10 transition hover:bg-primary disabled:cursor-not-allowed disabled:opacity-60"
        >
          <Save size={17} />

          {saving
  ? "Saving..."
  : isEditing
    ? "Update Examination"
    : "Create Examination Plan"}
        </button>

      </div>

    </form>
  );
}

export default ExaminationForm;
