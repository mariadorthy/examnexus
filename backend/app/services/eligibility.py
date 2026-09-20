from app.models.exam_registration import ExamRegistration


def get_eligible_students(examination_id):
    registrations = ExamRegistration.query.filter_by(
        examination_id=examination_id,
        status="REGISTERED"
    ).all()

    eligible_students = []

    for registration in registrations:
        student = registration.student

        if student and student.is_active:
            eligible_students.append(student)

    return eligible_students