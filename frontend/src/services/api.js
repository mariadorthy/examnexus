const API_URL =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:5000";


function getToken() {
  return localStorage.getItem(
    "examnexus_token"
  );
}


async function parseResponse(response) {
  const data = await response.json();

  if (!response.ok) {

    if (response.status === 401) {
      localStorage.removeItem(
        "examnexus_token"
      );

      localStorage.removeItem(
        "examnexus_user"
      );
    }

    throw new Error(
      data.message || "Request failed"
    );
  }

  return data;
}


export async function get(endpoint) {

  const token = getToken();

  const headers = {};

  if (token) {
    headers.Authorization =
      `Bearer ${token}`;
  }

  const response = await fetch(
    `${API_URL}/api${endpoint}`,
    {
      method: "GET",
      headers,
    }
  );

  return parseResponse(response);
}


export async function post(
  endpoint,
  data
) {

  const token = getToken();

  const headers = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers.Authorization =
      `Bearer ${token}`;
  }

  const response = await fetch(
    `${API_URL}/api${endpoint}`,
    {
      method: "POST",
      headers,
      body: JSON.stringify(data),
    }
  );

  return parseResponse(response);
}

export async function put(
  endpoint,
  data
) {
  const token = getToken();

  const headers = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers.Authorization =
      `Bearer ${token}`;
  }

  const response = await fetch(
    `${API_URL}/api${endpoint}`,
    {
      method: "PUT",
      headers,
      body: JSON.stringify(data),
    }
  );

  return parseResponse(response);
}


export async function patch(
  endpoint,
  data
) {
  const token = getToken();

  const headers = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers.Authorization =
      `Bearer ${token}`;
  }

  const response = await fetch(
    `${API_URL}/api${endpoint}`,
    {
      method: "PATCH",
      headers,
      body: JSON.stringify(data),
    }
  );

  return parseResponse(response);
}
export async function uploadCsv(endpoint, file) {
  const token = getToken();

  const formData = new FormData();
  formData.append("file", file);

  const headers = {};

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(
    `${API_URL}/api${endpoint}`,
    {
      method: "POST",
      headers,
      body: formData,
    }
  );

  return parseResponse(response);
}

export async function validateCsv(entity, file) {
  return uploadCsv(
    `/import/${entity}/validate`,
    file
  );
}

export async function importCsv(entity, file) {
  return uploadCsv(
    `/import/${entity}/import`,
    file
  );
}