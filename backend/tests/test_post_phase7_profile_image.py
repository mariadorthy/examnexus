"""
Post-Phase 7 — Student profile image (display contract).

Covers the field-name alias between Student.student_img (DB column)
and the `profile_image` key the frontend reads.

Upload endpoint tests come in a later batch (E7).
"""

import pytest

from app import db
from app.models.student import Student


def _student_client(app, student):
    """
    Build a test client that sends a real student JWT.

    Uses the same encoder the app uses, so the token is
    indistinguishable from a login-issued token.
    """
    from app.auth.security import create_access_token
    token = create_access_token(student.id, "student")
    client = app.test_client()
    original_open = client.open

    def open_with_auth(*args, **kwargs):
        headers = kwargs.pop("headers", {}) or {}
        headers.setdefault("Authorization", f"Bearer {token}")
        kwargs["headers"] = headers
        return original_open(*args, **kwargs)

    client.open = open_with_auth
    return client


def _any_active_student():
    return (
        Student.query
        .filter(Student.is_active.is_(True))
        .first()
    )


def test_dashboard_exposes_profile_image_key(app, app_context):
    """
    GET /api/dashboard/student must include `profile_image` in
    the user block, not the raw column name `student_img`.
    """
    student = _any_active_student()
    if student is None:
        pytest.skip("no active student in seed data")

    client = _student_client(app, student)
    resp = client.get("/api/dashboard/student")
    assert resp.status_code == 200, resp.get_data(as_text=True)[:300]

    body = resp.get_json()
    assert body["success"] is True
    assert "user" in body
    user = body["user"]
    assert "profile_image" in user, (
        "dashboard user block must expose `profile_image`"
    )
    assert "student_img" not in user, (
        "dashboard must NOT leak the raw column name `student_img`"
    )


def test_dashboard_profile_image_is_none_when_unset(app, app_context):
    """
    A student with no photo returns `profile_image: null`, so the
    frontend can cleanly fall back to initials.
    """
    student = _any_active_student()
    if student is None:
        pytest.skip("no active student in seed data")

    original = student.student_img
    try:
        student.student_img = None
        db.session.commit()

        client = _student_client(app, student)
        body = client.get("/api/dashboard/student").get_json()
        assert body["user"]["profile_image"] is None
    finally:
        student.student_img = original
        db.session.commit()


def test_dashboard_profile_image_returns_stored_url(app, app_context):
    """
    A student with a stored photo URL returns that exact URL.
    """
    student = _any_active_student()
    if student is None:
        pytest.skip("no active student in seed data")

    original = student.student_img
    try:
        student.student_img = "/static/profile_images/test-fixture.png"
        db.session.commit()

        client = _student_client(app, student)
        body = client.get("/api/dashboard/student").get_json()
        assert (
            body["user"]["profile_image"]
            == "/static/profile_images/test-fixture.png"
        )
    finally:
        student.student_img = original
        db.session.commit()