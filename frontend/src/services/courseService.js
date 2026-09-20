const API_URL =
  `${import.meta.env.VITE_API_URL || "http://127.0.0.1:5000"}/api/courses/`;

export async function getCourses() {
  const response = await fetch(API_URL);

  if (!response.ok) {
    throw new Error("Failed to load courses.");
  }

  return await response.json();
}

export async function createCourse(data) {
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
      result.message || "Failed to create course."
    );
  }

  return result;
}

export async function updateCourse(id, data) {
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
      result.message || "Failed to update course."
    );
  }

  return result;
}

export async function deleteCourse(id) {
  const response = await fetch(
    `${API_URL}${id}`,
    {
      method: "DELETE",
    }
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.message || "Failed to delete course."
    );
  }

  return result;
}
