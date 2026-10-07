import { useState } from "react";
import {
  Sparkles,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";

import { understandRequirements } from "../../services/requirementService";


const REQUIREMENT_LABELS = {
  minimize_halls: "Minimize number of halls",
  accessibility_required: "Accessibility requirement",
  exclude_maintenance_halls:
    "Exclude halls under maintenance",
  exclude_unavailable_halls:
    "Exclude unavailable halls",
  avoid_timetable_conflicts:
    "Avoid timetable conflicts",
};


function RequirementUnderstanding() {

  const [requirement, setRequirement] =
    useState("");

  const [result, setResult] =
    useState(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");


  const handleUnderstand = async () => {

    if (!requirement.trim()) {

      setError(
        "Please enter a requirement."
      );

      setResult(null);

      return;
    }


    setLoading(true);
    setError("");
    setResult(null);


    try {

      const data =
        await understandRequirements(
          requirement
        );

      setResult(data);

    } catch (err) {

      const message =
        err?.response?.data?.message ||
        err?.response?.data?.validation?.errors?.join(
          ", "
        ) ||
        err?.message ||
        "Unable to understand the requirement.";

      setError(message);

    } finally {

      setLoading(false);

    }

  };


  const recognizedRequirements =
    result?.requirements
      ? Object.entries(
          result.requirements
        ).filter(
          ([, enabled]) =>
            enabled === true
        )
      : [];


  const unsupportedRequirements =
    result?.unsupported_requirements ||
    [];


  return (

    <div
      className="
        mb-8
        overflow-hidden
        rounded-2xl
        border border-gray-200
        bg-white
        shadow-sm
      "
    >

      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <div
        className="
          border-b border-gray-200
          bg-gray-50
          px-6 py-5
        "
      >

        <div className="flex items-start gap-3">

          <div
            className="
              flex h-10 w-10 shrink-0
              items-center justify-center
              rounded-xl
              bg-sidebar
              text-white
            "
          >
            <Sparkles size={19} />
          </div>


          <div>

            <h2
              className="
                text-lg
                font-semibold
                text-gray-900
              "
            >
              Natural-Language Requirement Understanding
            </h2>


            <p
              className="
                mt-1
                max-w-3xl
                text-sm
                leading-6
                text-gray-600
              "
            >
              Describe examination requirements
              in plain language. The system will
              interpret them without directly
              changing examination or allocation
              data.
            </p>

          </div>

        </div>

      </div>


      {/* ================================================= */}
      {/* CONTENT */}
      {/* ================================================= */}

      <div className="p-6">

        <div className="space-y-4">

          {/* ================================================= */}
          {/* INPUT */}
          {/* ================================================= */}

          <div>

            <label
              htmlFor="examination-requirement"
              className="
                mb-2
                block
                text-sm
                font-medium
                text-gray-800
              "
            >
              Examination Requirement
            </label>


            <textarea
              id="examination-requirement"
              value={requirement}
              onChange={(event) =>
                setRequirement(
                  event.target.value
                )
              }
              placeholder="Example: Use the minimum number of halls and keep students requiring accessibility support in accessible halls."
              rows={4}
              className="
                w-full
                resize-y
                rounded-xl
                border border-gray-300
                bg-white
                px-4 py-3
                text-sm
                text-gray-900
                outline-none
                transition
                placeholder:text-gray-400
                focus:border-primary
                focus:ring-2
                focus:ring-primary/20
              "
            />

          </div>


          {/* ================================================= */}
          {/* ACTION */}
          {/* ================================================= */}

          <div>

            <button
              type="button"
              onClick={handleUnderstand}
              disabled={loading}
              className="
                inline-flex
                items-center
                gap-2
                rounded-xl
                bg-primary
                px-5 py-2.5
                text-sm
                font-semibold
                text-white
                shadow-sm
                transition
                hover:opacity-90
                disabled:cursor-not-allowed
                disabled:opacity-50
              "
            >

              <Sparkles size={17} />

              {loading
                ? "Understanding..."
                : "Understand Requirements"}

            </button>

          </div>


          {/* ================================================= */}
          {/* ERROR */}
          {/* ================================================= */}

          {error && (

            <div
              className="
                flex
                items-start
                gap-3
                rounded-xl
                border border-red-200
                bg-red-50
                p-4
                text-sm
                text-red-700
              "
            >

              <AlertCircle
                size={18}
                className="mt-0.5 shrink-0"
              />

              <span>
                {error}
              </span>

            </div>

          )}


          {/* ================================================= */}
          {/* RESULT */}
          {/* ================================================= */}

          {result && (

            <div
              className="
                overflow-hidden
                rounded-xl
                border border-gray-200
                bg-gray-50
              "
            >

              {/* ================================================= */}
              {/* RESULT HEADER */}
              {/* ================================================= */}

              <div
                className="
                  border-b border-gray-200
                  px-5 py-4
                "
              >

                <div className="flex items-center gap-2">

                  <CheckCircle2
                    size={18}
                    className="text-primary"
                  />

                  <h3
                    className="
                      text-sm
                      font-semibold
                      text-gray-900
                    "
                  >
                    Interpreted Requirements
                  </h3>

                </div>

              </div>


              <div className="space-y-5 p-5">

                {/* ================================================= */}
                {/* SUPPORTED */}
                {/* ================================================= */}

                {recognizedRequirements.length === 0 ? (

                  <p
                    className="
                      text-sm
                      text-gray-600
                    "
                  >
                    No supported requirements
                    were identified.
                  </p>

                ) : (

                  <div className="space-y-2">

                    {recognizedRequirements.map(
                      ([key]) => (

                        <div
                          key={key}
                          className="
                            flex
                            items-center
                            gap-3
                            rounded-lg
                            border border-gray-200
                            bg-white
                            px-4 py-3
                          "
                        >

                          <div
                            className="
                              flex h-7 w-7
                              shrink-0
                              items-center
                              justify-center
                              rounded-full
                              bg-accent/10
                              text-accent
                            "
                          >
                            <CheckCircle2
                              size={16}
                            />
                          </div>


                          <span
                            className="
                              text-sm
                              font-medium
                              text-gray-800
                            "
                          >
                            {REQUIREMENT_LABELS[key] ||
                              key}
                          </span>

                        </div>

                      )
                    )}

                  </div>

                )}


                {/* ================================================= */}
                {/* UNSUPPORTED */}
                {/* ================================================= */}

                {unsupportedRequirements.length > 0 && (

                  <div>

                    <div
                      className="
                        mb-3
                        flex
                        items-center
                        gap-2
                      "
                    >

                      <AlertCircle
                        size={17}
                        className="text-accent"
                      />

                      <h3
                        className="
                          text-sm
                          font-semibold
                          text-gray-900
                        "
                      >
                        Unsupported Requirements
                      </h3>

                    </div>


                    <div className="space-y-2">

                      {unsupportedRequirements.map(
                        (item, index) => (

                          <div
                            key={`${item.requirement}-${index}`}
                            className="
                              rounded-lg
                              border border-gray-200
                              bg-white
                              p-4
                            "
                          >

                            <p
                              className="
                                text-sm
                                font-medium
                                text-gray-900
                              "
                            >
                              {item.requirement}
                            </p>


                            <p
                              className="
                                mt-1
                                text-sm
                                leading-5
                                text-gray-600
                              "
                            >
                              {item.reason}
                            </p>

                          </div>

                        )
                      )}

                    </div>

                  </div>

                )}


                {/* ================================================= */}
                {/* SAFETY / SOURCE OF TRUTH */}
                {/* ================================================= */}

                <div
                  className="
                    border-t border-gray-200
                    pt-4
                  "
                >

                  <div
                    className="
                      rounded-lg
                      border border-gray-200
                      bg-white
                      px-4 py-3
                    "
                  >

                    <p
                      className="
                        text-xs
                        leading-5
                        text-gray-500
                      "
                    >
                      These interpreted requirements do
                      not directly modify examinations,
                      halls, seats, invigilators,
                      approvals, or published data.
                      Existing deterministic allocation
                      and validation remain the source
                      of truth.
                    </p>

                  </div>

                </div>

              </div>

            </div>

          )}

        </div>

      </div>

    </div>

  );
}


export default RequirementUnderstanding;