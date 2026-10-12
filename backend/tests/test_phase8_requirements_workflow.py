"""
Issue 5 — Natural-language requirement → allocation workflow.

Covers:
  - enriched dry-run proposal (non-mutating)
  - lifecycle gate
  - readiness gate
  - unsupported-requirement gate
  - stale-proposal gate
  - successful apply path preserves lifecycle transitions
"""

import pytest

from app import db
from app.models.examination import Examination
from app.models.hall_allocation import HallAllocation
from app.models.seat_allocation import SeatAllocation
from app.models.invigilator_allocation import InvigilatorAllocation


# ---------------------------------------------------------------
# Helpers — mirror test_phase12's reset logic (self-contained)
# ---------------------------------------------------------------

def _reset_examination_state(examination_id):
    from app.models.hall_ticket import HallTicket
    from app.services.allocation import generate_allocation
    from app.services.invigilator_allocation import (
        generate_invigilator_allocation,
    )

    HallTicket.query.filter_by(
        examination_id=examination_id
    ).delete(synchronize_session=False)
    SeatAllocation.query.filter_by(
        examination_id=examination_id
    ).delete(synchronize_session=False)
    InvigilatorAllocation.query.filter_by(
        examination_id=examination_id
    ).delete(synchronize_session=False)
    HallAllocation.query.filter_by(
        examination_id=examination_id
    ).delete(synchronize_session=False)
    db.session.commit()

    exam = Examination.query.get(examination_id)
    if exam is not None and exam.status != "DRAFT":
        exam.status = "DRAFT"
        db.session.commit()

    hall_result = generate_allocation(examination_id, force=True)
    assert hall_result.get("success"), hall_result

    invig_result = generate_invigilator_allocation(
        examination_id, force=True
    )
    assert invig_result.get("success"), invig_result


def _counts(examination_id):
    return {
        "halls": HallAllocation.query.filter_by(
            examination_id=examination_id
        ).count(),
        "seats": SeatAllocation.query.filter_by(
            examination_id=examination_id
        ).count(),
        "invs": InvigilatorAllocation.query.filter_by(
            examination_id=examination_id
        ).count(),
    }


@pytest.fixture
def prepared_examination(examination_id):
    _reset_examination_state(examination_id)
    yield examination_id
    _reset_examination_state(examination_id)


@pytest.fixture(autouse=True)
def _restore_after(examination_id):
    yield
    _reset_examination_state(examination_id)


# ---------------------------------------------------------------
# 1. Enriched dry-run
# ---------------------------------------------------------------

def test_preview_returns_proposal_without_mutating(
    admin_client, prepared_examination
):
    before = _counts(prepared_examination)

    r = admin_client.post(
        f"/api/requirements/apply/{prepared_examination}",
        json={"requirement": "Use minimum halls."},
    )
    assert r.status_code == 200, r.get_json()
    body = r.get_json()

    assert body["mode"] == "preview"
    assert "proposed_allocations" in body
    assert body["proposed_allocations"], "expected at least one hall"
    assert body["proposed_counts"]["halls"] >= 1
    assert body["validation"]["status"] == "VALID"
    assert body["readiness"]["ready_for_allocation"] is True
    assert body["examination"]["updated_at"]

    assert _counts(prepared_examination) == before


# ---------------------------------------------------------------
# 2. Lifecycle gate
# ---------------------------------------------------------------

@pytest.mark.parametrize(
    "status", ["VALIDATED", "REVIEW", "APPROVED"]
)
def test_apply_refused_for_locked_statuses(
    admin_client, prepared_examination, status
):
    exam = Examination.query.get(prepared_examination)
    exam.status = status
    db.session.commit()

    before = _counts(prepared_examination)

    r = admin_client.post(
        f"/api/requirements/apply/{prepared_examination}",
        json={
            "requirement": "Use minimum halls.",
            "confirm": True,
            "expected_updated_at": exam.updated_at.isoformat(),
        },
    )
    assert r.status_code == 409
    assert _counts(prepared_examination) == before


def test_apply_refused_for_published(
    admin_client, prepared_examination
):
    exam = Examination.query.get(prepared_examination)
    exam.status = "PUBLISHED"
    db.session.commit()

    before = _counts(prepared_examination)

    r = admin_client.post(
        f"/api/requirements/apply/{prepared_examination}",
        json={
            "requirement": "Use minimum halls.",
            "confirm": True,
            "expected_updated_at": exam.updated_at.isoformat(),
        },
    )
    assert r.status_code == 409
    body = r.get_json()
    assert "emergency" in body["message"].lower()
    assert _counts(prepared_examination) == before


# ---------------------------------------------------------------
# 3. Unsupported gate
# ---------------------------------------------------------------
def test_apply_refused_without_acknowledgement(
    admin_client, prepared_examination
):
    before = _counts(prepared_examination)

    # NOTE: the parser's UNSUPPORTED_PATTERNS require the word
    # "colored"/"coloured" between the colour and "seats". Use a
    # prompt the parser genuinely rejects so we exercise the
    # unsupported-requirement gate rather than the stale gate.
    r = admin_client.post(
        f"/api/requirements/apply/{prepared_examination}",
        json={
            "requirement": (
                "Use minimum halls and give students "
                "blue-colored seats."
            ),
            "confirm": True,
        },
    )
    assert r.status_code == 400, r.get_json()
    body = r.get_json()
    assert body.get("unsupported_requirements"), body
    assert _counts(prepared_examination) == before

def test_apply_with_acknowledgement_applies_supported_subset(
    admin_client, prepared_examination
):
    # Preview first to get expected_updated_at.
    exam = Examination.query.get(prepared_examination)
    expected = exam.updated_at.isoformat()

    r = admin_client.post(
        f"/api/requirements/apply/{prepared_examination}",
        json={
            "requirement": (
                "Use minimum halls and give students blue seats."
            ),
            "confirm": True,
            "acknowledge_unsupported": True,
            "expected_updated_at": expected,
        },
    )
    assert r.status_code == 200, r.get_json()
    assert r.get_json()["mode"] == "applied"


# ---------------------------------------------------------------
# 4. Stale-proposal gate
# ---------------------------------------------------------------
def test_apply_refused_for_stale_proposal(
    admin_client, prepared_examination
):
    # Capture the value the client would have echoed back.
    exam = Examination.query.get(prepared_examination)
    old = exam.updated_at.isoformat()

    # Genuinely change the examination so onupdate fires.
    # Assigning the same value does not emit an UPDATE and
    # therefore does not refresh updated_at.
    exam.name = f"{exam.name} (edited)"
    db.session.commit()
    db.session.expire_all()

    exam = Examination.query.get(prepared_examination)
    new_updated_at = exam.updated_at.isoformat()
    assert new_updated_at != old, (
        "updated_at did not advance; check Examination.onupdate"
    )

    before = _counts(prepared_examination)

    r = admin_client.post(
        f"/api/requirements/apply/{prepared_examination}",
        json={
            "requirement": "Use minimum halls.",
            "confirm": True,
            "expected_updated_at": old,
        },
    )
    assert r.status_code == 409, r.get_json()
    assert _counts(prepared_examination) == before
def test_apply_without_expected_updated_at_is_backward_compatible(
    admin_client, prepared_examination
):
    """
    Omitting expected_updated_at must not fail the request.

    This preserves the pre-Issue-5 contract for direct API
    callers and for the existing phase-12 integration tests.
    The stricter stale-proposal guard only activates when the
    client opts in by sending the field.
    """
    r = admin_client.post(
        f"/api/requirements/apply/{prepared_examination}",
        json={
            "requirement": "Use minimum halls.",
            "confirm": True,
        },
    )
    assert r.status_code == 200, r.get_json()
    assert r.get_json()["mode"] == "applied"

def test_apply_rejects_malformed_expected_updated_at(
    admin_client, prepared_examination
):
    """
    If the client opts into the stale-proposal guard, the
    value must be a non-empty string.
    """
    r = admin_client.post(
        f"/api/requirements/apply/{prepared_examination}",
        json={
            "requirement": "Use minimum halls.",
            "confirm": True,
            "expected_updated_at": "",
        },
    )
    assert r.status_code == 400, r.get_json()

# ---------------------------------------------------------------
# 5. Happy path preserves lifecycle
# ---------------------------------------------------------------

def test_apply_then_lifecycle_forward_transition(
    admin_client, prepared_examination
):
    exam = Examination.query.get(prepared_examination)
    expected = exam.updated_at.isoformat()

    r = admin_client.post(
        f"/api/requirements/apply/{prepared_examination}",
        json={
            "requirement": (
                "Use the minimum number of halls, keep "
                "accessibility students in accessible halls, "
                "exclude maintenance halls, exclude unavailable "
                "halls, avoid timetable conflicts."
            ),
            "confirm": True,
            "expected_updated_at": expected,
        },
    )
    assert r.status_code == 200, r.get_json()
    assert r.get_json()["validation"]["status"] == "VALID"

    r = admin_client.post(
        f"/api/examinations/{prepared_examination}/generate",
        json={},
    )
    assert r.status_code == 200, r.get_json()
    assert r.get_json()["status"] == "GENERATED"


# ---------------------------------------------------------------
# 6. RBAC
# ---------------------------------------------------------------

def test_apply_requires_admin(client, prepared_examination):
    r = client.post(
        f"/api/requirements/apply/{prepared_examination}",
        json={"requirement": "Use minimum halls."},
    )
    assert r.status_code in (401, 403)