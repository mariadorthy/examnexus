import { API_URL, getToken } from "./api";


/**
 * Admin: upload a single student's profile photo.
 *
 * @param {number} studentId  DB primary key of the student
 * @param {File} file         the image file chosen by the admin
 */
export async function uploadStudentProfileImage(studentId, file) {
  const token = getToken();

  const formData = new FormData();
  formData.append("file", file);

  const headers = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  // Do NOT set Content-Type — the browser sets the multipart
  // boundary automatically when the body is FormData.

  const response = await fetch(
    `${API_URL}/api/students/${studentId}/profile-image`,
    {
      method: "POST",
      headers,
      body: formData,
    }
  );

  let data = null;
  try {
    data = await response.json();
  } catch (_) {
    // Non-JSON error body
  }

  if (!response.ok) {
    throw new Error(
      (data && data.message) || "Profile image upload failed."
    );
  }

  return data;
}


/**
 * Admin: bulk-upload a ZIP of profile photos.
 *
 * Each archive entry's basename (without extension) must equal
 * a student's student_id code.
 *
 * @param {File} archiveFile  the .zip the admin selected
 */
export async function bulkUploadProfileImages(archiveFile) {
  const token = getToken();

  const formData = new FormData();
  formData.append("file", archiveFile);

  const headers = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(
    `${API_URL}/api/students/profile-images/bulk`,
    {
      method: "POST",
      headers,
      body: formData,
    }
  );

  let data = null;
  try {
    data = await response.json();
  } catch (_) {
    // Non-JSON error body
  }

  if (!response.ok) {
    throw new Error(
      (data && data.message) || "Bulk image upload failed."
    );
  }

  return data;
}