import React, { useEffect, useRef, useState } from "react";
import "./CsvImport.css";


const ENTITY_LABELS = {
  departments: "Departments",
  courses: "Courses",
  subjects: "Subjects",
  students: "Students",
  staff: "Staff",
  halls: "Halls",
};


function CsvImport({
  entity,
  isOpen,
  onClose,
  onValidate,
  onImport,
}) {
  const fileInputRef = useRef(null);

  const [file, setFile] = useState(null);
  const [validationResult, setValidationResult] = useState(null);
  const [importResult, setImportResult] = useState(null);

  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState("");

  const entityLabel =
    ENTITY_LABELS[entity] || entity || "Master Data";


  useEffect(() => {
    if (!isOpen) {
      resetState();
    }
  }, [isOpen]);


  const resetState = () => {
    setFile(null);
    setValidationResult(null);
    setImportResult(null);
    setLoading(false);
    setImporting(false);
    setError("");

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };


  const handleClose = () => {
    resetState();

    if (onClose) {
      onClose();
    }
  };


  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0];

    setError("");
    setValidationResult(null);
    setImportResult(null);

    if (!selectedFile) {
      setFile(null);
      return;
    }

    const fileName = selectedFile.name.toLowerCase();

    if (!fileName.endsWith(".csv")) {
      setFile(null);
      setError("Please select a CSV file.");

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      return;
    }

    setFile(selectedFile);
  };


  const handleValidate = async () => {
    if (!file) {
      setError("Please select a CSV file first.");
      return;
    }

    if (!onValidate) {
      setError(
        "CSV validation handler is not configured."
      );
      return;
    }

    setLoading(true);
    setError("");
    setValidationResult(null);
    setImportResult(null);

    try {
      const result = await onValidate(
        entity,
        file
      );

      if (!result || result.success === false) {
        setError(
          result?.message ||
          "CSV validation failed."
        );
        return;
      }

      setValidationResult(result);
    } catch (err) {
      setError(
        err?.message ||
        "Unable to validate the CSV file."
      );
    } finally {
      setLoading(false);
    }
  };


  const handleImport = async () => {
    if (!file) {
      setError("Please select a CSV file first.");
      return;
    }

    if (!validationResult) {
      setError(
        "Please validate the CSV before importing."
      );
      return;
    }

    if (validationResult.valid_rows <= 0) {
      setError(
        "There are no valid rows available for import."
      );
      return;
    }

    if (!onImport) {
      setError(
        "CSV import handler is not configured."
      );
      return;
    }

    setImporting(true);
    setError("");
    setImportResult(null);

    try {
      const result = await onImport(
        entity,
        file
      );

      if (!result || result.success === false) {
        setError(
          result?.message ||
          "CSV import failed."
        );
        return;
      }

      setImportResult(result);
    } catch (err) {
      setError(
        err?.message ||
        "Unable to import the CSV file."
      );
    } finally {
      setImporting(false);
    }
  };


  const handleChooseAnotherFile = () => {
    resetState();

    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };


  if (!isOpen) {
    return null;
  }


  const rows =
    validationResult?.rows || [];


  return (
    <div className="csv-import-overlay">
      <div className="csv-import-modal">

        <div className="csv-import-header">
          <div>
            <h2>Import {entityLabel}</h2>

            <p>
              Upload a CSV file, validate it, preview the
              results, and import only valid rows.
            </p>
          </div>

          <button
            type="button"
            className="csv-import-close"
            onClick={handleClose}
            disabled={loading || importing}
            aria-label="Close"
          >
            ×
          </button>
        </div>


        <div className="csv-import-body">

          {!importResult && (
            <>
              <div className="csv-import-upload-section">

                <label
                  htmlFor="csv-import-file"
                  className="csv-import-file-label"
                >
                  CSV File
                </label>

                <input
                  ref={fileInputRef}
                  id="csv-import-file"
                  type="file"
                  accept=".csv,text/csv"
                  onChange={handleFileChange}
                  disabled={loading || importing}
                />

                {file && (
                  <div className="csv-import-selected-file">
                    <strong>Selected file:</strong>{" "}
                    {file.name}

                    <span>
                      ({Math.round(file.size / 1024)} KB)
                    </span>
                  </div>
                )}

                <p className="csv-import-help">
                  Only .csv files are accepted.
                </p>
              </div>


              {error && (
                <div className="csv-import-error">
                  {error}
                </div>
              )}


              <div className="csv-import-actions">

                <button
                  type="button"
                  className="csv-import-secondary-button"
                  onClick={handleChooseAnotherFile}
                  disabled={loading || importing}
                >
                  Choose File
                </button>

                <button
                  type="button"
                  className="csv-import-primary-button"
                  onClick={handleValidate}
                  disabled={
                    !file ||
                    loading ||
                    importing
                  }
                >
                  {loading
                    ? "Validating..."
                    : "Validate CSV"}
                </button>

              </div>


              {validationResult && (
                <div className="csv-import-results">

                  <div className="csv-import-summary">

                    <div className="csv-summary-card">
                      <span>Total</span>
                      <strong>
                        {validationResult.total_rows || 0}
                      </strong>
                    </div>

                    <div className="csv-summary-card valid">
                      <span>Valid</span>
                      <strong>
                        {validationResult.valid_rows || 0}
                      </strong>
                    </div>

                    <div className="csv-summary-card invalid">
                      <span>Invalid</span>
                      <strong>
                        {validationResult.invalid_rows || 0}
                      </strong>
                    </div>

                    <div className="csv-summary-card duplicate">
                      <span>Duplicates</span>
                      <strong>
                        {validationResult.duplicate_rows || 0}
                      </strong>
                    </div>

                  </div>


                  <div className="csv-preview-section">

                    <div className="csv-preview-header">
                      <div>
                        <h3>CSV Preview</h3>

                        <p>
                          Only rows marked as valid will be
                          imported.
                        </p>
                      </div>
                    </div>


                    <div className="csv-preview-table-wrapper">
                      <table className="csv-preview-table">

                        <thead>
                          <tr>
                            <th>Row</th>
                            <th>Status</th>
                            <th>Data</th>
                            <th>Reason</th>
                          </tr>
                        </thead>

                        <tbody>

                          {rows.map((row) => (
                            <tr
                              key={row.row_number}
                              className={`csv-row-${row.status}`}
                            >
                              <td>
                                {row.row_number}
                              </td>

                              <td>
                                <span
                                  className={`csv-status-badge ${row.status}`}
                                >
                                  {row.status}
                                </span>
                              </td>

                              <td>
                                <div className="csv-row-data">
                                  {Object.entries(
                                    row.data || {}
                                  ).map(
                                    ([key, value]) => (
                                      <div
                                        key={key}
                                        className="csv-data-item"
                                      >
                                        <strong>
                                          {key}:
                                        </strong>{" "}
                                        {value || "—"}
                                      </div>
                                    )
                                  )}
                                </div>
                              </td>

                              <td>
                                {row.errors?.length > 0 ? (
                                  <ul className="csv-error-list">
                                    {row.errors.map(
                                      (message, index) => (
                                        <li key={index}>
                                          {message}
                                        </li>
                                      )
                                    )}
                                  </ul>
                                ) : (
                                  "—"
                                )}
                              </td>
                            </tr>
                          ))}

                        </tbody>

                      </table>
                    </div>

                  </div>


                  <div className="csv-import-actions">

                    <button
                      type="button"
                      className="csv-import-secondary-button"
                      onClick={handleChooseAnotherFile}
                      disabled={loading || importing}
                    >
                      Choose Another File
                    </button>

                    <button
                      type="button"
                      className="csv-import-primary-button"
                      onClick={handleImport}
                      disabled={
                        importing ||
                        validationResult.valid_rows <= 0
                      }
                    >
                      {importing
                        ? "Importing..."
                        : "Import Valid Rows"}
                    </button>

                  </div>

                </div>
              )}

            </>
          )}


          {importResult && (
            <div className="csv-import-success-section">

              <div className="csv-import-success-icon">
                ✓
              </div>

              <h3>
                Import Completed
              </h3>

              <p>
                The valid {entityLabel.toLowerCase()} records
                have been imported successfully.
              </p>


              <div className="csv-import-summary">

                <div className="csv-summary-card">
                  <span>Total</span>
                  <strong>
                    {importResult.summary?.total_rows || 0}
                  </strong>
                </div>

                <div className="csv-summary-card valid">
                  <span>Imported</span>
                  <strong>
                    {importResult.summary?.imported_rows || 0}
                  </strong>
                </div>

                <div className="csv-summary-card invalid">
                  <span>Invalid</span>
                  <strong>
                    {importResult.summary?.invalid_rows || 0}
                  </strong>
                </div>

                <div className="csv-summary-card duplicate">
                  <span>Duplicates</span>
                  <strong>
                    {importResult.summary?.duplicate_rows || 0}
                  </strong>
                </div>

              </div>


              <div className="csv-import-final-actions">

                <button
                  type="button"
                  className="csv-import-primary-button"
                  onClick={handleClose}
                >
                  Done
                </button>

              </div>

            </div>
          )}

        </div>

      </div>
    </div>
  );
}


export default CsvImport;