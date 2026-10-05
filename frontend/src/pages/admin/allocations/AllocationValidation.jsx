import { useEffect, useState } from "react";

import {
  ShieldCheck,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Users,
  Building2,
  Armchair,
} from "lucide-react";

import {
  get,
} from "../../../services/api";


function AllocationValidation({
  examinationId,
  examination,
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [hallValidation, setHallValidation] = useState(null);
  const [invigValidation, setInvigValidation] = useState(null);

  useEffect(() => {
    if (examinationId) {
      loadValidation(examinationId);
    } else {
      setHallValidation(null);
      setInvigValidation(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [examinationId]);

  const loadValidation = async (id) => {
    try {
      setLoading(true);
      setError("");

      const hallData = await get(
        `/allocations/validate/${id}`
      );
      setHallValidation(hallData);

      try {
        const invigData = await get(
          `/allocations/invigilators/validate/${id}`
        );
        setInvigValidation(invigData);
      } catch (invigErr) {
        setInvigValidation({
          status: "INVALID",
          errors: [
            invigErr.message ||
              "Invigilator validation failed",
          ],
        });
      }
    } catch (err) {
      console.error(err);
      setError(
        err.message ||
          "Unable to load validation results."
      );
      setHallValidation(null);
      setInvigValidation(null);
    } finally {
      setLoading(false);
    }
  };

  const overall =
    hallValidation?.status === "VALID" &&
    invigValidation?.status === "VALID"
      ? "VALID"
      : hallValidation?.status === "NOT GENERATED"
      ? "NOT GENERATED"
      : "INVALID";

  return (
    <section className="rounded-2xl border border-border bg-surface shadow-sm">

      <div className="flex flex-col gap-4 border-b border-border p-5 md:flex-row md:items-center md:justify-between md:p-6">

        <div>
          <h2 className="flex items-center gap-2 font-bold text-text">
            <ShieldCheck size={18} className="text-primary" />
            Allocation Validation
          </h2>
          <p className="mt-1 text-sm text-text-muted">
            Independent validation of persisted hall, seat and
            invigilator data.
          </p>
        </div>

        <button
          type="button"
          onClick={() =>
            examinationId && loadValidation(examinationId)
          }
          disabled={!examinationId || loading}
          className="flex w-fit items-center gap-2 rounded-xl border border-border bg-surface px-4 py-2.5 text-sm font-semibold text-sidebar transition hover:border-accent hover:bg-surface-muted disabled:cursor-not-allowed disabled:opacity-60"
        >
          <RefreshCw
            size={16}
            className={loading ? "animate-spin" : ""}
          />
          Re-run Validation
        </button>

      </div>

      {error && (
        <div className="m-5 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertCircle size={19} className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {!loading && hallValidation && (
        <>
          <div
            className={`mx-5 mt-5 rounded-xl border px-4 py-3 text-sm font-semibold ${
              overall === "VALID"
                ? "border-green-200 bg-green-50 text-green-700"
                : overall === "NOT GENERATED"
                ? "border-yellow-200 bg-yellow-50 text-yellow-800"
                : "border-red-200 bg-red-50 text-red-700"
            }`}
          >
            Overall: {overall}
          </div>

          <div className="grid gap-5 p-5 md:grid-cols-2 lg:grid-cols-4">

            <Metric
              label="Eligible Students"
              value={hallValidation.eligible_students ?? 0}
              icon={Users}
            />

            <Metric
              label="Allocated Capacity"
              value={hallValidation.allocated_capacity ?? 0}
              icon={Armchair}
            />

            <Metric
              label="Halls Used"
              value={hallValidation.halls_used ?? 0}
              icon={Building2}
            />

            <Metric
              label="Seat Records"
              value={hallValidation.seat_records ?? 0}
              icon={Armchair}
            />

          </div>

          {hallValidation.errors?.length > 0 && (
            <ErrorList
              title="Hall / Seat Validation Errors"
              errors={hallValidation.errors}
            />
          )}

          {invigValidation?.errors?.length > 0 && (
            <ErrorList
              title="Invigilator Validation Errors"
              errors={invigValidation.errors}
            />
          )}

          <div className="grid gap-5 border-t border-border p-5 md:grid-cols-2">

            <Panel
              title="Hall / Seat Validation"
              status={hallValidation.status}
              details={[
                [
                  "Eligible students",
                  hallValidation.eligible_students ?? 0,
                ],
                [
                  "Allocated capacity",
                  hallValidation.allocated_capacity ?? 0,
                ],
                [
                  "Unallocated students",
                  hallValidation.unallocated_students ?? 0,
                ],
                [
                  "Halls used",
                  hallValidation.halls_used ?? 0,
                ],
                [
                  "Seat records",
                  hallValidation.seat_records ?? 0,
                ],
              ]}
            />

            <Panel
              title="Invigilator Validation"
              status={
                invigValidation?.status || "NOT RUN"
              }
              details={[
                [
                  "Invigilator assignments",
                  invigValidation?.invigilator_assignments ?? 0,
                ],
                [
                  "Distinct staff",
                  invigValidation?.distinct_staff ?? 0,
                ],
              ]}
            />

          </div>
        </>
      )}

      {loading && (
        <div className="flex items-center justify-center py-16">
          <RefreshCw
            size={24}
            className="animate-spin text-accent"
          />
          <span className="ml-3 text-sm text-text-muted">
            Loading validation...
          </span>
        </div>
      )}

      {!loading && !hallValidation && !error && (
        <div className="p-10 text-center">
          <ShieldCheck
            size={26}
            className="mx-auto text-text-muted"
          />
          <p className="mt-3 text-sm text-text-muted">
            Select an examination to run validation.
          </p>
        </div>
      )}

    </section>
  );
}


function Metric({ label, value, icon: Icon }) {
  return (
    <div className="rounded-xl border border-border bg-surface-muted p-4">
      <div className="flex items-start justify-between">
        <p className="text-xs font-medium text-text-muted">
          {label}
        </p>
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-light text-primary">
          <Icon size={15} />
        </div>
      </div>
      <p className="mt-2 text-xl font-bold text-text">
        {value}
      </p>
    </div>
  );
}


function Panel({ title, status, details }) {
  const isOk = status === "VALID";

  return (
    <div className="rounded-xl border border-border bg-surface p-5">
      <div className="flex items-center justify-between">
        <p className="text-sm font-bold text-text">
          {title}
        </p>
        <span
          className={`rounded-full px-3 py-1 text-xs font-semibold ${
            isOk
              ? "bg-green-50 text-success"
              : "bg-yellow-50 text-warning"
          }`}
        >
          {status}
        </span>
      </div>

      <dl className="mt-4 space-y-2 text-sm">
        {details.map(([label, value]) => (
          <div
            key={label}
            className="flex items-center justify-between"
          >
            <dt className="text-text-muted">{label}</dt>
            <dd className="font-semibold text-text">
              {value}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}


function ErrorList({ title, errors }) {
  return (
    <div className="mx-5 mb-5 rounded-xl border border-red-200 bg-red-50 p-4">
      <p className="text-sm font-bold text-red-800">
        {title}
      </p>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-red-700">
        {errors.map((line, idx) => (
          <li key={idx}>{line}</li>
        ))}
      </ul>
    </div>
  );
}


export default AllocationValidation;