  const API_URL =
  `${import.meta.env.VITE_API_BASE_URL}/api/allocations`;

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

  export async function generateAllocation(
  examinationId
) {
  const token = localStorage.getItem("examnexus_token");
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;

 const response = await fetchWithTimeout(
    `${API_URL}/generate/${examinationId}`,
    {
      method: "POST",
      headers,
    }
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.message ||
        "Failed to generate allocation."
    );
  }

  return result;
}

export async function getAllocations(
  examinationId
) {
  const token = localStorage.getItem(
    "examnexus_token"
  );

  const headers = {};

  if (token) {
    headers.Authorization =
      `Bearer ${token}`;
  }

  const response = await fetchWithTimeout(
    `${API_URL}/${examinationId}`,
    {
      method: "GET",
      headers,
    }
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.message ||
        "Failed to load allocations."
    );
  }

  return result;
}

export async function validateAllocation(
  examinationId
) {
  const token = localStorage.getItem("examnexus_token");
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetchWithTimeout(
    `${API_URL}/validate/${examinationId}`,
    { headers }
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.message ||
        "Allocation validation failed."
    );
  }

  return result;
}

export async function getAllocationSummary(
  examinationId
) {
  const token = localStorage.getItem("examnexus_token");
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetchWithTimeout(
    `${API_URL}/summary/${examinationId}`,
    { headers }
  );

  if (!response.ok) {
    throw new Error(
      "Failed to load allocation summary."
    );
  }

  return await response.json();
}
export async function generateBulkAllocation(
  examinationIds
) {
  const token = localStorage.getItem("examnexus_token");
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetchWithTimeout(
    `${API_URL}/bulk-generate`,
    {
      method: "POST",
      headers,
      body: JSON.stringify({
        examination_ids: examinationIds,
      }),
    }
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.message ||
        "Failed to generate bulk allocation."
    );
  }

  return result;
}

export async function generateBulkSeatAllocation(
  examinationIds,
  force = false
) {
 const response = await fetchWithTimeout(
    `${API_URL}/seats/bulk-generate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem(
          "examnexus_token"
        )}`,
      },
      body: JSON.stringify({
        examination_ids: examinationIds,
        force,
      }),
    }
  );

  const result = await response.json();

  if (!response.ok && !result.results) {
    throw new Error(
      result.message ||
        "Failed to generate bulk seat allocation."
    );
  }

  return result;
}


export async function bulkValidateExaminations(
  examinationIds
) {
const response = await fetchWithTimeout(
    `${API_URL}/validate/bulk`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem(
          "examnexus_token"
        )}`,
      },
      body: JSON.stringify({
        examination_ids: examinationIds,
      }),
    }
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.message ||
        "Failed to bulk validate examinations."
    );
  }

  return result;
}
// =========================================================
// FEATURE 21 — DYNAMIC REALLOCATION / WHAT-IF
// =========================================================

export async function simulateReallocation(
  examinationId,
  excludedHallIds
) {
  const response = await fetchWithTimeout(
    `${API_URL}/reallocate/what-if/${examinationId}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem(
          "examnexus_token"
        )}`,
      },
      body: JSON.stringify({
        excluded_hall_ids: excludedHallIds,
      }),
    }
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.message ||
        "Failed to simulate reallocation."
    );
  }

  return result;
}

export async function applyReallocation(
  examinationId,
  excludedHallIds
) {
  const response = await fetchWithTimeout(
    `${API_URL}/reallocate/apply/${examinationId}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem(
          "examnexus_token"
        )}`,
      },
      body: JSON.stringify({
        excluded_hall_ids: excludedHallIds,
        confirm: true,
      }),
    }
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.message ||
        "Failed to apply reallocation."
    );
  }

  return result;
}

export const getExplanation = async (examinationId) => {
  const token = localStorage.getItem("examnexus_token");

  const headers = {};

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

const response = await fetchWithTimeout(
    `${API_URL}/explain/${examinationId}`,
    {
      method: "GET",
      headers,
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data?.message ||
        "Failed to fetch allocation explanation"
    );
  }

  return data;
};

export const getHallExplanation = async (
  examinationId,
  hallId,
  timetableId
) => {
  const token = localStorage.getItem("examnexus_token");

  const headers = {};

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

const response = await fetchWithTimeout(
    `${API_URL}/explain/${examinationId}/hall/${hallId}?timetable_id=${timetableId}`,
    {
      method: "GET",
      headers,
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data?.message ||
        "Failed to fetch hall explanation"
    );
  }

  return data;
};

// =========================================================
// EMERGENCY REALLOCATION (PUBLISHED EXAMINATIONS)
// =========================================================

export async function simulateEmergencyReallocation(
  examinationId,
  incidentId,
  excludedHallIds
) {
 const response = await fetchWithTimeout(
    `${API_URL}/reallocate/emergency/what-if/${examinationId}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem(
          "examnexus_token"
        )}`,
      },
      body: JSON.stringify({
        incident_id: incidentId,
        excluded_hall_ids: excludedHallIds,
      }),
    }
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.message ||
        "Failed to simulate emergency reallocation."
    );
  }

  return result;
}

export async function applyEmergencyReallocation(
  examinationId,
  incidentId,
  excludedHallIds,
  acknowledgeInProgress = false
) {
 const response = await fetchWithTimeout(
    `${API_URL}/reallocate/emergency/apply/${examinationId}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem(
          "examnexus_token"
        )}`,
      },
      body: JSON.stringify({
        incident_id: incidentId,
        excluded_hall_ids: excludedHallIds,
        confirm: true,
        acknowledge_in_progress: acknowledgeInProgress,
      }),
    }
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.message ||
        "Failed to apply emergency reallocation."
    );
  }

  return result;
}