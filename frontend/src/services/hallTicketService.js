import {
  get,
  post,
} from "./api";


export async function generateHallTickets(
  examinationId,
  force = false
) {
  return post(
    `/hall-tickets/generate/${examinationId}`,
    { force }
  );
}


export async function getHallTicket(
  examinationId,
  studentId
) {
  return get(
    `/hall-tickets/${examinationId}/${studentId}`
  );
}