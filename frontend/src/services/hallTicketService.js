import { get, post } from "./api";

const API_URL = import.meta.env.VITE_API_BASE_URL;

function getToken() {
  return localStorage.getItem("examnexus_token");
}


export async function generateHallTickets(examinationId, force = false) {
  return post(
    `/hall-tickets/generate/${examinationId}`,
    { force }
  );
}


export async function getHallTicket(examinationId, studentId) {
  return get(
    `/hall-tickets/${examinationId}/${studentId}`
  );
}


/**
 * Download a hall-ticket PDF and trigger a browser download.
 *
 * Uses a raw fetch (not the get() helper) because we want a
 * binary blob, not JSON. But it reuses the same base URL and the
 * same localStorage token key as api.js, so there is exactly one
 * place that defines each.
 */
export async function downloadHallTicket(examinationId, studentId) {
  const token = getToken();

  const headers = {};

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(
    `${API_URL}/api/hall-tickets/download/${examinationId}/${studentId}`,
    { method: "GET", headers }
  );

  if (!response.ok) {
    // Non-PDF error body → try to surface the server message.
    let message = "Failed to download hall ticket";
    try {
      const data = await response.json();
      if (data && data.message) message = data.message;
    } catch (_) {
      // not JSON; keep the default message
    }
    throw new Error(message);
  }

  // Prefer the server-provided filename so per-student names
  // (roll number, exam) are preserved. Fall back to a generic
  // name if the header is missing or malformed.
  const disposition = response.headers.get("Content-Disposition") || "";
  let filename = "ExamNexus_Hall_Ticket.pdf";
  const match = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(disposition);
  if (match && match[1]) {
    filename = match[1].trim();
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}