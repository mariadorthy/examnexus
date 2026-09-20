const API_URL =
  `${import.meta.env.VITE_API_URL || "http://127.0.0.1:5000"}/api/departments/`;

export async function getDepartments() {
  const response = await fetch(API_URL);

  if (!response.ok) {
    throw new Error("Failed to load departments.");
  }

  return await response.json();
}

export async function createDepartment(data) {
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
      result.message || "Failed to create department."
    );
  }

  return result;
}

export async function updateDepartment(id, data) {
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
      result.message || "Failed to update department."
    );
  }

  return result;
}

export async function deleteDepartment(id) {
  const response = await fetch(
    `${API_URL}${id}`,
    {
      method: "DELETE",
    }
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.message || "Failed to delete department."
    );
  }

  return result;
}
