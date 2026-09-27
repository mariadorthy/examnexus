import { useEffect, useState } from "react";

import {
  X,
  CalendarDays,
  Clock,
  ArrowLeft,
} from "lucide-react";

import { get } from "../../../services/api";


export default function  ExaminationDetails({
  examinationId,
  onClose, 
}) {
  const id = examinationId;

  const [examination, setExamination] = useState(null);
const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");


  async function loadData() {
    try {
      setLoading(true);
      setError("");

      const examinationData = await get(
  `/examinations/${id}`
);

setExamination(examinationData);

    } catch (err) {
      setError(
        err.message ||
        "Failed to load examination."
      );
    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    loadData();
  }, [id]);

  if (loading) {
    return (
      <div className="p-6">
        Loading examination...
      </div>
    );
  }


  if (error && !examination) {
    return (
      <div className="p-6">
        <button
          onClick={onClose}
          className="mb-4"
        >
          <ArrowLeft size={18} />
        </button>

        <p className="text-red-600">
          {error}
        </p>
      </div>
    );
  }


  if (!examination) {
    return (
      <div className="p-6">
        Examination not found.
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
    <div className="flex max-h-[90vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl bg-surface shadow-2xl">

      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-6 py-4">
        <div>
          <h2 className="text-xl font-semibold">
            {examination.name || "Examination Details"}
          </h2>

          <p className="mt-1 text-sm text-gray-500">
            Examination configuration
          </p>
        </div>

        <button
          type="button"
          onClick={onClose}
          className="rounded-lg p-2 text-gray-500 transition hover:bg-accent-light hover:text-gray-900"
          title="Close"
        >
          <X size={20} />
        </button>
      </div>

      {/* Content */}
      <div className="overflow-y-auto p-6">

        {error && (
          <div className="mb-4 text-red-600">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">

          <div>
            <p className="text-sm text-gray-500">
              Examination Type
            </p>

            <p className="font-medium">
              {examination.exam_type || "-"}
            </p>
          </div>

          <div>
            <p className="text-sm text-gray-500">
              Status
            </p>

            <p className="font-medium">
              {examination.status || "-"}
            </p>
          </div>

          <div>
            <p className="text-sm text-gray-500">
              Start Date
            </p>

            <p className="font-medium">
              {examination.start_date || "-"}
            </p>
          </div>

          <div>
            <p className="text-sm text-gray-500">
              End Date
            </p>

            <p className="font-medium">
              {examination.end_date || "-"}
            </p>
          </div>

        </div>

      </div>
    </div>
  </div>
);

}
