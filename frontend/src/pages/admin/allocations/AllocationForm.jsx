import { useEffect, useState } from "react";
import {
  X,
  Building2,
  Loader2,
} from "lucide-react";

import { get, patch } from "../../../services/api";


function AllocationForm({
  allocation,
  onClose,
  onSuccess,
}) {

  const [halls, setHalls] = useState([]);

  const [hallId, setHallId] = useState(
    allocation?.hall_id || ""
  );

  const [allocatedCapacity, setAllocatedCapacity] =
    useState(
      allocation?.allocated_capacity ?? ""
    );

  const [purpose, setPurpose] = useState(
    allocation?.purpose || "NORMAL"
  );

  const [loadingHalls, setLoadingHalls] =
    useState(true);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  useEffect(() => {

    loadHalls();

  }, []);

  useEffect(() => {

    setHallId(allocation?.hall_id || "");
    setAllocatedCapacity(
      allocation?.allocated_capacity ?? ""
    );
    setPurpose(allocation?.purpose || "NORMAL");

  }, [allocation]);

  const loadHalls = async () => {

    try {

      setLoadingHalls(true);

      const data = await get("/halls/");

      setHalls(Array.isArray(data) ? data : []);

    } catch (err) {

      console.error("Halls load error:", err);

      setError(
        err.message ||
        "Unable to load halls."
      );

    } finally {

      setLoadingHalls(false);

    }
  };

  const handleSubmit = async (event) => {

    event.preventDefault();

    setError("");

    const capacity = Number(allocatedCapacity);

    if (!hallId) {

      setError("Please select a hall.");
      return;
    }

    if (
      !allocatedCapacity ||
      Number.isNaN(capacity) ||
      capacity <= 0
    ) {

      setError(
        "Allocated capacity must be greater than zero."
      );
      return;
    }

    try {

      setLoading(true);

      await patch(
        `/allocations/${allocation.id}`,
        {
          hall_id: Number(hallId),
          allocated_capacity: capacity,
          purpose,
        }
      );

      onSuccess();

    } catch (err) {

      console.error(
        "Allocation update error:",
        err
      );

      setError(
        err.message ||
        "Unable to update hall allocation."
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
        z-[70]
        flex
        items-center
        justify-center
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
          w-full
          max-w-lg
          overflow-hidden
          rounded-2xl
          bg-surface
          shadow-2xl
        "
      >

        <div
          className="
            flex
            items-center
            justify-between
            border-b
            border-border
            px-6
            py-5
          "
        >

          <div className="flex items-center gap-3">

            <div
              className="
                flex
                h-11
                w-11
                items-center
                justify-center
                rounded-xl
                bg-accent-light
                text-primary
              "
            >
              <Building2 size={21} />
            </div>

            <div>

              <h2
                className="
                  text-lg
                  font-bold
                  text-text
                "
              >
                Edit Hall Allocation
              </h2>

              <p
                className="
                  text-sm
                  text-text-muted
                "
              >
                Update the hall, capacity or purpose
                for this allocation.
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

        <form
          onSubmit={handleSubmit}
          className="p-6"
        >

          {error && (

            <div
              className="
                mb-5
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
              {error}
            </div>

          )}

          <div className="mb-5">

            <label
              className="
                mb-2
                block
                text-sm
                font-semibold
                text-sidebar
              "
            >
              Hall
            </label>

            <select
              value={hallId}
              onChange={(event) =>
                setHallId(event.target.value)
              }
              disabled={loadingHalls}
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
                disabled:opacity-60
              "
            >

              <option value="">
                {loadingHalls
                  ? "Loading halls..."
                  : "Select a hall"}
              </option>

              {halls.map((hall) => (

                <option
                  key={hall.id}
                  value={hall.id}
                >
                  {`${hall.name} • ${hall.building_name} • Floor ${hall.floor_no} • Cap ${hall.examination_capacity}${hall.is_accessible ? " • Accessible" : ""}`}
                </option>

              ))}

            </select>

          </div>

          <div className="mb-5">

            <label
              className="
                mb-2
                block
                text-sm
                font-semibold
                text-sidebar
              "
            >
              Allocated Capacity
            </label>

            <input
              type="number"
              min="1"
              value={allocatedCapacity}
              onChange={(event) =>
                setAllocatedCapacity(
                  event.target.value
                )
              }
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
            />

            <p
              className="
                mt-1.5
                text-xs
                text-text-light
              "
            >
              Must be greater than zero and must not
              exceed the selected hall examination
              capacity.
            </p>

          </div>

          <div className="mb-7">

            <label
              className="
                mb-2
                block
                text-sm
                font-semibold
                text-sidebar
              "
            >
              Purpose
            </label>

            <select
              value={purpose}
              onChange={(event) =>
                setPurpose(event.target.value)
              }
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
              <option value="NORMAL">NORMAL</option>
              <option value="ACCESSIBILITY">
                ACCESSIBILITY
              </option>
              <option value="MIXED">MIXED</option>
            </select>

          </div>

          <div
            className="
              flex
              flex-col-reverse
              gap-3
              sm:flex-row
              sm:justify-end
            "
          >

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
              disabled={loading || loadingHalls}
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

              {loading ? "Saving..." : "Save Changes"}

            </button>

          </div>

        </form>

      </div>

    </div>
  );
}

export default AllocationForm;