import { post } from "./api";

/**
 * Understand an administrator's natural-language examination
 * requirements.
 *
 * This endpoint only interprets the requirement.
 * It does not perform allocation or modify examination data.
 */
export const understandRequirements = async (requirement) => {
  if (
    typeof requirement !== "string" ||
    !requirement.trim()
  ) {
    throw new Error(
      "Please enter an examination requirement."
    );
  }

  return post("/requirements/understand", {
    requirement: requirement.trim(),
  });
};

/**
 * Feature 18 -> allocation workflow (Issue 5).
 *
 * Send a natural-language requirement OR a structured
 * requirement object to the existing apply endpoint.
 *
 * The backend always responds with either:
 *   - a non-mutating proposal (mode === "preview"), or
 *   - an applied result (mode === "applied").
 *
 * This helper never decides preview vs apply: the caller sets
 * `body.confirm` explicitly.
 */
export const applyRequirements = async (
  examinationId,
  body,
) => {
  if (!examinationId) {
    throw new Error(
      "An examination must be selected first."
    );
  }

  return post(
    `/requirements/apply/${examinationId}`,
    body,
  );
};

/**
 * Feature 18 -> allocation workflow, bulk variant (Issue 5).
 *
 * Sends the same structured requirement to /requirements/apply-bulk
 * for a list of examination ids. The backend loops the single-exam
 * logic per examination and returns per-row results.
 */
export const applyRequirementsBulk = async (body) => {
  if (!body || !Array.isArray(body.examination_ids)
      || body.examination_ids.length === 0) {
    throw new Error(
      "Select at least one examination for the bulk workflow."
    );
  }

  return post(
    "/requirements/apply-bulk",
    body,
  );
};