"""
Phase 2 — Master data presence and uniqueness.
"""

from app.models.department import Department
from app.models.course import Course
from app.models.subject import Subject
from app.models.student import Student
from app.models.staff import Staff
from app.models.hall import Hall


def test_departments_master_data_exists(app_context):
    assert Department.query.count() > 0


def test_courses_master_data_exists(app_context):
    assert Course.query.count() > 0


def test_subjects_master_data_exists(app_context):
    assert Subject.query.count() > 0


def test_students_master_data_exists(app_context):
    assert Student.query.count() > 0


def test_staff_master_data_exists(app_context):
    assert Staff.query.count() > 0


def test_halls_master_data_exists(app_context):
    assert Hall.query.count() > 0


def test_student_ids_are_unique(app_context):
    student_ids = [
        student.student_id
        for student in Student.query.all()
        if student.student_id
    ]

    assert len(student_ids) == len(set(student_ids))


def test_student_emails_are_unique(app_context):
    emails = [
        student.email.lower()
        for student in Student.query.all()
        if student.email
    ]

    assert len(emails) == len(set(emails))


def test_hall_names_are_unique(app_context):
    names = [
        hall.name
        for hall in Hall.query.all()
        if hall.name
    ]

    assert len(names) == len(set(names))