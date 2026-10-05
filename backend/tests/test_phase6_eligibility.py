"""
Phase 6 — Eligibility + resource readiness.
"""

from app.models.exam_registration import ExamRegistration
from app.models.hall import Hall

from app.services.eligibility import get_eligible_students


def _registrations(examination_id):
    return ExamRegistration.query.filter_by(
        examination_id=examination_id
    ).all()


def test_examination_registrations_exist(
    app_context, examination_id
):
    assert len(_registrations(examination_id)) > 0


def test_eligible_students_found(app_context, examination_id):
    students = get_eligible_students(examination_id)
    assert len(students) > 0


def test_eligible_students_have_no_duplicates(
    app_context, examination_id
):
    ids = [
        s.id
        for s in get_eligible_students(examination_id)
    ]
    assert len(ids) == len(set(ids))


def test_all_eligible_students_active(
    app_context, examination_id
):
    for student in get_eligible_students(examination_id):
        assert student.is_active


def test_eligible_students_have_registered_status(
    app_context, examination_id
):
    students = get_eligible_students(examination_id)
    eligible_ids = {s.id for s in students}

    registered_ids = {
        r.student_id
        for r in _registrations(examination_id)
        if r.status == "REGISTERED"
    }

    assert eligible_ids.issubset(registered_ids)


def test_usable_halls_available(app_context):
    halls = Hall.query.filter_by(
        is_active=True,
        is_available=True,
        is_under_maintenance=False,
    ).all()
    assert len(halls) > 0


def test_resource_capacity_is_sufficient(
    app_context, examination_id
):
    from app.models.timetable import Timetable

    students = get_eligible_students(examination_id)
    timetables = Timetable.query.filter_by(
        examination_id=examination_id
    ).all()

    halls = Hall.query.filter_by(
        is_active=True,
        is_available=True,
        is_under_maintenance=False,
    ).all()

    usable_capacity = sum(
        h.examination_capacity or 0 for h in halls
    )
    required_capacity = len(students) * len(timetables)

    assert usable_capacity >= required_capacity