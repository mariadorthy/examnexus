export const API_URL =
  import.meta.env.VITE_API_BASE_URL;

  export function getToken() {
  return localStorage.getItem(
    "examnexus_token"
  );
}

const REQUEST_TIMEOUT_MS = 20000;

async function fetchWithTimeout(url, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(
    () => controller.abort(),
    REQUEST_TIMEOUT_MS
  );

  try {
    return await fetch(url, {
      ...options,
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timer);
  }
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

      // Tell App.jsx to drop the in-memory user without
      // a full page reload (DEF-05 / DEF-10).
      window.dispatchEvent(
        new Event("examnexus:unauthorized")
      );
    }
    
    const error = new Error(
      data.message || "Request failed"
    );

    // Preserve structured backend error bodies so callers
    // can show actual validation reasons, not just the
    // summary message. Backwards-compatible: err.message
    // is unchanged for all existing callers.
    error.status = response.status;
    error.errors = Array.isArray(data?.errors)
      ? data.errors
      : [];
    error.response = data;

    throw error;
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

    const response = await fetchWithTimeout(
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

    const response = await fetchWithTimeout(
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

   const response = await fetchWithTimeout(
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

    const response = await fetchWithTimeout(
    `${API_URL}/api${endpoint}`,
    {
      method: "PATCH",
      headers,
      body: JSON.stringify(data),
    }
  );

  return parseResponse(response);
}

export async function del(endpoint) {
  const token = getToken();
  const headers = {};

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetchWithTimeout(
    `${API_URL}/api${endpoint}`,
    {
      method: "DELETE",
      headers,
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
