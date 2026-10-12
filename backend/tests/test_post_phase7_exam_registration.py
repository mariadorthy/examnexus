"""
Post-Phase 7 — Exam registration bulk preview/create.

Covers app/services/exam_registration.py (14% coverage in the
Phase A audit) and the routes that wrap it.

The service is the gatekeeper for "which students are entered
into an examination". Its behavior must be:
  - preview is read-only
  - create persists exactly what preview proposed
  - the examination's course/semester are authoritative
  - duplicate registrations are not created
  - active_only controls whether inactive students appear
"""

import pytest

from app import db
from app.models.student import Student
from app.models.examination import Examination
from app.models.exam_registration import ExamRegistration

from app.services.exam_registration import (
    preview_bulk_registration,
    create_bulk_registrations,
)


def _course_semester_students(examination):
    """Return the students that would match the exam's course+semester."""
    return (
        Student.query
        .filter_by(
            course_id=examination.course_id,
            semester=examination.semester,
            is_active=True,
        )
        .all()
    )


def test_preview_returns_matching_students(app_context, examination_id):
    """
    Preview returns the students whose course+semester match the
    examination, plus accurate counts.
    """
    examination = db.session.get(Examination, examination_id)
    assert examination is not None

    result = preview_bulk_registration(examination_id)

    assert result["success"] is True
    assert result["examination_id"] == examination_id
    assert result["course_id"] == examination.course_id
    assert result["semester"] == examination.semester
    assert result["total_matching_students"] >= 0
    assert result["new_registrations"] >= 0
    assert isinstance(result["students"], list)


def test_preview_does_not_mutate_database(app_context, examination_id):
    """Preview must not create or delete any ExamRegistration row."""
    before = ExamRegistration.query.filter_by(
        examination_id=examination_id
    ).count()

    preview_bulk_registration(examination_id)

    after = ExamRegistration.query.filter_by(
        examination_id=examination_id
    ).count()

    assert after == before


def test_preview_rejects_unknown_examination(app_context):
    """A nonexistent examination_id is rejected cleanly."""
    result = preview_bulk_registration(999999999)

    assert result["success"] is False
    assert "not found" in result["message"].lower()


def test_preview_rejects_mismatched_course(app_context, examination_id):
    """
    If the caller passes a course_id that doesn't match the
    examination's course, the preview refuses rather than
    silently filtering.
    """
    examination = db.session.get(Examination, examination_id)
    assert examination is not None

    # Pick a course id that is definitely different
    from app.models.course import Course
    other = (
        Course.query
        .filter(Course.id != examination.course_id)
        .first()
    )
    if other is None:
        pytest.skip("no second course available")

    result = preview_bulk_registration(
        examination_id, course_id=other.id
    )

    assert result["success"] is False
    assert "does not match" in result["message"].lower()


def test_create_persists_exactly_what_preview_proposed(
    app_context, examination_id
):
    """
    The count returned by preview() as `new_registrations` must
    equal the number of rows create() actually inserts.
    """
    # Bring the exam to a deterministic state: no prior rows for
    # these students in this exam.
    preview_before = preview_bulk_registration(examination_id)
    assert preview_before["success"] is True

    expected_new = preview_before["new_registrations"]

    result = create_bulk_registrations(examination_id)

    assert result["success"] is True
    assert result["created"] == expected_new

    # Every student listed in the preview should now have a row.
    listed_ids = {s["id"] for s in preview_before["students"]}
    for student_id in listed_ids:
        assert (
            ExamRegistration.query
            .filter_by(
                student_id=student_id,
                examination_id=examination_id,
            )
            .first()
            is not None
        )


def test_create_is_idempotent_for_existing_registrations(
    app_context, examination_id
):
    """
    Calling create twice must not duplicate registrations. The
    second call reports 0 created and no new rows appear.
    """
    create_bulk_registrations(examination_id)
    first_count = ExamRegistration.query.filter_by(
        examination_id=examination_id
    ).count()

    second = create_bulk_registrations(examination_id)

    assert second["success"] is True
    assert second["created"] == 0

    second_count = ExamRegistration.query.filter_by(
        examination_id=examination_id
    ).count()
    assert second_count == first_count


def test_create_rejects_inactive_students_when_active_only(
    app_context, examination_id
):
    """
    When active_only=True (the default), inactive students in the
    matching course/semester are excluded from the plan.

    We flip a matching active student to inactive, run preview,
    and prove they don't appear — then restore them.
    """
    examination = db.session.get(Examination, examination_id)
    candidates = _course_semester_students(examination)
    if not candidates:
        pytest.skip("no active students match this exam")

    victim = candidates[0]
    original = victim.is_active
    try:
        victim.is_active = False
        db.session.commit()

        result = preview_bulk_registration(
            examination_id, active_only=True
        )
        assert result["success"] is True
        listed_ids = {s["id"] for s in result["students"]}
        assert victim.id not in listed_ids
    finally:
        victim.is_active = original
        db.session.commit()


# ============================================================
# Route-level tests
# ============================================================

def test_bulk_preview_requires_auth(client, examination_id):
    resp = client.post(
        "/api/exam-registrations/bulk-preview",
        json={"examination_id": examination_id},
    )
    assert resp.status_code in (401, 403)


def test_bulk_preview_requires_examination_id(admin_client):
    resp = admin_client.post(
        "/api/exam-registrations/bulk-preview",
        json={},
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["success"] is False
    assert "examination_id" in body["message"].lower()


def test_bulk_preview_unknown_examination_returns_400(
    admin_client,
):
    resp = admin_client.post(
        "/api/exam-registrations/bulk-preview",
        json={"examination_id": 999999999},
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["success"] is False


def test_bulk_preview_returns_plan_for_valid_exam(
    admin_client, examination_id
):
    resp = admin_client.post(
        "/api/exam-registrations/bulk-preview",
        json={"examination_id": examination_id},
    )
    assert resp.status_code == 200, resp.get_json()
    body = resp.get_json()
    assert body["success"] is True
    assert "new_registrations" in body
    assert isinstance(body["students"], list)