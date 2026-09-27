import {
  get,
  post,
  put,
} from "./api";


export async function getExaminations() {
  return await get(
    "/examinations/"
  );
}


export async function getExamination(id) {
  return await get(
    `/examinations/${id}`
  );
}


export async function createExamination(data) {
  return await post(
    "/examinations/",
    data
  );
}


export async function updateExamination(
  id,
  data
) {
  return await put(
    `/examinations/${id}`,
    data
  );
}