from app import db

from app.models.student import Student
from app.models.examination import Examination
from app.models.exam_registration import ExamRegistration


def preview_bulk_registration(
    examination_id,
    course_id=None,
    semester=None,
    batch=None,
    active_only=True,
):
    examination = Examination.query.get(examination_id)

    if not examination:
        return {
            "success": False,
            "message": "Examination not found",
        }

    query = Student.query

    if active_only:
        query = query.filter(Student.is_active.is_(True))

    # Examination is the authoritative course/semester.
    target_course_id = examination.course_id
    target_semester = examination.semester

    if course_id is not None and int(course_id) != target_course_id:
        return {
            "success": False,
            "message": "Selected course does not match the examination course",
        }

    if semester is not None and int(semester) != target_semester:
        return {
            "success": False,
            "message": "Selected semester does not match the examination semester",
        }

    query = query.filter(
        Student.course_id == target_course_id,
        Student.semester == target_semester,
    )

    if batch:
        query = query.filter(Student.batch == batch)

    students = query.order_by(Student.id).all()

    student_ids = [student.id for student in students]

    existing_ids = set()

    if student_ids:
        existing_ids = {
            student_id
            for (student_id,) in db.session.query(
                ExamRegistration.student_id
            )
            .filter(
                ExamRegistration.examination_id == examination_id,
                ExamRegistration.student_id.in_(student_ids),
            )
            .all()
        }

    new_students = [
        student
        for student in students
        if student.id not in existing_ids
    ]

    return {
        "success": True,
        "examination_id": examination.id,
        "examination_name": examination.name,
        "course_id": target_course_id,
        "semester": target_semester,
        "total_matching_students": len(students),
        "already_registered": len(existing_ids),
        "new_registrations": len(new_students),
        "students": [
            {
                "id": student.id,
                "student_id": student.student_id,
                "name": student.name,
                "email": student.email,
                "batch": student.batch,
            }
            for student in new_students
        ],
    }


def create_bulk_registrations(
    examination_id,
    course_id=None,
    semester=None,
    batch=None,
    active_only=True,
):
    preview = preview_bulk_registration(
        examination_id=examination_id,
        course_id=course_id,
        semester=semester,
        batch=batch,
        active_only=active_only,
    )

    if not preview["success"]:
        return preview

    student_ids = [
        student["id"]
        for student in preview["students"]
    ]

    if not student_ids:
        return {
            **preview,
            "message": "No new students require registration",
            "created": 0,
        }

    registrations = [
        ExamRegistration(
            student_id=student_id,
            examination_id=examination_id,
            status="REGISTERED",
            fee_status="PENDING",
        )
        for student_id in student_ids
    ]

    try:
        db.session.add_all(registrations)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return {
        **preview,
        "message": "Bulk examination registrations created successfully",
        "created": len(registrations),
    }