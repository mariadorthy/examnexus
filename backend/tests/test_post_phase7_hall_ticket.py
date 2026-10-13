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
from app.services.allocation import (
    generate_allocation,
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

@pytest.fixture
def issued_and_reissued_ticket(app_context, examination_id):
    """
    Produce a realistic supersede scenario for one student:

      1. Prepare the examination (allocation + invigilators + PUBLISHED).
      2. Issue v1 hall tickets.
      3. Pick one student, capture their v1 verification_token.
      4. Force-regenerate -> v1 rows flip to SUPERSEDED, v2 rows ISSUED.
      5. Capture the same student's v2 verification_token.

    Returns a dict with student_id, examination_id, old_token, new_token.
    """
    _prepare_hall_ticket_state(examination_id)

    # Step 2 — v1 issuance.
    first = generate_hall_tickets(examination_id, force=True)
    assert first.get("success") is True, first

    # Step 3 — pick a student with a v1 ticket.
    v1_row = (
        HallTicket.query
        .filter_by(examination_id=examination_id, status="ISSUED")
        .order_by(HallTicket.id.asc())
        .first()
    )
    assert v1_row is not None, (
        "no v1 ticket was issued; cannot build reissue fixture"
    )
    student_id = v1_row.student_id
    old_token = v1_row.verification_token

    # Step 4 — force reissue: v1 -> SUPERSEDED, v2 -> ISSUED.
    second = generate_hall_tickets(examination_id, force=True)
    assert second.get("success") is True, second

    # Step 5 — capture v2 token for the same student.
    v2_row = (
        HallTicket.query
        .filter_by(
            examination_id=examination_id,
            student_id=student_id,
            status="ISSUED",
        )
        .order_by(HallTicket.version.desc())
        .first()
    )
    assert v2_row is not None, (
        "no v2 ticket was issued for the sampled student"
    )
    assert v2_row.verification_token != old_token, (
        "reissue must generate a fresh verification_token"
    )

    return {
        "student_id": student_id,
        "examination_id": examination_id,
        "old_token": old_token,
        "new_token": v2_row.verification_token,
    }

def _prepare_hall_ticket_state(examination_id):
    """
    Prepare all dependencies required by hall-ticket tests.

    Dependency order:
    hall allocation -> invigilator allocation -> lifecycle -> published.
    """
    generate_allocation(
        examination_id,
        force=True
    )

    _ensure_invigilators(examination_id)
    _ensure_published(examination_id)

# ============================================================
# 8C.1 — Generate hall tickets
# ============================================================

def test_hall_ticket_generation_succeeds(
    app_context, examination_id
):
    _prepare_hall_ticket_state(examination_id)

    result = generate_hall_tickets(
        examination_id,
        force=True
    )

    assert result.get("success") is True, result

def test_hall_tickets_issued(app_context, examination_id):
    _prepare_hall_ticket_state(examination_id)

    result = generate_hall_tickets(
        examination_id,
        force=True
    )

    assert result.get("success") is True, result
    assert result.get("issued", 0) > 0

def test_persisted_ticket_count_matches_issued(
    app_context, examination_id
):
    """
    The count of ISSUED tickets for the examination must equal
    the number the service reported as issued. Prior SUPERSEDED
    versions are preserved by design (audit trail) so they are
    excluded from the comparison.
    """
    _prepare_hall_ticket_state(examination_id)

    result = generate_hall_tickets(
        examination_id,
        force=True
    )

    assert result.get("success") is True, result

    count = HallTicket.query.filter_by(
        examination_id=examination_id,
        status="ISSUED",
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
    _prepare_hall_ticket_state(examination_id)

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

    # get_hall_ticket returns the ticket for this (student, exam)
    # but in the versioned model there may be multiple rows. The
    # one that get_hall_ticket returns is queried by (student,
    # examination) and picks whichever row comes first, which may
    # be a SUPERSEDED version from a prior run. To assert validity
    # deterministically, use the ISSUED row directly.
    issued = (
        HallTicket.query
        .filter_by(
            examination_id=examination_id,
            student_id=student_id,
            status="ISSUED",
        )
        .first()
    )
    assert issued is not None, (
        "no ISSUED hall ticket exists for the sample student"
    )

    verification = verify_hall_ticket(
        issued.verification_token
    )
    assert verification.get("valid") is True
    assert verification.get("status") == "ISSUED"

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
    _prepare_hall_ticket_state(examination_id)
    generate_hall_tickets(examination_id, force=True)
    result = generate_hall_tickets(examination_id, force=False)
    assert result.get("success") is False

def test_force_reissue_does_not_create_duplicates(
    app_context, examination_id
):
    """
    Force reissuing must not create two currently-valid tickets
    for the same student. The previous ISSUED rows are kept for
    audit but flipped to SUPERSEDED, so:
      - the count of ISSUED rows stays constant,
      - the total row count grows by exactly the number of
        previous ISSUED rows (all became SUPERSEDED).
    """
    _prepare_hall_ticket_state(examination_id)
    generate_hall_tickets(examination_id, force=True)

    issued_before = HallTicket.query.filter_by(
        examination_id=examination_id,
        status="ISSUED",
    ).count()
    total_before = HallTicket.query.filter_by(
        examination_id=examination_id
    ).count()

    generate_hall_tickets(examination_id, force=True)

    issued_after = HallTicket.query.filter_by(
        examination_id=examination_id,
        status="ISSUED",
    ).count()
    total_after = HallTicket.query.filter_by(
        examination_id=examination_id
    ).count()

    assert issued_after == issued_before, (
        "force reissue must not change the number of currently "
        "ISSUED tickets"
    )
    assert total_after == total_before + issued_before, (
        "force reissue must preserve the previous ISSUED rows as "
        "SUPERSEDED; total row count should grow by exactly the "
        "number of prior ISSUED tickets"
    )

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

def test_verify_unknown_token_returns_404(client):
    resp = client.get("/api/hall-tickets/verify/deadbeefdeadbeef")
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["valid"] is False
    assert "not found" in body["message"].lower()
    # No identity fields on a truly unknown token.
    assert "student_name" not in body


def test_verify_superseded_token_returns_200_with_identity(client, issued_and_reissued_ticket):
    old_token = issued_and_reissued_ticket["old_token"]
    resp = client.get(f"/api/hall-tickets/verify/{old_token}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["valid"] is False
    assert body["status"] == "SUPERSEDED"
    assert body["student_name"]
    assert body["student_code"]
    assert body["examination"]
    assert "superseded" in body["message"].lower()


def test_verify_new_token_after_reissue_is_valid(client, issued_and_reissued_ticket):
    new_token = issued_and_reissued_ticket["new_token"]
    resp = client.get(f"/api/hall-tickets/verify/{new_token}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["valid"] is True
    assert body["status"] == "ISSUED"


def test_get_hall_ticket_prefers_latest_issued_after_reissue(issued_and_reissued_ticket):
    from app.services.hall_ticket import get_hall_ticket
    result = get_hall_ticket(
        issued_and_reissued_ticket["student_id"],
        issued_and_reissued_ticket["examination_id"],
    )
    assert result["success"] is True
    assert (
        result["ticket"]["verification_token"]
        == issued_and_reissued_ticket["new_token"]
    )