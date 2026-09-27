import { useEffect, useState } from "react";
import {
  RefreshCw,
  Pencil,
  X,
} from "lucide-react";

import {
  getTimetable,
  updateTimetableEntry,
} from "../../../services/timetableService";


export default function TimetableView({
  examinationId,
    onClose,
}) {
  const id = examinationId;

  const [timetable, setTimetable] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [editingId, setEditingId] =
    useState(null);


 async function loadTimetable() {
  if (!id) {
    setError("No examination selected.");
    setLoading(false);
    return;
  }

  try {
      setLoading(true);
      setError("");

      const data = await getTimetable(id);

      setTimetable(data);

    } catch (err) {
      setError(
        err.message ||
        "Failed to load timetable."
      );
    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    loadTimetable();
  }, [id]);

  async function handleSave(entry) {
    try {
      await updateTimetableEntry(
        entry.id,
        {
          exam_date: entry.exam_date,
          session: entry.session,
          start_time: entry.start_time,
          end_time: entry.end_time,
        }
      );

      setEditingId(null);

      await loadTimetable();

    } catch (err) {
      setError(
        err.message ||
        "Failed to update timetable."
      );
    }
  }


 if (loading) {
  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm">
      <div className="rounded-2xl bg-surface px-8 py-6 shadow-2xl">
        Loading timetable...
      </div>
    </div>
  );
}


 return (
  <div
    className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm"
    onMouseDown={(event) => {
      if (event.target === event.currentTarget) {
  onClose?.();
}
    }}
  >
    <div className="flex max-h-[90vh] w-full max-w-6xl flex-col overflow-hidden rounded-2xl bg-surface shadow-2xl">

<div className="flex items-center justify-between">

  <div>
    <h1 className="text-2xl font-semibold">
      Timetable
    </h1>

    <p className="text-gray-500">
      Examination timetable entries
    </p>
  </div>

  <div className="flex items-center gap-3">

    <button
      type="button"
      onClick={loadTimetable}
      className="flex items-center gap-2"
    >
      <RefreshCw size={18} />
      Refresh
    </button>

    <button
      type="button"
      onClick={onClose}
      className="rounded-lg p-2 text-gray-500 hover:bg-background hover:text-text"
      title="Close"
    >
      <X size={20} />
    </button>

  </div>

</div>

      {error && (
        <div className="text-red-600">
          {error}
        </div>
      )}


      {timetable.length === 0 ? (
        <div className="border rounded p-6">
          No timetable entries found.
        </div>
      ) : (

        <div className="overflow-x-auto border rounded">

          <table className="w-full">

            <thead>
              <tr>

                <th className="p-3 text-left">
                  Date
                </th>

                <th className="p-3 text-left">
                  Session
                </th>

                <th className="p-3 text-left">
                  Subject
                </th>

                <th className="p-3 text-left">
                  Start
                </th>

                <th className="p-3 text-left">
                  End
                </th>

                <th className="p-3 text-left">
                  Status
                </th>

                <th className="p-3 text-left">
                  Action
                </th>

              </tr>
            </thead>


            <tbody>

              {timetable.map(
                (entry) => {

                  const isEditing =
                    editingId === entry.id;

                  return (
                    <tr key={entry.id}>

                      <td className="p-3">

                        {isEditing ? (
                          <input
                            type="date"
                            value={entry.exam_date}
                            onChange={(event) => {
                              setTimetable(
                                (current) =>
                                  current.map(
                                    (item) =>
                                      item.id === entry.id
                                        ? {
                                            ...item,
                                            exam_date:
                                              event.target.value,
                                          }
                                        : item
                                  )
                              );
                            }}
                          />
                        ) : (
                          entry.exam_date
                        )}

                      </td>


                      <td className="p-3">

                        {isEditing ? (
                          <select
                            value={entry.session}
                            onChange={(event) => {
                              setTimetable(
                                (current) =>
                                  current.map(
                                    (item) =>
                                      item.id === entry.id
                                        ? {
                                            ...item,
                                            session:
                                              event.target.value,
                                          }
                                        : item
                                  )
                              );
                            }}
                          >
                            <option value="FN">
                              FN
                            </option>

                            <option value="AN">
                              AN
                            </option>

                          </select>
                        ) : (
                          entry.session
                        )}

                      </td>


                      <td className="p-3">
                        {entry.subject_code
  ? `${entry.subject_code} - ${entry.subject_name}`
  : entry.subject_id}
                      </td>


                      <td className="p-3">

                        {isEditing ? (
                          <input
                            type="time"
                            value={entry.start_time}
                            onChange={(event) => {
                              setTimetable(
                                (current) =>
                                  current.map(
                                    (item) =>
                                      item.id === entry.id
                                        ? {
                                            ...item,
                                            start_time:
                                              event.target.value,
                                          }
                                        : item
                                  )
                              );
                            }}
                          />
                        ) : (
                          entry.start_time
                        )}

                      </td>


                      <td className="p-3">

                        {isEditing ? (
                          <input
                            type="time"
                            value={entry.end_time}
                            onChange={(event) => {
                              setTimetable(
                                (current) =>
                                  current.map(
                                    (item) =>
                                      item.id === entry.id
                                        ? {
                                            ...item,
                                            end_time:
                                              event.target.value,
                                          }
                                        : item
                                  )
                              );
                            }}
                          />
                        ) : (
                          entry.end_time
                        )}

                      </td>


                      <td className="p-3">
                        {entry.status}
                      </td>


                      <td className="p-3">

                        {isEditing ? (

                          <button
                            onClick={() =>
                              handleSave(entry)
                            }
                          >
                            Save
                          </button>

                        ) : (

                          <button
                            onClick={() =>
                              setEditingId(
                                entry.id
                              )
                            }
                            className="flex items-center gap-1"
                          >
                            <Pencil size={16} />
                            Edit
                          </button>

                        )}

                      </td>

                    </tr>
                  );
                }
              )}

            </tbody>

          </table>

        </div>

      )}
      </div>
    </div>
  );
}