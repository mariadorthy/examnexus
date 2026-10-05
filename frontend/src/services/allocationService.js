const API_URL =
  `${import.meta.env.VITE_API_URL || "http://127.0.0.1:5000"}/api/allocations`;

export async function generateAllocation(
  examinationId
) {
  const response = await fetch(
    `${API_URL}/generate/${examinationId}`,
    {
      method: "POST",
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
  const response = await fetch(
    `${API_URL}/${examinationId}`
  );

  if (!response.ok) {
    throw new Error(
      "Failed to load allocations."
    );
  }

  return await response.json();
}

export async function validateAllocation(
  examinationId
) {
  const response = await fetch(
    `${API_URL}/validate/${examinationId}`
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
  const response = await fetch(
    `${API_URL}/summary/${examinationId}`
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
  const response = await fetch(
    `${API_URL}/bulk-generate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
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
        "Failed to generate bulk allocation."
    );
  }

  return result;
}

export async function generateBulkSeatAllocation(
  examinationIds,
  force = false
) {
  const response = await fetch(
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
  const response = await fetch(
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