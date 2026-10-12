const API_URL = `${import.meta.env.VITE_API_BASE_URL}/api/halls`;

function authHeaders() {
  const token = localStorage.getItem("examnexus_token");
  const headers = { "Content-Type": "application/json" };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

async function parse(response) {
  let data = null;
  try {
    data = await response.json();
  } catch (_) {
    // non-JSON error body
  }
  if (!response.ok) {
    throw new Error(
      (data && data.message) || "Hall incident request failed."
    );
  }
  return data;
}

export async function reportHallIncident(
  hallId,
  { category, description, scope, examinationId }
) {
  const response = await fetch(
    `${API_URL}/${hallId}/incidents`,
    {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        category,
        description,
        scope,
        examination_id: examinationId ?? null,
      }),
    }
  );
  return parse(response);
}

export async function resolveHallIncident(incidentId, notes) {
  const response = await fetch(
    `${API_URL}/incidents/${incidentId}/resolve`,
    {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ resolution_notes: notes ?? null }),
    }
  );
  return parse(response);
}
export async function listHallIncidents({
  status,
  hallId,
  examinationId,
} = {}) {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  if (hallId) params.set("hall_id", hallId);
  if (examinationId) {
    params.set("examination_id", examinationId);
  }

  const query = params.toString();
  const url = query
    ? `${API_URL}/incidents?${query}`
    : `${API_URL}/incidents`;

  const response = await fetch(url, {
    method: "GET",
    headers: authHeaders(),
  });
  return parse(response);
}