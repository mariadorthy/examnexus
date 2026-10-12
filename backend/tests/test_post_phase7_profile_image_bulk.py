"""
Post-Phase 7 — Profile image uploads (admin single + bulk).

Covers:
  - admin single-image upload for one student
  - admin bulk-ZIP upload with mixed valid/invalid entries
  - validation rules (MIME, size, unknown student)
  - authorization (student token cannot upload)
  - privacy: the public verify endpoint does not return a photo
"""

import io
import zipfile

import pytest

from app import db
from app.models.student import Student


# ---------- helpers ----------

# Valid 1x1 PNG magic bytes + filler — enough to pass the
# magic-byte sniff in profile_image.detect_image_mimetype.
_PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452"
) + b"\x00" * 128


def _student_client(app, student):
    """Client that authenticates as the given student."""
    from app.auth.security import create_access_token
    token = create_access_token(student.id, "student")
    c = app.test_client()
    original_open = c.open

    def with_auth(*args, **kwargs):
        headers = kwargs.pop("headers", {}) or {}
        headers.setdefault(
            "Authorization", f"Bearer {token}"
        )
        kwargs["headers"] = headers
        return original_open(*args, **kwargs)

    c.open = with_auth
    return c


def _any_active_student():
    return (
        Student.query
        .filter(Student.is_active.is_(True))
        .first()
    )


def _post_single(admin_client, student_pk, filename, content):
    return admin_client.post(
        f"/api/students/{student_pk}/profile-image",
        data={"file": (io.BytesIO(content), filename)},
        content_type="multipart/form-data",
    )


def _post_bulk(admin_client, zip_bytes, filename="photos.zip"):
    return admin_client.post(
        "/api/students/profile-images/bulk",
        data={"file": (io.BytesIO(zip_bytes), filename)},
        content_type="multipart/form-data",
    )


def _build_zip(entries):
    """entries: list of (name, bytes)"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in entries:
            zf.writestr(name, data)
    return buf.getvalue()


# ---------- single upload ----------

def test_single_upload_happy_path(
    app_context, admin_client
):
    student = _any_active_student()
    if student is None:
        pytest.skip("no active student")

    original = student.student_img
    try:
        resp = _post_single(
            admin_client, student.id,
            "photo.png", _PNG_BYTES,
        )
        assert resp.status_code == 200, resp.get_data(as_text=True)[:300]
        body = resp.get_json()
        assert body["success"] is True
        assert body["profile_image"].startswith(
            "/static/profile_images/"
        )
        db.session.refresh(student)
        assert student.student_img == body["profile_image"]
    finally:
        student.student_img = original
        db.session.commit()


def test_single_upload_rejects_non_image(
    app_context, admin_client
):
    student = _any_active_student()
    if student is None:
        pytest.skip("no active student")

    resp = _post_single(
        admin_client, student.id,
        "malicious.png", b"not really a png",
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["success"] is False


def test_single_upload_rejects_oversize(
    app_context, admin_client
):
    student = _any_active_student()
    if student is None:
        pytest.skip("no active student")

    oversize = _PNG_BYTES + b"\x00" * (3 * 1024 * 1024)
    resp = _post_single(
        admin_client, student.id,
        "big.png", oversize,
    )
    assert resp.status_code == 400
    assert "too large" in resp.get_json()["message"].lower()


def test_single_upload_unknown_student_404(
    app_context, admin_client
):
    resp = _post_single(
        admin_client, 999999999,
        "photo.png", _PNG_BYTES,
    )
    assert resp.status_code == 404


def test_single_upload_student_token_forbidden(
    app, app_context
):
    """A student JWT cannot hit the admin upload route."""
    student = _any_active_student()
    if student is None:
        pytest.skip("no active student")

    c = _student_client(app, student)
    resp = c.post(
        f"/api/students/{student.id}/profile-image",
        data={"file": (io.BytesIO(_PNG_BYTES), "photo.png")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 403


# ---------- bulk upload ----------

def test_bulk_upload_happy_path(
    app_context, admin_client
):
    student = _any_active_student()
    if student is None:
        pytest.skip("no active student")

    original = student.student_img
    try:
        z = _build_zip([
            (f"{student.student_id}.png", _PNG_BYTES),
        ])
        resp = _post_bulk(admin_client, z)
        assert resp.status_code == 200, resp.get_data(as_text=True)[:300]
        body = resp.get_json()
        assert body["success"] is True
        assert body["matched"] == 1
        assert body["saved"] == 1
        assert body["skipped"] == []

        db.session.refresh(student)
        assert student.student_img is not None
    finally:
        student.student_img = original
        db.session.commit()


def test_bulk_upload_skips_unknown_students(
    app_context, admin_client
):
    student = _any_active_student()
    if student is None:
        pytest.skip("no active student")

    z = _build_zip([
        ("NO_SUCH_STUDENT_XYZ.png", _PNG_BYTES),
    ])
    resp = _post_bulk(admin_client, z)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["saved"] == 0
    assert len(body["skipped"]) == 1
    assert "no student" in body["skipped"][0]["reason"].lower()


def test_bulk_upload_skips_wrong_mime(
    app_context, admin_client
):
    student = _any_active_student()
    if student is None:
        pytest.skip("no active student")

    z = _build_zip([
        (f"{student.student_id}.png", b"not an image"),
    ])
    resp = _post_bulk(admin_client, z)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["saved"] == 0
    assert len(body["skipped"]) == 1


def test_bulk_upload_rejects_non_zip(
    app_context, admin_client
):
    resp = _post_bulk(
        admin_client, b"this is not a zip archive",
    )
    assert resp.status_code == 400
    assert "not a valid" in resp.get_json()["message"].lower()


def test_bulk_upload_requires_admin(
    client, app_context
):
    z = _build_zip([("X.png", _PNG_BYTES)])
    resp = client.post(
        "/api/students/profile-images/bulk",
        data={"file": (io.BytesIO(z), "photos.zip")},
        content_type="multipart/form-data",
    )
    assert resp.status_code in (401, 403)


# ---------- privacy: verify endpoint must not leak photos ----------

def test_verify_endpoint_does_not_return_profile_image(
    app_context, examination_id
):
    """
    The public verification endpoint must not expose the
    student's photo. This is a privacy requirement even if a
    photo exists.
    """
    from app.models.hall_ticket import HallTicket
    from app.services.hall_ticket import verify_hall_ticket

    # Use the currently ISSUED ticket for this examination so a
    # leftover SUPERSEDED row from an earlier test run does not
    # poison the assertion.
    ticket = (
        HallTicket.query
        .filter_by(
            examination_id=examination_id,
            status="ISSUED",
        )
        .first()
    )
    if ticket is None:
        pytest.skip("no currently-issued hall ticket in DB")

    result = verify_hall_ticket(ticket.verification_token)
    assert result.get("valid") is True
    assert "profile_image" not in result, (
        "verify_hall_ticket must NOT return profile_image"
    )
    assert "student_img" not in result