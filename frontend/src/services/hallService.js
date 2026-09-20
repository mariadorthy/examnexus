const API_URL =
  `${import.meta.env.VITE_API_URL || "http://127.0.0.1:5000"}/api/halls/`;

export async function getHalls() {
  const response = await fetch(API_URL);

  if (!response.ok) {
    throw new Error("Failed to load halls.");
  }

  return await response.json();
}

export async function createHall(data) {
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
      result.message || "Failed to create hall."
    );
  }

  return result;
}

export async function updateHall(id, data) {
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
      result.message || "Failed to update hall."
    );
  }

  return result;
}

export async function deleteHall(id) {
  const response = await fetch(
    `${API_URL}${id}`,
    {
      method: "DELETE",
    }
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.message || "Failed to delete hall."
    );
  }

  return result;
}
