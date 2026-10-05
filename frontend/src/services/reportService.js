import { get } from "./api";


export async function getAllocationReport(
  examinationId
) {
  return get(
    `/reports/allocation/${examinationId}`
  );
}


export async function getStudentAllocationReport(
  examinationId
) {
  return get(
    `/reports/students/${examinationId}`
  );
}


export async function getHallUtilizationReport(
  examinationId
) {
  return get(
    `/reports/halls/${examinationId}`
  );
}


export async function getInvigilatorReport(
  examinationId
) {
  return get(
    `/reports/invigilators/${examinationId}`
  );
}