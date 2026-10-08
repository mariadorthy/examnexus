import { get, post } from "./api";

const API_URL =
  `${import.meta.env.VITE_API_BASE_URL}/api/departments`;

export async function getDepartments() {
  return await get("/departments");
}

export async function createDepartment(data) {
  return await post("/departments", data);
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
