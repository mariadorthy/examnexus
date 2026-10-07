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