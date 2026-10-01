import { post } from "./api";

const API_URL =
  `${import.meta.env.VITE_API_URL || "http://127.0.0.1:5000"}/api/exam-registrations/`;

export async function getExamRegistrations() {
  const response = await fetch(API_URL);

  if (!response.ok) {
    throw new Error(
      "Failed to load exam registrations."
    );
  }

  return await response.json();
}

export async function createExamRegistration(data) {
  const response = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.message ||
        "Failed to create exam registration."
    );
  }

  return result;
}

export async function updateExamRegistration(
  id,
  data
) {
  const response = await fetch(
    `${API_URL}${id}`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    }
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.message ||
        "Failed to update exam registration."
    );
  }

  return result;
}

export async function deleteExamRegistration(id) {
  const response = await fetch(
    `${API_URL}${id}`,
    {
      method: "DELETE",
    }
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.message ||
        "Failed to delete exam registration."
    );
  }

  return result;
}

export async function previewBulkExamRegistrations(data) {
  return await post(
    "/exam-registrations/bulk-preview",
    data
  );
}

export async function createBulkExamRegistrations(data) {
  return await post(
    "/exam-registrations/bulk",
    data
  );
}