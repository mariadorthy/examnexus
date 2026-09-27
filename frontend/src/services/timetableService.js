import {
  get,
  post,
  put,
} from "./api";


export async function getTimetable(
  examinationId
) {
  return await get(
    `/timetable/${examinationId}`
  );
}


export async function generateTimetable(
  examinationId,
  data
) {
  return await post(
    `/timetable/${examinationId}/generate`,
    data
  );
}

export async function updateTimetableEntry(
  timetableId,
  data
) {
  return await put(
    `/timetable/${timetableId}`,
    data
  );
}