"""
Post-Phase 7 — Hall ticket PDF download.

Companion to tests/test_post_phase7_hall_ticket.py. Uses the same
conftest fixtures (app_context, examination_id, admin_client).

Strategy:
  - Content assertions (title, student name, DOB-absence, multi-entry)
    run against the pure renderer `build_hall_ticket_pdf` with a
    synthetic payload. No DB writes, no session risk.
  - HTTP assertions (status, content-type, Content-Disposition, PDF
    magic bytes) run against the live /hall-tickets/download/... route.
"""

import io
import base64

import pytest

from app import db
from app.models.examination import Examination
from app.models.seat_allocation import SeatAllocation
from app.models.hall_ticket import HallTicket
from app.models.invigilator_allocation import InvigilatorAllocation

from app.services.hall_ticket import (
    generate_hall_tickets,
    get_hall_ticket,
)
from app.services.lifecycle import transition_status
from app.services.invigilator_allocation import (
    generate_invigilator_allocation,
)
from app.services.allocation import generate_allocation


# ------------------------------------------------------------
# Capability probes
# ------------------------------------------------------------

def _has_pdf_renderer():
    try:
        from app.services.hall_ticket_pdf import build_hall_ticket_pdf  # noqa: F401
        return True
    except ImportError:
        return False


def _has_pdf_service():
    try:
        from app.services.hall_ticket import get_hall_ticket_pdf  # noqa: F401
        return True
    except ImportError:
        return False

def _download_route_registered(app):
    return any(
        "/hall-tickets/download/" in str(r.rule)
        for r in app.url_map.iter_rules()
    )

def _pdf_text(pdf_bytes):
    """Extract text from a PDF using pypdf; return '' if not available."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


# A tiny valid PNG (1x1 transparent) base64-encoded, so the renderer's
# `Image(...)` call succeeds without needing a real QR from the DB.
_TINY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "YAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)


def _synthetic_payload(
    student_name="Aarav Sharma",
    student_id="S001",
    exam_name="End Semester Examination",
    exam_type="Theory",
    entries=None,
):
    """Minimal payload matching _build_ticket_payload's shape."""
    if entries is None:
        entries = [
            {
                "timetable_id": 1,
                "subject_id": 10,
                "subject_name": "Data Structures",
                "subject_code": "CS201",
                "exam_date": "2026-04-12",
                "session": "MORNING",
                "start_time": "09:30",
                "end_time": "12:30",
                "hall_id": 5,
                "hall_name": "Hall A",
                "building_name": "Main Block",
                "floor_no": 2,
                "seat_number": "A-14",
                "row_label": "A",
                "seat_index": 14,
            },
            {
                "timetable_id": 2,
                "subject_id": 11,
                "subject_name": "Algorithms",
                "subject_code": "CS202",
                "exam_date": "2026-04-15",
                "session": "AFTERNOON",
                "start_time": "14:00",
                "end_time": "17:00",
                "hall_id": 5,
                "hall_name": "Hall B",
                "building_name": "Main Block",
                "floor_no": 1,
                "seat_number": "B-07",
                "row_label": "B",
                "seat_index": 7,
            },
        ]
    return {
        "student": {
            "id": 1,
            "student_id": student_id,
            "name": student_name,
            "course_id": 1,
            "batch": "2023-2027",
            "semester": 4,
        },
        "examination": {
            "id": 1,
            "name": exam_name,
            "exam_type": exam_type,
            "course_id": 1,
            "semester": 4,
            "start_date": "2026-04-12",
            "end_date": "2026-04-20",
        },
        "entries": entries,
    }


# ============================================================
# Renderer-level tests (pure function, no DB)
# ============================================================

def test_renderer_produces_valid_pdf_bytes(app_context):
    if not _has_pdf_renderer():
        pytest.skip("build_hall_ticket_pdf not implemented")

    from app.services.hall_ticket_pdf import build_hall_ticket_pdf

    pdf_bytes = build_hall_ticket_pdf(
        _synthetic_payload(),
        _TINY_PNG_B64,
    )

    assert pdf_bytes[:4] == b"%PDF"
    assert len(pdf_bytes) > 500  # not an empty stub


def test_renderer_contains_title_and_student_fields(app_context):
    if not _has_pdf_renderer():
        pytest.skip("build_hall_ticket_pdf not implemented")

    from app.services.hall_ticket_pdf import build_hall_ticket_pdf

    pdf_bytes = build_hall_ticket_pdf(
        _synthetic_payload(
            student_name="Aarav Sharma",
            student_id="S001",
            exam_name="End Semester Examination",
        ),
        _TINY_PNG_B64,
    )
    text = _pdf_text(pdf_bytes)

    if not text:
        pytest.skip("pypdf unavailable or no text layer — cannot assert on content")

    upper = text.upper()
    assert "EXAMINATION HALL TICKET" in upper
    assert "End Semester Examination" in text
    assert "Aarav Sharma" in text
    assert "S001" in text


def test_renderer_does_not_contain_dob_or_email(app_context):
    if not _has_pdf_renderer():
        pytest.skip("build_hall_ticket_pdf not implemented")

    from app.services.hall_ticket_pdf import build_hall_ticket_pdf

    # Give the renderer a payload that also carries DOB/email in
    # unused keys — the renderer must ignore them.
    payload = _synthetic_payload()
    payload["student"]["dob"] = "2005-01-15"
    payload["student"]["email"] = "aarav@example.edu"

    pdf_bytes = build_hall_ticket_pdf(payload, _TINY_PNG_B64)
    text = _pdf_text(pdf_bytes)

    if not text:
        pytest.skip("pypdf unavailable — cannot assert on content")

    lowered = text.lower()
    assert "date of birth" not in lowered
    assert "2005-01-15" not in text
    assert "aarav@example.edu" not in text


def test_renderer_handles_multiple_entries(app_context):
    if not _has_pdf_renderer():
        pytest.skip("build_hall_ticket_pdf not implemented")

    from app.services.hall_ticket_pdf import build_hall_ticket_pdf

    pdf_bytes = build_hall_ticket_pdf(
        _synthetic_payload(),
        _TINY_PNG_B64,
    )
    text = _pdf_text(pdf_bytes)

    if not text:
        pytest.skip("pypdf unavailable — cannot assert on content")

    assert "CS201" in text
    assert "CS202" in text
    assert "A-14" in text
    assert "B-07" in text


def test_renderer_handles_missing_optional_fields(app_context):
    """Empty entries list + missing exam_type must not crash."""
    if not _has_pdf_renderer():
        pytest.skip("build_hall_ticket_pdf not implemented")

    from app.services.hall_ticket_pdf import build_hall_ticket_pdf

    payload = _synthetic_payload(entries=[], exam_type=None)
    pdf_bytes = build_hall_ticket_pdf(payload, _TINY_PNG_B64)
    assert pdf_bytes[:4] == b"%PDF"


def test_renderer_handles_missing_qr(app_context):
    """No QR base64 (None / empty string) must not crash."""
    if not _has_pdf_renderer():
        pytest.skip("build_hall_ticket_pdf not implemented")

    from app.services.hall_ticket_pdf import build_hall_ticket_pdf

    for qr in (None, "", "not-valid-base64!!!"):
        pdf_bytes = build_hall_ticket_pdf(_synthetic_payload(), qr)
        assert pdf_bytes[:4] == b"%PDF"


# ============================================================
# HTTP endpoint tests (via admin_client)
# ============================================================

def _ensure_published(examination_id):
    examination = db.session.get(Examination, examination_id)
    if examination.status == "PUBLISHED":
        return
    order = ["DRAFT", "GENERATED", "VALIDATED",
             "REVIEW", "APPROVED", "PUBLISHED"]
    start = order.index(examination.status)
    for nxt in order[start + 1:]:
        result = transition_status(examination_id, nxt)
        assert result.get("success") is True, result
    db.session.refresh(examination)
    assert examination.status == "PUBLISHED"


def _ensure_invigilators(examination_id):
    existing = InvigilatorAllocation.query.filter_by(
        examination_id=examination_id
    ).count()
    if existing > 0:
        return
    result = generate_invigilator_allocation(examination_id, force=True)
    assert result.get("success") is True, result


def _prepare_state(examination_id):
    generate_allocation(examination_id, force=True)
    _ensure_invigilators(examination_id)
    _ensure_published(examination_id)


def _sample_student_and_ticket(examination_id):
    seat = (
        SeatAllocation.query
        .filter_by(examination_id=examination_id)
        .first()
    )
    if seat is None:
        return None, None
    ticket = (
        HallTicket.query
        .filter_by(examination_id=examination_id,
                   student_id=seat.student_id)
        .first()
    )
    return seat.student_id, ticket


def test_download_endpoint_returns_pdf(
    app_context, examination_id, admin_client
):
    if not _has_pdf_service():
        pytest.skip("get_hall_ticket_pdf not implemented")
    if not _download_route_registered(admin_client.application):
        pytest.skip("/hall-tickets/download/... route not registered")

    _prepare_state(examination_id)
    generate_hall_tickets(examination_id, force=True)

    student_id, _ = _sample_student_and_ticket(examination_id)
    if student_id is None:
        pytest.skip("no allocated student available")

    resp = admin_client.get(
        f"/api/hall-tickets/download/{examination_id}/{student_id}"
    )

    # On failure, produce a readable diagnostic. The body may be a
    # binary PDF, a JSON error, or an HTML error page — decode defensively.
    if resp.status_code != 200:
        try:
            snippet = resp.get_data(as_text=True)[:300]
        except UnicodeDecodeError:
            snippet = repr(resp.data[:300])
        raise AssertionError(
            f"status={resp.status_code} body={snippet!r} "
            f"— check that the /api prefix matches the registered blueprint URL"
        )

    assert resp.headers["Content-Type"].startswith("application/pdf")
    cd = resp.headers.get("Content-Disposition", "")
    assert "attachment" in cd
    assert "ExamNexus_HallTicket_" in cd
    assert ".pdf" in cd
    assert resp.data[:4] == b"%PDF"

    from app.models.student import Student

    student = Student.query.get(student_id)
    if student is not None and student.student_id:
        # The sanitized roll number should be in the filename.
        assert student.student_id.replace(" ", "_") in cd
        
def test_download_rejects_unknown_student(
    app_context, examination_id, admin_client
):
    if not _download_route_registered(admin_client.application):
        pytest.skip("download route not registered")

    resp = admin_client.get(
        f"/api/hall-tickets/download/{examination_id}/999999999"
    )

    assert resp.status_code in (403, 404)


def test_download_requires_auth(
    app_context, examination_id, client
):
    """`client` fixture has no bearer token."""
    if not _download_route_registered(client.application):
        pytest.skip("download route not registered")

    resp = client.get(
        f"/api/hall-tickets/download/{examination_id}/1"
    )
    assert resp.status_code in (401, 403, 404)


def test_verify_unknown_token_is_invalid(app_context):
    from app.services.hall_ticket import verify_hall_ticket

    # Make sure the session is clean before this call, in case an
    # earlier test in the module left it half-flushed.
    db.session.rollback()

    result = verify_hall_ticket("00000000000000000000000000000000")
    assert result.get("valid") is False

def test_verify_scopes_timetable_to_the_ticket_student(
    app_context, examination_id
):
    """
    Regression: verify_hall_ticket must only return the timetable
    entries the ticket's student is registered for — not every
    timetable row in the examination.

    Skips if the seed data registers every student for every
    subject (leak unobservable).
    """
    from app.services.hall_ticket import (
        generate_hall_tickets,
        verify_hall_ticket,
    )

    _prepare_state(examination_id)
    generate_hall_tickets(examination_id, force=True)

    from app.models.timetable import Timetable

    total_tt = Timetable.query.filter_by(
        examination_id=examination_id
    ).count()

    # Find a student whose seat count is strictly less than the
    # total timetable count. If none exists, the seed data makes
    # the assertion vacuous.
    students_with_seats = (
        db.session.query(SeatAllocation.student_id)
        .filter_by(examination_id=examination_id)
        .distinct()
        .all()
    )

    candidate = None
    for (sid,) in students_with_seats:
        own = SeatAllocation.query.filter_by(
            examination_id=examination_id, student_id=sid
        ).count()
        if own < total_tt:
            candidate = sid
            break

    if candidate is None:
        pytest.skip(
            "seed data registers every student for every subject; "
            "leak is unobservable with this dataset"
        )

    ticket = (
        HallTicket.query
        .filter_by(
            examination_id=examination_id,
            student_id=candidate,
            status="ISSUED",
        )
        .first()
    )
    if ticket is None:
        pytest.skip("candidate student has no currently-issued hall ticket")
        
    own_count = SeatAllocation.query.filter_by(
        examination_id=examination_id, student_id=candidate
    ).count()

    result = verify_hall_ticket(ticket.verification_token)
    assert result.get("valid") is True
    assert len(result["timetable"]) == own_count, (
        f"verify returned {len(result['timetable'])} timetable entries; "
        f"expected {own_count} (this student's own seat count)"
    )