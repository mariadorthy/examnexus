const API_URL =
  `${import.meta.env.VITE_API_URL || "http://127.0.0.1:5000"}/api/examinations/`;

export async function getExaminations() {
  const response = await fetch(API_URL);

  if (!response.ok) {
    throw new Error("Failed to load examinations.");
  }

  return await response.json();
}

export async function createExamination(data) {
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
      result.message || "Failed to create examination."
    );
  }

  return result;
}

export async function updateExamination(id, data) {
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
      result.message || "Failed to update examination."
    );
  }

  return result;
}

export async function deleteExamination(id) {
  const response = await fetch(
    `${API_URL}${id}`,
    {
      method: "DELETE",
    }
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.message || "Failed to delete examination."
    );
  }

  return result;
}
