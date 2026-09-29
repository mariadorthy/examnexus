from app.models.exam_registration import ExamRegistration
from app.models.examination import Examination
from app.models.timetable import Timetable


def get_eligible_students(examination_id, timetable_id=None):
    examination = Examination.query.get(examination_id)

    if not examination:
        return []

    if timetable_id is not None:
        timetable = Timetable.query.get(timetable_id)

        if not timetable:
            return []

        if timetable.examination_id != examination_id:
            return []

        # if timetable.subject.course_id != examination.course_id:
        #     return []

        # if timetable.subject.semester != examination.semester:
        #     return []

    registrations = ExamRegistration.query.filter_by(
    examination_id=examination_id,
    status="REGISTERED",
    fee_status="PAID"
).all()

    eligible_students = []
    seen_student_ids = set()

    for registration in registrations:
        student = registration.student

        if not student:
            continue

        if not student.is_active:
            continue

        # if student.course_id != examination.course_id:
        #     continue

        # if student.semester != examination.semester:
        #     continue

        if student.id in seen_student_ids:
            continue

        eligible_students.append(student)
        seen_student_ids.add(student.id)

    return eligible_students