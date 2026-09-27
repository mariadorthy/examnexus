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
  generateTimetable,
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
  const [selectedExaminationId, setSelectedExaminationId] =
    useState("");

  const [selectedSubjectIds, setSelectedSubjectIds] =
    useState([]);

  const [selectedSessions, setSelectedSessions] =
    useState([]);

  const [excludedDates, setExcludedDates] =
    useState([]);

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


  /* ================================================= */
  /* SELECTED EXAMINATION */
  /* ================================================= */

  const selectedExamination =
    examinations.find(
      (examination) =>
        String(examination.id) ===
        String(selectedExaminationId)
    );


  /* ================================================= */
  /* AVAILABLE SUBJECTS */
  /* ================================================= */

  const availableSubjects =
    selectedExamination
      ? subjects.filter(
          (subject) =>
            Number(subject.course_id) ===
              Number(
                selectedExamination.course_id
              ) &&
            Number(subject.semester) ===
              Number(
                selectedExamination.semester
              ) &&
            subject.is_active !== false
        )
      : [];


  /* ================================================= */
  /* SESSION CONFIG */
  /* ================================================= */

  const availableSessions =
    selectedExamination?.session_config?.length
      ? selectedExamination.session_config
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

    setSelectedExaminationId("");

    setSelectedSubjectIds([]);

    setSelectedSessions([]);

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
  /* SELECT SUBJECT */
  /* ================================================= */

  function toggleSubject(subjectId) {

    setSelectedSubjectIds(
      (current) => {

        if (
          current.includes(subjectId)
        ) {

          return current.filter(
            (id) =>
              id !== subjectId
          );

        }

        return [
          ...current,
          subjectId,
        ];

      }
    );

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
  /* GENERATE TIMETABLE */
  /* ================================================= */

  async function handleGenerate() {

    setError("");

    if (!selectedExamination) {

      setError(
        "Please select an examination."
      );

      return;

    }

    if (
      selectedSubjectIds.length === 0
    ) {

      setError(
        "Please select at least one subject."
      );

      return;

    }

    if (
      selectedSessions.length === 0
    ) {

      setError(
        "Please select at least one session."
      );

      return;

    }


    try {

      setCreating(true);

      await generateTimetable(
        selectedExamination.id,
        {
          start_date:
            selectedExamination.start_date,

          end_date:
            selectedExamination.end_date,

          subject_ids:
            selectedSubjectIds,

          sessions:
            selectedSessions,

          excluded_dates:
            excludedDates,

          clear_existing: false,
        }
      );


      setShowCreateForm(false);

      setSelectedExaminationId("");

      setSelectedSubjectIds([]);

      setSelectedSessions([]);

      setExcludedDates([]);

      await loadData();

    } catch (err) {

      console.error(
        "Timetable generation error:",
        err
      );

      setError(
        err.message ||
        "Failed to generate timetable."
      );

    } finally {

      setCreating(false);

    }

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

            <section className="mb-8 rounded-2xl border border-border bg-surface p-6 shadow-sm">

              <div className="mb-6 flex items-center justify-between">

                <div>

                  <h3 className="text-lg font-bold text-text">

                    Create Timetable

                  </h3>

                  <p className="mt-1 text-sm text-text-muted">

                    Select an examination,
                    subjects and sessions
                    to generate its timetable.

                  </p>

                </div>


                <button
                  type="button"
                  onClick={
                    handleCloseCreateForm
                  }
                  className="rounded-lg p-2 text-text-muted hover:bg-background hover:text-text"
                >

                  <X size={20} />

                </button>

              </div>


              {/* EXAMINATION */}

              <div className="mb-6">

                <label className="mb-2 block text-sm font-semibold text-text">

                  Examination

                </label>

                <select
                  value={
                    selectedExaminationId
                  }
                  onChange={(event) => {

                    setSelectedExaminationId(
                      event.target.value
                    );

                    setSelectedSubjectIds([]);

                    setSelectedSessions([]);

                    setExcludedDates([]);

                  }}
                  className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none focus:border-primary"
                >

                  <option value="">

                    Select examination

                  </option>

                  {examinations.map(
                    (examination) => (

                      <option
                        key={
                          examination.id
                        }
                        value={
                          examination.id
                        }
                      >

                        {examination.name}

                        {" — "}

                        {examination.course_name}

                        {" — Semester "}

                        {examination.semester}

                      </option>

                    )
                  )}

                </select>

              </div>


              {selectedExamination && (

                <>

                  {/* EXAMINATION INFO */}

                  <div className="mb-6 grid gap-4 rounded-xl bg-background p-4 md:grid-cols-3">

                    <div>

                      <p className="text-xs text-text-muted">

                        Date Range

                      </p>

                      <p className="mt-1 text-sm font-semibold text-text">

                        {selectedExamination.start_date}

                        {" → "}

                        {selectedExamination.end_date}

                      </p>

                    </div>


                    <div>

                      <p className="text-xs text-text-muted">

                        Course

                      </p>

                      <p className="mt-1 text-sm font-semibold text-text">

                        {selectedExamination.course_name}

                      </p>

                    </div>


                    <div>

                      <p className="text-xs text-text-muted">

                        Duration

                      </p>

                      <p className="mt-1 text-sm font-semibold text-text">

                        {selectedExamination.duration_minutes}

                        {" minutes"}

                      </p>

                    </div>

                  </div>


                  {/* SUBJECTS */}

                  <div className="mb-6">

                    <div className="mb-3">

                      <label className="text-sm font-semibold text-text">

                        Subjects

                      </label>

                      <p className="mt-1 text-xs text-text-muted">

                        Subjects matching the selected
                        examination course and semester.

                      </p>

                    </div>


                    {availableSubjects.length === 0 ? (

                      <div className="rounded-xl border border-yellow-200 bg-yellow-50 p-4 text-sm text-yellow-700">

                        No active subjects found
                        for this course and semester.

                      </div>

                    ) : (

                      <div className="grid gap-3 md:grid-cols-2">

                        {availableSubjects.map(
                          (subject) => {

                            const selected =
                              selectedSubjectIds.includes(
                                subject.id
                              );

                            return (

                              <button
                                key={
                                  subject.id
                                }
                                type="button"
                                onClick={() =>
                                  toggleSubject(
                                    subject.id
                                  )
                                }
                                className={`flex items-center gap-3 rounded-xl border p-4 text-left transition ${
                                  selected
                                    ? "border-primary bg-accent-light"
                                    : "border-border bg-background hover:border-accent"
                                }`}
                              >

                                <div
                                  className={`flex h-5 w-5 items-center justify-center rounded border ${
                                    selected
                                      ? "border-primary bg-primary text-white"
                                      : "border-border"
                                  }`}
                                >

                                  {selected && (
                                    <Check
                                      size={14}
                                    />
                                  )}

                                </div>


                                <div>

                                  <p className="text-sm font-semibold text-text">

                                    {subject.subject_code}

                                  </p>

                                  <p className="text-sm text-text-muted">

                                    {subject.subject_name}

                                  </p>

                                </div>

                              </button>

                            );

                          }
                        )}

                      </div>

                    )}

                  </div>


                  {/* SESSIONS */}

                  <div className="mb-6">

                    <div className="mb-3">

                      <label className="text-sm font-semibold text-text">

                        Sessions

                      </label>

                      <p className="mt-1 text-xs text-text-muted">

                        Select the sessions available
                        for timetable generation.

                      </p>

                    </div>


                    <div className="grid gap-3 md:grid-cols-2">

                      {availableSessions.map(
                        (session) => {

                          const sessionName =
                            session.session;

                          const selected =
                            selectedSessions.includes(
                              sessionName
                            );

                          return (

                            <button
                              key={
                                sessionName
                              }
                              type="button"
                              onClick={() =>
                                toggleSession(
                                  sessionName
                                )
                              }
                              className={`rounded-xl border p-4 text-left transition ${
                                selected
                                  ? "border-primary bg-accent-light"
                                  : "border-border bg-background hover:border-accent"
                              }`}
                            >

                              <div className="flex items-center justify-between">

                                <div>

                                  <p className="text-sm font-semibold text-text">

                                    {sessionName}

                                  </p>

                                  <p className="mt-1 text-xs text-text-muted">

                                    {session.start_time}

                                    {" → "}

                                    {session.end_time}

                                  </p>

                                </div>


                                {selected && (

                                  <Check
                                    size={18}
                                    className="text-primary"
                                  />

                                )}

                              </div>

                            </button>

                          );

                        }
                      )}

                    </div>

                  </div>


                  {/* EXCLUDED DATES */}

                  <div className="mb-6">

                    <label className="mb-2 block text-sm font-semibold text-text">

                      Excluded Dates

                    </label>

                    <p className="mb-3 text-xs text-text-muted">

                      Optional dates that should not
                      receive timetable entries.

                    </p>


                    <div className="flex gap-3">

                      <input
                        type="date"
                        value={
                          newExcludedDate
                        }
                        min={
                          selectedExamination.start_date
                        }
                        max={
                          selectedExamination.end_date
                        }
                        onChange={(event) =>
                          setNewExcludedDate(
                            event.target.value
                          )
                        }
                        className="rounded-xl border border-border bg-background px-4 py-3 text-sm"
                      />


                      <button
                        type="button"
                        onClick={
                          addExcludedDate
                        }
                        className="rounded-xl border border-border px-4 py-3 text-sm font-semibold hover:bg-background"
                      >

                        Add

                      </button>

                    </div>


                    {excludedDates.length > 0 && (

                      <div className="mt-3 flex flex-wrap gap-2">

                        {excludedDates.map(
                          (date) => (

                            <button
                              key={date}
                              type="button"
                              onClick={() =>
                                removeExcludedDate(
                                  date
                                )
                              }
                              className="flex items-center gap-2 rounded-full bg-accent-light px-3 py-1 text-xs font-semibold text-primary"
                            >

                              {date}

                              <X
                                size={13}
                              />

                            </button>

                          )
                        )}

                      </div>

                    )}

                  </div>


                  {/* ACTIONS */}

                  <div className="flex justify-end gap-3 border-t border-border pt-5">

                    <button
                      type="button"
                      onClick={
                        handleCloseCreateForm
                      }
                      disabled={creating}
                      className="rounded-xl border border-border px-5 py-3 text-sm font-semibold text-text hover:bg-background"
                    >

                      Cancel

                    </button>


                    <button
                      type="button"
                      onClick={
                        handleGenerate
                      }
                      disabled={creating}
                      className="flex items-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-semibold text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                    >

                      {creating && (

                        <RefreshCw
                          size={17}
                          className="animate-spin"
                        />

                      )}

                      {creating
                        ? "Generating..."
                        : "Generate Timetable"}

                    </button>

                  </div>

                </>

              )}

            </section>

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