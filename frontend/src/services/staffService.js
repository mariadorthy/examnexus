      const API_URL =
  `${import.meta.env.VITE_API_BASE_URL}/api/staff`;

export async function getStaff() {
  const response = await fetch(API_URL);

  if (!response.ok) {
    throw new Error("Failed to load staff.");
  }

  return await response.json();
}

export async function createStaff(data) {
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
      result.message || "Failed to create staff."
    );
  }

  return result;
}

export async function updateStaff(id, data) {
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
      result.message || "Failed to update staff."
    );
  }

  return result;
}

export async function deleteStaff(id) {
  const response = await fetch(
    `${API_URL}${id}`,
    {
      method: "DELETE",
    }
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.message || "Failed to delete staff."
    );
  }

  return result;
}
