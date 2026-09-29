import { useEffect, useState } from "react";
import {
  Plus,
  RefreshCw,
  Eye,
  X,
  CalendarDays,
  Check,
} from "lucide-react";

import AdminSidebar from "../../../components/AdminSidebar";
import TimetableView from "./TimetableView";
import {
  get,
} from "../../../services/api";

import {
  getTimetable,
  generateBulkTimetable,
} from "../../../services/timetableService";

export default function Timetables({
  user,
  onLogout,
  onNavigate,
}) {

  const [sidebarOpen, setSidebarOpen] =
    useState(false);

  const [examinations, setExaminations] =
    useState([]);

  const [subjects, setSubjects] =
    useState([]);

  const [existingTimetables, setExistingTimetables] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [showCreateForm, setShowCreateForm] =
    useState(false);
const [viewingExaminationId, setViewingExaminationId] =
  useState(null);
  const [selectedPlanKey, setSelectedPlanKey] = useState("");
const [selectedSessions, setSelectedSessions] = useState([]);
const [gapDays, setGapDays] = useState(0);
const [excludedDates, setExcludedDates] = useState([]);

  const [newExcludedDate, setNewExcludedDate] =
    useState("");

  const [creating, setCreating] =
    useState(false);


  /* ================================================= */
  /* LOAD DATA */
  /* ================================================= */

  async function loadData() {

    try {

      setLoading(true);
      setError("");

      const [
        examinationData,
        subjectData,
      ] = await Promise.all([
        get("/examinations/"),
        get("/subjects/"),
      ]);

      console.log(
  "EXAMINATION DATA:",
  examinationData
);

setExaminations(
  examinationData || []
);

      setSubjects(
        subjectData || []
      );


      /*
       * An examination is shown in
       * "Existing Timetables" ONLY when
       * it actually has timetable entries.
       */

      const timetableResults = [];

      for (
        const examination
        of examinationData || []
      ) {

        try {

          const entries =
            await getTimetable(
              examination.id
            );

          if (
            Array.isArray(entries) &&
            entries.length > 0
          ) {

            timetableResults.push({
              examination,
              entries,
            });

          }

        } catch (err) {

          console.error(
            `Failed to load timetable for examination ${examination.id}:`,
            err
          );

        }

      }

      setExistingTimetables(
        timetableResults
      );

    } catch (err) {

      console.error(
        "Timetable page error:",
        err
      );

      setError(
        err.message ||
        "Failed to load timetable data."
      );

    } finally {

      setLoading(false);

    }

  }


  useEffect(() => {

    loadData();

  }, []);

  const handleGenerate = async () => {
  if (!selectedPlan) {
    setError("Please select an examination plan.");
    return;
  }

  if (!selectedSessions.length) {
    setError("Please select at least one session.");
    return;
  }

const numericGap = Number(gapDays);

if (
  !Number.isInteger(numericGap) ||
  numericGap < 0
) {
  setError(
    "Gap between exams must be 0 or a positive whole number."
  );
  return;
}
  try {
    setCreating(true);
    setError("");

    const result = await generateBulkTimetable({
      examination_ids: selectedExaminations.map(
        (examination) => examination.id
      ),
      sessions: selectedSessions,
      gap_days: numericGap,
      excluded_dates: excludedDates,
      clear_existing: true,
    });

    const createdCount =
      result?.created_count ?? 0;

    const skippedCount =
      result?.skipped_count ?? 0;

    if (createdCount === 0 && skippedCount > 0) {

  alert(
    `No new timetable entries were created.\n\n` +
    `Skipped: ${skippedCount} existing entries.`
  );

} else {

  setError("");

  alert(
    `Timetable generated successfully.\n\n` +
    `Created: ${createdCount}\n` +
    `Skipped: ${skippedCount}`
  );

}

handleCloseCreateForm();

await loadData();
  } catch (err) {
    setError(
      err?.message ||
      "Failed to generate timetable."
    );
  } finally {
    setCreating(false);
  }
};

  const examinationPlans = Object.values(
  examinations.reduce((plans, examination) => {
    const key = [
      examination.name,
      examination.exam_type,
      examination.start_date,
      examination.end_date,
      examination.duration_minutes,
    ].join("|");

    if (!plans[key]) {
      plans[key] = {
        key,
        name: examination.name,
        exam_type: examination.exam_type,
        start_date: examination.start_date,
        end_date: examination.end_date,
        duration_minutes: examination.duration_minutes,
        examinations: [],
      };
    }

    plans[key].examinations.push(examination);

    return plans;
  }, {})
);

  /* ================================================= */
  /* SELECTED EXAMINATION */
  /* ================================================= */

  const selectedPlan = examinationPlans.find(
  (plan) => plan.key === selectedPlanKey
);

const selectedExaminations =
  selectedPlan?.examinations || [];

const referenceExamination =
  selectedExaminations[0] || null;

  /* ================================================= */
  /* SESSION CONFIG */
  /* ================================================= */

  const availableSessions =
  referenceExamination?.session_config?.length
    ? referenceExamination.session_config
    : [
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
      ];

  /* ================================================= */
  /* OPEN CREATE FORM */
  /* ================================================= */

  function handleCreateTimetable() {

  setError("");

  setSelectedPlanKey("");
  setSelectedSessions([]);
  setGapDays(0);
  setExcludedDates([]);
  setNewExcludedDate("");

  setShowCreateForm(true);

}

  /* ================================================= */
  /* CLOSE CREATE FORM */
  /* ================================================= */

  function handleCloseCreateForm() {

    if (creating) {
      return;
    }

    setShowCreateForm(false);

    setError("");

  }

  /* ================================================= */
  /* SELECT SESSION */
  /* ================================================= */

  function toggleSession(sessionName) {

    setSelectedSessions(
      (current) => {

        if (
          current.includes(sessionName)
        ) {

          return current.filter(
            (session) =>
              session !== sessionName
          );

        }

        return [
          ...current,
          sessionName,
        ];

      }
    );

  }


  /* ================================================= */
  /* EXCLUDED DATE */
  /* ================================================= */

  function addExcludedDate() {

    if (!newExcludedDate) {
      return;
    }

    if (
      excludedDates.includes(
        newExcludedDate
      )
    ) {
      return;
    }

    setExcludedDates(
      (current) => [
        ...current,
        newExcludedDate,
      ]
    );

    setNewExcludedDate("");

  }


  function removeExcludedDate(date) {

    setExcludedDates(
      (current) =>
        current.filter(
          (item) =>
            item !== date
        )
    );

  }

  /* ================================================= */
  /* VIEW TIMETABLE */
  /* ================================================= */

function handleViewTimetable(examinationId) {
  setViewingExaminationId(examinationId);
}


  /* ================================================= */
  /* LOADING */
  /* ================================================= */

  if (loading) {

    return (

      <div className="min-h-screen bg-background">

        <AdminSidebar
          user={user}
          onLogout={onLogout}
          sidebarOpen={sidebarOpen}
          setSidebarOpen={setSidebarOpen}
          activePage="Timetable"
          onNavigate={onNavigate}
        />

        <main className="lg:ml-72">

          <div className="p-8">

            <div className="flex items-center gap-2 text-text-muted">

              <RefreshCw
                size={18}
                className="animate-spin"
              />

              Loading timetable...

            </div>

          </div>

        </main>

      </div>

    );

  }


  /* ================================================= */
  /* PAGE */
  /* ================================================= */

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
        activePage="Timetable"
        onNavigate={onNavigate}
      />


      {/* ================================================= */}
      {/* MAIN */}
      {/* ================================================= */}

      <main className="lg:ml-72">


        {/* ================================================= */}
        {/* TOP BAR */}
        {/* ================================================= */}

        <header className="sticky top-0 z-20 flex h-20 items-center justify-between border-b border-border bg-background/95 px-5 backdrop-blur md:px-8">

          <div className="flex items-center gap-4">

            <button
              type="button"
              onClick={() =>
                setSidebarOpen(true)
              }
              className="rounded-lg p-2 text-sidebar hover:bg-surface lg:hidden"
            >
              <CalendarDays
                size={23}
              />
            </button>


            <div>

              <p className="text-xs font-semibold uppercase tracking-widest text-accent">

                Administration

              </p>

              <h1 className="text-xl font-bold text-text md:text-2xl">

                Timetable

              </h1>

            </div>

          </div>


          <div className="flex items-center gap-3">

            <div className="hidden text-right sm:block">

              <p className="text-sm font-semibold text-text">

                {user?.name ||
                  "Administrator"}

              </p>

              <p className="text-xs text-text-muted">

                Administrator

              </p>

            </div>


            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary font-bold text-white">

              {user?.name
                ? user.name
                    .charAt(0)
                    .toUpperCase()
                : "A"}

            </div>

          </div>

        </header>


        {/* ================================================= */}
        {/* CONTENT */}
        {/* ================================================= */}

        <div className="p-5 md:p-8">

          {/* ================================================= */}
          {/* HEADER */}
          {/* ================================================= */}

          <section className="mb-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">

            <div>

              <p className="text-sm font-medium text-accent">

                Examination Scheduling

              </p>

              <h2 className="mt-1 text-2xl font-bold text-text md:text-3xl">

                Timetable

              </h2>

              <p className="mt-2 text-text-muted">

                Create and manage examination
                timetables.

              </p>

            </div>


            <div className="flex items-center gap-3">

              <button
                type="button"
                onClick={loadData}
                className="flex items-center gap-2 rounded-xl border border-border bg-surface px-4 py-3 text-sm font-semibold text-text hover:bg-background"
              >

                <RefreshCw
                  size={17}
                />

                Refresh

              </button>


              <button
                type="button"
                onClick={
                  handleCreateTimetable
                }
                className="flex items-center gap-2 rounded-xl bg-primary px-4 py-3 text-sm font-semibold text-white hover:opacity-90"
              >

                <Plus
                  size={18}
                />

                Create Timetable

              </button>

            </div>

          </section>


          {/* ================================================= */}
          {/* ERROR */}
          {/* ================================================= */}

          {error && (

            <div className="mb-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">

              {error}

            </div>

          )}


          {/* ================================================= */}
          {/* CREATE FORM */}
          {/* ================================================= */}

          {showCreateForm && (
  <div
    className="fixed inset-0 z-[50] flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm"
    onMouseDown={(event) => {
      if (event.target === event.currentTarget) {
        handleCloseCreateForm();
      }
    }}
  >
    <section className="flex max-h-[90vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl bg-surface shadow-2xl">
       
       <div className="flex items-center justify-between border-b border-border px-6 py-5">
  <div>
    <h3 className="text-lg font-bold text-text">
      Create Timetable
    </h3>

    <p className="mt-1 text-sm text-text-muted">
  Select an examination plan, configure the sessions
  and gap between exams, then generate all timetables in bulk.
</p>
  </div>

  <button
    type="button"
    onClick={handleCloseCreateForm}
    disabled={creating}
    className="rounded-lg p-2 text-text-muted hover:bg-background hover:text-text disabled:opacity-50"
  >
    <X size={20} />
  </button>
</div>

          <div className="overflow-y-auto px-6 py-6">

  {/* EXAMINATION */}

  <div className="mb-6">

                <label className="mb-2 block text-sm font-semibold text-text">

                  Examination

                </label>

<select
  value={selectedPlanKey}
  onChange={(event) => {
    setSelectedPlanKey(event.target.value);
    setSelectedSessions([]);
    setExcludedDates([]);
  }}
  className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-text outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
>
  <option value="">
    Select examination plan
  </option>

  {examinationPlans.map((plan) => (
    <option
      key={plan.key}
      value={plan.key}
    >
      {plan.name} — {plan.exam_type} —{" "}
      {plan.examinations.length} examinations
    </option>
  ))}
</select>

              </div>
{selectedPlan && (
  <div>

    {/* PLAN INFORMATION */}
    <div className="mb-6 rounded-xl border border-border bg-background p-4">

      <div className="grid gap-4 md:grid-cols-3">

        <div>
          <p className="text-xs text-text-muted">
            Date Range
          </p>

          <p className="mt-1 text-sm font-semibold text-text">
            {selectedPlan.start_date} → {selectedPlan.end_date}
          </p>
        </div>

        <div>
          <p className="text-xs text-text-muted">
            Examinations
          </p>

          <p className="mt-1 text-sm font-semibold text-text">
            {selectedExaminations.length}
          </p>
        </div>

        <div>
          <p className="text-xs text-text-muted">
            Duration
          </p>

          <p className="mt-1 text-sm font-semibold text-text">
            {selectedPlan.duration_minutes} minutes
          </p>
        </div>

      </div>

    </div>


    {/* INCLUDED EXAMINATIONS */}
    <div className="mb-6">

      <label className="mb-3 block text-sm font-semibold text-sidebar">
        Included Examinations
      </label>

      <div className="space-y-2">

        {selectedExaminations.map((examination) => {

          const activeSubjectCount = subjects.filter(
            (subject) =>
              Number(subject.course_id) ===
                Number(examination.course_id) &&
              Number(subject.semester) ===
                Number(examination.semester) &&
              subject.is_active
          ).length;

          return (
            <div
              key={examination.id}
              className="rounded-xl border border-border bg-background px-4 py-3"
            >

              <div className="flex items-center justify-between">

                <div>

                  <p className="text-sm font-semibold text-sidebar">
                    {examination.course_name ||
                      examination.course_code ||
                      `Course ${examination.course_id}`}
                  </p>

                  <p className="text-xs text-text-muted">
                    Semester {examination.semester}
                  </p>

                </div>

                <span className="text-xs font-medium text-text-muted">
                  {activeSubjectCount} active subjects
                </span>

              </div>

            </div>
          );

        })}

      </div>

      <p className="mt-2 text-xs text-text-muted">
        Subjects are selected automatically from the active
        subjects for each course and semester.
      </p>

    </div>


   {/* GAP BETWEEN EXAMS */}
<div className="mb-6">

  <label className="mb-2 block text-sm font-semibold text-sidebar">
    Gap Between Exams
  </label>

  <p className="mb-3 text-xs text-text-muted">
  0 means exams can be scheduled on consecutive available days.
  Higher values leave additional available days between exams.
</p>

<input
  type="number"
  min="0"
  step="1"
  value={gapDays}
    onChange={(event) =>
      setGapDays(event.target.value)
    }
    className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-text outline-none transition placeholder:text-text-light focus:border-primary focus:ring-4 focus:ring-primary/10"
  />

</div>


{/* SESSIONS */}
<div className="mb-6">

      <label className="mb-3 block text-sm font-semibold text-sidebar">
        Sessions
      </label>

      <div className="grid gap-3 md:grid-cols-2">

        {availableSessions.map((session) => {

          const sessionName = session.session;

          const selected =
            selectedSessions.includes(sessionName);

          return (
            <button
              key={sessionName}
              type="button"
              onClick={() =>
                toggleSession(sessionName)
              }
              className={`flex items-center justify-between rounded-xl border px-4 py-3 text-left transition ${
                selected
                  ? "border-primary bg-accent-light"
                  : "border-border bg-background hover:bg-surface"
              }`}
            >

              <div>

                <p className="text-sm font-semibold text-text">
                  {sessionName}
                </p>

                <p className="text-xs text-text-muted">
                  {session.start_time} → {session.end_time}
                </p>

              </div>

              {selected && (
                <Check
                  size={18}
                  className="text-primary"
                />
              )}

            </button>
          );

        })}

      </div>

    </div>


    {/* EXCLUDED DATES */}
    <div className="mb-6">

      <label className="mb-3 block text-sm font-semibold text-sidebar">
        Excluded Dates
      </label>

      <div className="flex gap-2">

        <input
          type="date"
          value={newExcludedDate}
          min={selectedPlan.start_date}
          max={selectedPlan.end_date}
          onChange={(event) =>
            setNewExcludedDate(event.target.value)
          }
          className="flex-1 rounded-xl border border-border bg-background px-4 py-3 text-sm text-text outline-none focus:border-primary focus:ring-4 focus:ring-primary/10"
        />

        <button
          type="button"
          onClick={addExcludedDate}
          className="rounded-xl bg-primary px-4 py-3 text-sm font-semibold text-white hover:opacity-90"
        >
          Add
        </button>

      </div>

      {excludedDates.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">

          {excludedDates.map((date) => (
            <div
              key={date}
              className="flex items-center gap-2 rounded-full bg-background px-3 py-1.5 text-xs font-medium text-text"
            >

              {date}

              <button
                type="button"
                onClick={() =>
                  removeExcludedDate(date)
                }
                className="text-text-muted hover:text-red-600"
              >
                <X size={14} />
              </button>

            </div>
          ))}

        </div>
      )}

    </div>


    {/* ACTIONS */}
    <div className="flex justify-end gap-3 border-t border-border pt-5">

      <button
        type="button"
        onClick={handleCloseCreateForm}
        disabled={creating}
        className="rounded-xl border border-border bg-background px-5 py-3 text-sm font-semibold text-text hover:bg-surface disabled:opacity-50"
      >
        Cancel
      </button>

      <button
        type="button"
        onClick={handleGenerate}
        disabled={creating}
        className="flex items-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-semibold text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
      >

        {creating ? (
          <>
            <RefreshCw
              size={17}
              className="animate-spin"
            />
            Generating...
          </>
        ) : (
          <>
            <CalendarDays size={17} />
            Generate Timetable
          </>
        )}

      </button>

    </div>

  </div>
)}
           </div>
</section>
</div>
)}


          {/* ================================================= */}
          {/* EXISTING TIMETABLES */}
          {/* ================================================= */}

          <section>

            <div className="mb-4">

              <h3 className="text-lg font-bold text-text">

                Existing Timetables

              </h3>

              <p className="text-sm text-text-muted">

                Only examinations with generated
                timetable entries are shown here.

              </p>

            </div>


            {existingTimetables.length === 0 ? (

              <div className="rounded-2xl border border-border bg-surface p-8 text-center shadow-sm">

                <CalendarDays
                  size={32}
                  className="mx-auto text-text-muted"
                />

                <p className="mt-3 font-semibold text-text">

                  No timetables created yet.

                </p>

                <p className="mt-1 text-sm text-text-muted">

                  Click "Create Timetable" to
                  create the first examination
                  timetable.

                </p>

              </div>

            ) : (

              <div className="overflow-x-auto rounded-2xl border border-border bg-surface shadow-sm">

                <table className="w-full">

                  <thead>

                    <tr className="border-b border-border bg-background">

                      <th className="p-4 text-left text-sm font-semibold text-text">

                        Examination

                      </th>

                      <th className="p-4 text-left text-sm font-semibold text-text">

                        Course

                      </th>

                      <th className="p-4 text-left text-sm font-semibold text-text">

                        Semester

                      </th>

                      <th className="p-4 text-left text-sm font-semibold text-text">

                        Entries

                      </th>

                      <th className="p-4 text-left text-sm font-semibold text-text">

                        Status

                      </th>

                      <th className="p-4 text-left text-sm font-semibold text-text">

                        Action

                      </th>

                    </tr>

                  </thead>


                  <tbody>

                    {existingTimetables.map(
                      ({
                        examination,
                        entries,
                      }) => (

                        <tr
                          key={
                            examination.id
                          }
                          className="border-b border-border last:border-b-0 hover:bg-background"
                        >

                          <td className="p-4">

                            <p className="font-semibold text-text">

                              {examination.name}

                            </p>

                            <p className="mt-1 text-xs text-text-muted">

                              {examination.exam_type}

                            </p>

                          </td>


                          <td className="p-4 text-sm text-text">

                            {examination.course_name}

                          </td>


                          <td className="p-4 text-sm text-text">

                            Semester{" "}

                            {examination.semester}

                          </td>


                          <td className="p-4 text-sm text-text">

                            {entries.length}

                          </td>


                          <td className="p-4">

                            <span className="rounded-full bg-accent-light px-3 py-1 text-xs font-semibold text-primary">

                              {entries.every(
                                (entry) =>
                                  entry.status ===
                                  "GENERATED"
                              )
                                ? "GENERATED"
                                : "UPDATED"}

                            </span>

                          </td>


                          <td className="p-4">

                            <button
                              type="button"
                              onClick={() =>
                                handleViewTimetable(
                                  examination.id
                                )
                              }
                              className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold text-primary hover:bg-accent-light"
                            >

                              <Eye
                                size={17}
                              />

                              View

                            </button>

                          </td>

                        </tr>

                      )
                    )}

                  </tbody>

                </table>

              </div>

            )}

          </section>

{/* TIMETABLE VIEW */}
{viewingExaminationId && (
  <TimetableView
    examinationId={viewingExaminationId}
    onClose={() => setViewingExaminationId(null)}
  />
)}
        </div>

      </main>

    </div>

  );

}