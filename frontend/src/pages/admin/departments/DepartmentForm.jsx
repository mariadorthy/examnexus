import { useEffect, useState } from "react";
import {
  X,
  Building2,
  Loader2,
} from "lucide-react";

import { post, put } from "../../../services/api";
const API_URL =
  "http://127.0.0.1:5000/api/departments";

function DepartmentForm({
  department,
  onClose,
  onSuccess,
}) {

  const isEdit = Boolean(department);


  const [departmentCode, setDepartmentCode] =
    useState(
      department?.department_code || ""
    );


  const [departmentName, setDepartmentName] =
    useState(
      department?.department_name || ""
    );


  const [error, setError] = useState("");

  const [loading, setLoading] = useState(false);


  useEffect(() => {

    setDepartmentCode(
      department?.department_code || ""
    );

    setDepartmentName(
      department?.department_name || ""
    );

  }, [department]);


  const handleSubmit = async (event) => {

    event.preventDefault();

    setError("");


    const code =
      departmentCode.trim().toUpperCase();

    const name =
      departmentName.trim();


    if (!code) {

      setError(
        "Please enter a department code."
      );

      return;
    }


    if (!name) {

      setError(
        "Please enter a department name."
      );

      return;
    }


    try {

      setLoading(true);

const data = isEdit
  ? await put(
      `/departments/${department.id}`,
      {
        department_code: code,
        department_name: name,
      }
    )
  : await post(
      "/departments",
      {
        department_code: code,
        department_name: name,
      }
    );


      onSuccess();

    } catch (err) {

      console.error(
        "Department form error:",
        err
      );

      setError(
        err.message ||
        "Unable to save department."
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
        bg-black/40
        p-4
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
          w-full
          max-w-lg
          overflow-hidden
          rounded-2xl
          bg-surface
          shadow-2xl
        "
      >

        <div className="
          flex
          items-center
          justify-between
          border-b
          border-border
          px-6
          py-5
        ">

          <div className="flex items-center gap-3">

            <div className="
              flex
              h-11
              w-11
              items-center
              justify-center
              rounded-xl
              bg-accent-light
              text-primary
            ">
              <Building2 size={21} />
            </div>

            <div>

              <h2 className="
                text-lg
                font-bold
                text-text
              ">
                {isEdit
                  ? "Edit Department"
                  : "Add Department"}
              </h2>

              <p className="
                text-sm
                text-text-muted
              ">
                {isEdit
                  ? "Update department information."
                  : "Create a new academic department."}
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

            <div className="
              mb-5
              rounded-xl
              border
              border-red-200
              bg-red-50
              px-4
              py-3
              text-sm
              text-red-700
            ">
              {error}
            </div>

          )}


          <div className="mb-5">

            <label className="
              mb-2
              block
              text-sm
              font-semibold
              text-sidebar
            ">
              Department Code
            </label>

            <input
              type="text"
              value={departmentCode}
              onChange={(event) =>
                setDepartmentCode(
                  event.target.value
                )
              }
              placeholder="e.g. CSE"
              maxLength={20}
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

            <p className="
              mt-1.5
              text-xs
              text-text-light
            ">
              Maximum 20 characters.
            </p>

          </div>


          <div className="mb-7">

            <label className="
              mb-2
              block
              text-sm
              font-semibold
              text-sidebar
            ">
              Department Name
            </label>

            <input
              type="text"
              value={departmentName}
              onChange={(event) =>
                setDepartmentName(
                  event.target.value
                )
              }
              placeholder="e.g. Computer Science and Engineering"
              maxLength={100}
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


          <div className="
            flex
            flex-col-reverse
            gap-3
            sm:flex-row
            sm:justify-end
          ">

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
                ? (
                    isEdit
                      ? "Saving..."
                      : "Creating..."
                  )
                : (
                    isEdit
                      ? "Save Changes"
                      : "Create Department"
                  )}

            </button>

          </div>

        </form>

      </div>

    </div>
  );
}


export default DepartmentForm;
