          const API_URL =
  `${import.meta.env.VITE_API_BASE_URL}/api/subjects`;

export async function getSubjects() {
  const response = await fetch(API_URL);

  if (!response.ok) {
    throw new Error("Failed to load subjects.");
  }

  return await response.json();
}

export async function createSubject(data) {
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
      result.message || "Failed to create subject."
    );
  }

  return result;
}

export async function updateSubject(id, data) {
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
      result.message || "Failed to update subject."
    );
  }

  return result;
}

export async function deleteSubject(id) {
  const response = await fetch(
    `${API_URL}${id}`,
    {
      method: "DELETE",
    }
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.message || "Failed to delete subject."
    );
  }

  return result;
}
