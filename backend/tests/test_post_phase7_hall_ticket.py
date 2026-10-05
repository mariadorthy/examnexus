"""
Post-Phase 7 — Hall ticket + QR generation and safety.
"""

import base64 as b64
import pytest
import json as jsonlib

from app import db
from app.models.examination import Examination
from app.models.seat_allocation import SeatAllocation
from app.models.hall_ticket import HallTicket
from app.models.invigilator_allocation import InvigilatorAllocation

from app.services.hall_ticket import (
    generate_hall_tickets,
    get_hall_ticket,
    verify_hall_ticket,
)
from app.services.lifecycle import transition_status
from app.services.invigilator_allocation import (
    generate_invigilator_allocation,
)

def _ensure_published(examination_id):
    examination = db.session.get(Examination, examination_id)

    if examination.status == "PUBLISHED":
        return

    lifecycle_order = [
        "DRAFT",
        "GENERATED",
        "VALIDATED",
        "REVIEW",
        "APPROVED",
        "PUBLISHED",
    ]

    current_index = lifecycle_order.index(
        examination.status
    )

    for next_index in range(
        current_index + 1,
        len(lifecycle_order),
    ):
        result = transition_status(
            examination_id,
            lifecycle_order[next_index],
        )

        assert result.get("success") is True, result

    db.session.refresh(examination)
    assert examination.status == "PUBLISHED"


def _ensure_invigilators(examination_id):
    """
    Hall-ticket issuance requires persisted invigilator
    allocation. Earlier force-regeneration tests may have
    removed those rows, so prepare the dependency explicitly.
    """
    existing = InvigilatorAllocation.query.filter_by(
        examination_id=examination_id
    ).count()

    if existing > 0:
        return

    result = generate_invigilator_allocation(
        examination_id,
        force=True
    )

    assert result.get("success") is True, result

# ============================================================
# 8C.1 — Generate hall tickets
# ============================================================

def test_hall_ticket_generation_succeeds(
    app_context, examination_id
):
    _ensure_published(examination_id)
    _ensure_invigilators(examination_id)

    result = generate_hall_tickets(
        examination_id,
        force=True
    )

    assert result.get("success") is True, result

def test_hall_tickets_issued(app_context, examination_id):
    _ensure_published(examination_id)
    _ensure_invigilators(examination_id)

    result = generate_hall_tickets(
        examination_id,
        force=True
    )

    assert result.get("success") is True, result
    assert result.get("issued", 0) > 0

def test_persisted_ticket_count_matches_issued(
    app_context, examination_id
):
    _ensure_published(examination_id)
    _ensure_invigilators(examination_id)

    result = generate_hall_tickets(
        examination_id,
        force=True
    )

    assert result.get("success") is True, result

    count = HallTicket.query.filter_by(
        examination_id=examination_id
    ).count()

    assert count == result.get("issued")

# ============================================================
# 8C.2 — Sample ticket
# ============================================================

def _sample_student(examination_id):
    seat = SeatAllocation.query.filter_by(
        examination_id=examination_id
    ).first()
    return seat.student_id if seat else None


def test_sample_hall_ticket_retrieval(app_context, examination_id):
    student_id = _sample_student(examination_id)
    if student_id is None:
        pytest.skip(
            "No allocated student is available for hall-ticket test"
        )
    result = get_hall_ticket(student_id, examination_id)
    assert result.get("success") is True


def test_ticket_has_verification_token(
    app_context, examination_id
):
    student_id = _sample_student(examination_id)
    result = get_hall_ticket(student_id, examination_id)
    assert result["ticket"].get("verification_token")


def test_ticket_has_qr_image(app_context, examination_id):
    student_id = _sample_student(examination_id)
    result = get_hall_ticket(student_id, examination_id)
    assert result["ticket"].get("qr_base64")


def test_ticket_has_exam_entries(app_context, examination_id):
    student_id = _sample_student(examination_id)
    result = get_hall_ticket(student_id, examination_id)
    assert len(result["payload"].get("entries", [])) > 0


# ============================================================
# 8C.3 — QR payload safety
# ============================================================

def test_qr_output_is_a_valid_png(app_context, examination_id):
    student_id = _sample_student(examination_id)
    result = get_hall_ticket(student_id, examination_id)
    qr_b64 = result["ticket"]["qr_base64"]
    qr_bytes = b64.b64decode(qr_b64)
    assert qr_bytes[:8] == b"\x89PNG\r\n\x1a\n"


def test_verification_token_is_32_char_hex(
    app_context, examination_id
):
    student_id = _sample_student(examination_id)
    result = get_hall_ticket(student_id, examination_id)
    token = result["ticket"]["verification_token"]
    assert len(token) == 32

    try:
        int(token, 16)
    except ValueError:
        pytest.fail(
            "Verification token is not valid hexadecimal"
        )


def test_qr_payload_contains_no_sensitive_fields(
    app_context, examination_id
):
    student_id = _sample_student(examination_id)
    result = get_hall_ticket(student_id, examination_id)
    token = result["ticket"]["verification_token"]
    embedded = jsonlib.dumps({"t": token}, separators=(",", ":"))
    lowered = embedded.lower()
    assert "password" not in lowered
    assert "jwt" not in lowered
    assert "hash" not in lowered


# ============================================================
# 8C.4 — Verify endpoint
# ============================================================

def test_verify_endpoint_returns_valid(app_context, examination_id):
    student_id = _sample_student(examination_id)
    result = get_hall_ticket(student_id, examination_id)
    token = result["ticket"]["verification_token"]
    verification = verify_hall_ticket(token)
    assert verification.get("valid") is True


def test_verify_response_has_no_password_fields(
    app_context, examination_id
):
    student_id = _sample_student(examination_id)
    result = get_hall_ticket(student_id, examination_id)
    token = result["ticket"]["verification_token"]
    verification = verify_hall_ticket(token)
    assert "password" not in verification
    assert "password_hash" not in verification


def test_verify_response_has_safe_identity_fields(
    app_context, examination_id
):
    student_id = _sample_student(examination_id)
    result = get_hall_ticket(student_id, examination_id)
    token = result["ticket"]["verification_token"]
    verification = verify_hall_ticket(token)
    assert "student_code" in verification
    assert "student_name" in verification


# ============================================================
# 8C.5 — Requires PUBLISHED
# ============================================================

def test_hall_ticket_generation_blocked_when_not_published(
    app_context, examination_id
):
    examination = db.session.get(Examination, examination_id)
    original = examination.status

    try:
        examination.status = "REVIEW"
        db.session.commit()

        result = generate_hall_tickets(examination_id, force=True)
        assert result.get("success") is False
    finally:
        examination.status = original
        db.session.commit()


def test_duplicate_ticket_generation_without_force_is_rejected(
    app_context, examination_id
):
    _ensure_published(examination_id)
    generate_hall_tickets(examination_id, force=True)
    result = generate_hall_tickets(examination_id, force=False)
    assert result.get("success") is False


def test_force_reissue_does_not_create_duplicates(
    app_context, examination_id
):
    _ensure_published(examination_id)
    generate_hall_tickets(examination_id, force=True)
    before = HallTicket.query.filter_by(
        examination_id=examination_id
    ).count()

    generate_hall_tickets(examination_id, force=True)
    after = HallTicket.query.filter_by(
        examination_id=examination_id
    ).count()

    assert after == before


# ============================================================
# 9C — Safety after tamper
# ============================================================

def test_hall_ticket_rejected_when_invigilators_missing(
    app_context, examination_id
):
    _ensure_published(examination_id)

    InvigilatorAllocation.query.filter_by(
        examination_id=examination_id
    ).delete(synchronize_session=False)
    db.session.commit()

    try:
        result = generate_hall_tickets(
            examination_id, force=True
        )
        assert result.get("success") is False
    finally:
        generate_invigilator_allocation(
            examination_id, force=True
        )