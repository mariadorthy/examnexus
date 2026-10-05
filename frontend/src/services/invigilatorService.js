import {
  get,
  post,
} from "./api";


export async function generateInvigilators(
  examinationId,
  force = false
) {
  return post(
    `/allocations/invigilators/generate/${examinationId}`,
    { force }
  );
}


export async function getInvigilators(
  examinationId
) {
  return get(
    `/allocations/invigilators/${examinationId}`
  );
}


export async function validateInvigilators(
  examinationId
) {
  return get(
    `/allocations/invigilators/validate/${examinationId}`
  );
}


export async function getInvigilatorWorkload(
  examinationId
) {
  return get(
    `/allocations/invigilators/workload/${examinationId}`
  );
}

export async function generateBulkInvigilators(
  examinationIds,
  force = false
) {
  return post(
    "/allocations/invigilators/bulk-generate",
    {
      examination_ids: examinationIds,
      force,
    }
  );
}